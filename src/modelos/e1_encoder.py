"""E1 — Encoder ajustado (BERT/RoBERTa) para NER, un modelo por tipo de entidad.

Por qué un modelo por tipo: en el CWLC las entidades se anidan (una Abreviatura puede
estar dentro de una Enfermedad). Un solo etiquetador BIO no puede dar dos etiquetas a la
misma palabra, así que, como Báez et al. (2022) y Rojas et al. (2022), entrenamos un
etiquetador independiente por tipo ("Multiple Single-Entity" / MLC).

El ciclo de entrenamiento está escrito a mano con PyTorch (sin `Trainer`) para que se vea
cada paso de la Unidad 2 del curso: lotes, pérdida, retropropagación, optimizador AdamW,
evaluación por época y "early stopping".
"""
from __future__ import annotations

import json
import math
import random
import time
from dataclasses import dataclass, asdict
from pathlib import Path

import numpy as np
import torch
from torch.utils.data import DataLoader
from transformers import AutoModelForTokenClassification, AutoTokenizer, get_linear_schedule_with_warmup

from datos.cwlc import Oracion, bio_a_spans
from evaluacion import metricas
from reproducibilidad import fijar_semilla_total, huella_predicciones


def dispositivo() -> str:
    if torch.backends.mps.is_available():
        return "mps"
    if torch.cuda.is_available():
        return "cuda"
    return "cpu"


def fijar_semilla(semilla: int) -> dict:
    """Compatibilidad: delega en reproducibilidad.fijar_semilla_total."""
    return fijar_semilla_total(semilla)


# ----------------------------------------------------------------------------- etiquetas

def etiquetas_palabra(oracion: Oracion, tipo: str) -> list[str]:
    """Etiquetas BIO por palabra para UN tipo de entidad, a partir de los spans de carácter."""
    off = oracion.offsets()
    tags = ["O"] * len(oracion.tokens)
    for _, a, b, t in oracion.entidades:
        if t != tipo:
            continue
        palabras = [i for i, (x, y) in enumerate(off) if x >= a and y <= b]
        for k, i in enumerate(palabras):
            tags[i] = ("B-" if k == 0 else "I-") + tipo
    return tags


# ----------------------------------------------------------------------------- datos

@dataclass
class Config:
    modelo: str
    tipo: str
    epocas: int = 5
    lr: float = 3e-5
    batch: int = 16
    max_len: int = 512
    paciencia: int = 2
    semilla: int = 42
    max_train: int | None = None  # para pruebas rápidas o curvas de aprendizaje


class Codificador:
    """Tokeniza en subpalabras y alinea las etiquetas: solo la 1.ª subpalabra de cada palabra lleva etiqueta."""

    def __init__(self, nombre_modelo: str, tipo: str, max_len: int):
        try:
            self.tok = AutoTokenizer.from_pretrained(nombre_modelo, add_prefix_space=True)
        except TypeError:
            self.tok = AutoTokenizer.from_pretrained(nombre_modelo)
        self.etiquetas = ["O", f"B-{tipo}", f"I-{tipo}"]
        self.id_de = {e: i for i, e in enumerate(self.etiquetas)}
        self.max_len = max_len

    def codificar(self, tokens: list[str], tags: list[str] | None = None) -> dict:
        enc = self.tok(tokens, is_split_into_words=True, truncation=True, max_length=self.max_len)
        ids_palabra = enc.word_ids()
        etiquetas, previo = [], None
        for w in ids_palabra:
            if w is None or w == previo:
                etiquetas.append(-100)  # -100 = PyTorch ignora esta posición en la pérdida
            else:
                etiquetas.append(self.id_de[tags[w]] if tags else 0)
            previo = w
        enc["labels"] = etiquetas
        enc["word_ids"] = ids_palabra
        return enc

    def collate(self, lote: list[dict]) -> dict:
        n = max(len(x["input_ids"]) for x in lote)
        pad = self.tok.pad_token_id
        salida = {
            "input_ids": torch.tensor([x["input_ids"] + [pad] * (n - len(x["input_ids"])) for x in lote]),
            "attention_mask": torch.tensor([[1] * len(x["input_ids"]) + [0] * (n - len(x["input_ids"])) for x in lote]),
            "labels": torch.tensor([x["labels"] + [-100] * (n - len(x["labels"])) for x in lote]),
        }
        return salida


