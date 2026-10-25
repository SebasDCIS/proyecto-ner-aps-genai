"""Métricas de NER a nivel de entidad.

Cada entidad se representa como una tupla (doc_id, inicio, fin, tipo), con
posiciones de carácter [inicio, fin) sobre el texto original.

- F1 estricto: coinciden inicio, fin y tipo.
- F1 laxo: se superponen y tienen el mismo tipo (cada entidad gold se empareja
  como máximo una vez).
- Bootstrap por documento para intervalos de confianza, y bootstrap pareado
  para comparar dos sistemas sobre los mismos documentos.
"""
from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from typing import Iterable, Sequence

import numpy as np

Entidad = tuple[str, int, int, str]  # (doc_id, inicio, fin, tipo)


@dataclass
class Conteo:
    vp: int = 0
    fp: int = 0
    fn: int = 0

    def __add__(self, otro: "Conteo") -> "Conteo":
        return Conteo(self.vp + otro.vp, self.fp + otro.fp, self.fn + otro.fn)

    @property
    def precision(self) -> float:
        return self.vp / (self.vp + self.fp) if (self.vp + self.fp) else 0.0

    @property
    def recall(self) -> float:
        return self.vp / (self.vp + self.fn) if (self.vp + self.fn) else 0.0

    @property
    def f1(self) -> float:
        p, r = self.precision, self.recall
        return 2 * p * r / (p + r) if (p + r) else 0.0


def _se_superponen(a: Entidad, b: Entidad) -> bool:
    return a[1] < b[2] and b[1] < a[2]


def contar(gold: Iterable[Entidad], pred: Iterable[Entidad], modo: str = "estricto") -> Conteo:
    """Cuenta VP, FP y FN. modo: 'estricto' o 'laxo'."""
    gold, pred = list(set(gold)), list(set(pred))
    if modo == "estricto":
        g, p = set(gold), set(pred)
        vp = len(g & p)
        return Conteo(vp, len(p) - vp, len(g) - vp)
    if modo != "laxo":
        raise ValueError("modo debe ser 'estricto' o 'laxo'")
    usados: set[int] = set()
    vp = 0
    for pe in sorted(pred, key=lambda e: (e[0], e[1], e[2])):
        for i, ge in enumerate(gold):
            if i in usados:
                continue
            if ge[0] == pe[0] and ge[3] == pe[3] and _se_superponen(ge, pe):
                usados.add(i)
                vp += 1
                break
    return Conteo(vp, len(pred) - vp, len(gold) - vp)


def por_documento(gold: Iterable[Entidad], pred: Iterable[Entidad], modo: str) -> dict[str, Conteo]:
    g, p = defaultdict(list), defaultdict(list)
    for e in gold:
        g[e[0]].append(e)
    for e in pred:
        p[e[0]].append(e)
    docs = set(g) | set(p)
    return {d: contar(g[d], p[d], modo) for d in docs}


def por_tipo(gold: Iterable[Entidad], pred: Iterable[Entidad], modo: str) -> dict[str, Conteo]:
    gold, pred = list(gold), list(pred)
    tipos = {e[3] for e in gold} | {e[3] for e in pred}
    return {
        t: contar([e for e in gold if e[3] == t], [e for e in pred if e[3] == t], modo)
        for t in sorted(tipos)
    }


def macro_f1(gold: Iterable[Entidad], pred: Iterable[Entidad], modo: str) -> float:
    tipos = por_tipo(gold, pred, modo)
    return float(np.mean([c.f1 for c in tipos.values()])) if tipos else 0.0


def bootstrap_f1(
    conteos_doc: dict[str, Conteo],
    n: int = 1000,
    semilla: int = 42,
    alfa: float = 0.05,
) -> tuple[float, float, float]:
    """F1 micro y su IC (percentiles) remuestreando documentos con reposición."""
    docs = sorted(conteos_doc)
    total = sum((conteos_doc[d] for d in docs), Conteo())
    rng = np.random.default_rng(semilla)
    arr = np.array([[conteos_doc[d].vp, conteos_doc[d].fp, conteos_doc[d].fn] for d in docs])
    f1s = []
    for _ in range(n):
        idx = rng.integers(0, len(docs), len(docs))
        vp, fp, fn = arr[idx].sum(axis=0)
        f1s.append(Conteo(int(vp), int(fp), int(fn)).f1)
    lo, hi = np.percentile(f1s, [100 * alfa / 2, 100 * (1 - alfa / 2)])
    return total.f1, float(lo), float(hi)


def bootstrap_pareado(
    conteos_a: dict[str, Conteo],
    conteos_b: dict[str, Conteo],
    n: int = 1000,
    semilla: int = 42,
    alfa: float = 0.05,
) -> tuple[float, float, float]:
    """Diferencia F1(A) - F1(B) con IC, usando los mismos documentos en cada remuestreo."""
    docs = sorted(set(conteos_a) | set(conteos_b))
    vacio = Conteo()
    a = np.array([[conteos_a.get(d, vacio).vp, conteos_a.get(d, vacio).fp, conteos_a.get(d, vacio).fn] for d in docs])
    b = np.array([[conteos_b.get(d, vacio).vp, conteos_b.get(d, vacio).fp, conteos_b.get(d, vacio).fn] for d in docs])
    dif_obs = Conteo(*map(int, a.sum(0))).f1 - Conteo(*map(int, b.sum(0))).f1
    rng = np.random.default_rng(semilla)
    difs = []
    for _ in range(n):
        idx = rng.integers(0, len(docs), len(docs))
        difs.append(Conteo(*map(int, a[idx].sum(0))).f1 - Conteo(*map(int, b[idx].sum(0))).f1)
    lo, hi = np.percentile(difs, [100 * alfa / 2, 100 * (1 - alfa / 2)])
    return dif_obs, float(lo), float(hi)


def alucinaciones(pred_textos: Sequence[tuple[str, str]], textos: dict[str, str]) -> float:
    """Proporción de entidades predichas (doc_id, texto_entidad) que no aparecen en el texto.

    Útil para LLM generativos, que pueden devolver entidades inexistentes.
    """
    if not pred_textos:
        return 0.0
    faltan = sum(1 for d, t in pred_textos if t.strip().lower() not in textos.get(d, "").lower())
    return faltan / len(pred_textos)


def ubicar_en_texto(texto: str, entidades: Sequence[tuple[str, str]], doc_id: str) -> list[Entidad]:
    """Convierte la salida de un LLM [(tipo, texto_entidad), ...] en entidades con posiciones.

    Busca cada mención en el texto (sin distinguir mayúsculas), de izquierda a
    derecha, sin reutilizar una posición ya asignada. Las menciones que no se
    encuentran se descartan (se cuentan aparte como alucinaciones).
    """
    bajo = texto.lower()
    ocupadas: list[tuple[int, int]] = []
    salida: list[Entidad] = []
    for tipo, mencion in entidades:
        m = mencion.strip().lower()
        if not m:
            continue
        inicio = 0
        while True:
            i = bajo.find(m, inicio)
            if i < 0:
                break
            j = i + len(m)
            if all(j <= a or i >= b for a, b in ocupadas):
                ocupadas.append((i, j))
                salida.append((doc_id, i, j, tipo))
                break
            inicio = i + 1
    return salida