# ----------------------------------------------------------------------------- predicción

@torch.no_grad()
def predecir(modelo, cod: Codificador, oraciones: list[Oracion], tipo: str, batch: int = 32, disp: str = "cpu"):
    """Devuelve entidades predichas (id, inicio, fin, tipo) con posiciones de carácter."""
    modelo.eval()
    pred: list[tuple[str, int, int, str]] = []
    for i in range(0, len(oraciones), batch):
        bloque = oraciones[i:i + batch]
        encs = [cod.codificar(o.tokens) for o in bloque]
        entrada = cod.collate(encs)
        logits = modelo(input_ids=entrada["input_ids"].to(disp),
                        attention_mask=entrada["attention_mask"].to(disp)).logits.argmax(-1).cpu().tolist()
        for o, enc, fila in zip(bloque, encs, logits):
            tags = ["O"] * len(o.tokens)
            previo = None
            for pos, w in enumerate(enc["word_ids"]):
                if w is not None and w != previo:
                    tags[w] = cod.etiquetas[fila[pos]]
                previo = w
            off = o.offsets()
            for a, b, t in bio_a_spans(tags):
                pred.append((o.id, off[a][0], off[b - 1][1], t))
    return pred


# ----------------------------------------------------------------------------- entrenamiento

def entrenar(cfg: Config, train: list[Oracion], dev: list[Oracion], registro=print):
    """Ajusta un encoder para un tipo de entidad. Devuelve (modelo, codificador, historial)."""
    estado_semilla = fijar_semilla_total(cfg.semilla)
    disp = dispositivo()
    cod = Codificador(cfg.modelo, cfg.tipo, cfg.max_len)
    modelo = AutoModelForTokenClassification.from_pretrained(
        cfg.modelo, num_labels=len(cod.etiquetas),
        id2label=dict(enumerate(cod.etiquetas)), label2id=cod.id_de,
    ).to(disp)

    datos_train = list(train)
    if cfg.max_train:
        random.Random(cfg.semilla).shuffle(datos_train)
        datos_train = datos_train[: cfg.max_train]
    ejemplos = [cod.codificar(o.tokens, etiquetas_palabra(o, cfg.tipo)) for o in datos_train]
    cargador = DataLoader(ejemplos, batch_size=cfg.batch, shuffle=True, collate_fn=cod.collate,
                          generator=torch.Generator().manual_seed(cfg.semilla))

    optim = torch.optim.AdamW(modelo.parameters(), lr=cfg.lr, weight_decay=0.01)
    pasos = cfg.epocas * math.ceil(len(ejemplos) / cfg.batch)
    sched = get_linear_schedule_with_warmup(optim, int(0.1 * pasos), pasos)
    gold_dev = [e for o in dev for e in o.entidades if e[3] == cfg.tipo]

    mejor_f1, mejor_estado, sin_mejora, historial = -1.0, None, 0, []
    for epoca in range(1, cfg.epocas + 1):
        modelo.train()
        t0, perdida_total = time.time(), 0.0
        for lote in cargador:
            lote = {k: v.to(disp) for k, v in lote.items()}
            perdida = modelo(**lote).loss
            perdida.backward()
            torch.nn.utils.clip_grad_norm_(modelo.parameters(), 1.0)
            optim.step(); sched.step(); optim.zero_grad()
            perdida_total += perdida.item()
        pred_dev = predecir(modelo, cod, dev, cfg.tipo, disp=disp)
        f1 = metricas.contar(gold_dev, pred_dev, "estricto").f1
        historial.append({"epoca": epoca, "perdida": perdida_total / len(cargador), "f1_dev": f1,
                          "segundos": round(time.time() - t0, 1)})
        registro(f"  época {epoca}: pérdida={historial[-1]['perdida']:.4f}  F1 dev={f1:.4f}  ({historial[-1]['segundos']} s)")
        if f1 > mejor_f1:
            mejor_f1, sin_mejora = f1, 0
            mejor_estado = {k: v.detach().cpu().clone() for k, v in modelo.state_dict().items()}
        else:
            sin_mejora += 1
            if sin_mejora >= cfg.paciencia:
                registro("  sin mejora en dev: se detiene (early stopping)")
                break
    modelo.load_state_dict(mejor_estado)
    historial.append({"semilla": estado_semilla, "mejor_f1_dev": mejor_f1,
                      "revision_modelo": getattr(modelo.config, "_commit_hash", None)})
    return modelo, cod, historial


def evaluar(gold, pred, oraciones: list[Oracion] | None = None, tipo: str | None = None, n_boot: int = 1000,
            train: list[Oracion] | None = None) -> dict:
    """Métricas estándar del proyecto para un tipo de entidad.

    Si se entrega `train`, agrega dos análisis de sensibilidad por posible fuga:
    - F1 en el test SIN las oraciones repetidas en train (duplicados normalizados).
    - Recall en entidades cuya mención ya se vio en train vs menciones nuevas.
    """
    res = {"huella_predicciones": huella_predicciones(pred)}
    for modo in ["estricto", "laxo"]:
        c = metricas.contar(gold, pred, modo)
        f1, lo, hi = metricas.bootstrap_f1(metricas.por_documento(gold, pred, modo), n=n_boot)
        res[modo] = {"precision": c.precision, "recall": c.recall, "f1": f1, "ic95": [lo, hi],
                     "vp": c.vp, "fp": c.fp, "fn": c.fn}
    if oraciones is not None and tipo is not None:
        from datos.cwlc import es_abreviada
        por_id = {o.id: o for o in oraciones}
        gold_ab = [e for e in gold if es_abreviada(e, por_id[e[0]])]
        gold_no = [e for e in gold if not es_abreviada(e, por_id[e[0]])]
        # una predicción cuenta para el grupo de la entidad gold con la que se superpone
        def subgrupo(g):
            ids = {(e[0]) for e in g}
            return [p for p in pred if p[0] in ids and any(p[0] == e[0] and p[1] < e[2] and e[1] < p[2] for e in g)]
        for nombre, g in [("abreviadas", gold_ab), ("no_abreviadas", gold_no)]:
            c = metricas.contar(g, subgrupo(g), "estricto")
            res[nombre] = {"n_gold": len(g), "recall_estricto": c.recall}
        if train is not None:
            from datos.auditoria import normalizar
            textos_train = {normalizar(o.texto) for o in train}
            ids_dup = {o.id for o in oraciones if normalizar(o.texto) in textos_train}
            g2 = [e for e in gold if e[0] not in ids_dup]
            p2 = [e for e in pred if e[0] not in ids_dup]
            c2 = metricas.contar(g2, p2, "estricto")
            res["test_sin_duplicados"] = {"oraciones_excluidas": len(ids_dup), "f1_estricto": c2.f1,
                                          "precision": c2.precision, "recall": c2.recall}
            vistas = {normalizar(o.mencion(e)) for o in train for e in o.entidades if e[3] == tipo}
            g_v = [e for e in gold if normalizar(por_id[e[0]].mencion(e)) in vistas]
            g_n = [e for e in gold if normalizar(por_id[e[0]].mencion(e)) not in vistas]
            for nombre, g in [("menciones_vistas", g_v), ("menciones_nuevas", g_n)]:
                c = metricas.contar(g, subgrupo(g), "estricto")
                res[nombre] = {"n_gold": len(g), "recall_estricto": c.recall}
    return res


def guardar_resultados(ruta: Path, cfg: Config, historial: list, resultados: dict, huella: dict | None = None) -> None:
    ruta.parent.mkdir(parents=True, exist_ok=True)
    ruta.write_text(json.dumps({"config": asdict(cfg), "historial": historial, "resultados": resultados,
                                "huella": huella}, indent=2, ensure_ascii=False, default=str), encoding="utf-8")
