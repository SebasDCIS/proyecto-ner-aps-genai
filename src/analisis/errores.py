"""Análisis de errores (notebook 05): en qué se equivoca cada sistema y por qué.

No entrena ni llama a ningún modelo: reutiliza las predicciones ya guardadas en results/cache
(E1: un .pkl por encoder, tipo y semilla; E2 y nube: un .jsonl de respuestas por corrida).

Contiene cuatro análisis:
1. Tipología de errores: correcta, error de límite (más larga, más corta, desplazada), espuria, omitida.
2. Palabras mal escritas en las derivaciones reales ("FUSROSEMIDA", "ISUFICIENCIA"): recall en
   menciones con y sin error ortográfico. No se simula ruido: se mide el que ya trae el corpus.
3. Lenguaje local: abreviaturas según cuántas veces aparecen en train (frecuentes, raras, nunca vistas).
4. Cruce encoder × LLM: qué menciones encuentra solo uno, y cuánto ganaría un sistema híbrido simple.
"""
from __future__ import annotations

import json
import pickle
import unicodedata
from collections import Counter, defaultdict
from functools import lru_cache
from pathlib import Path

import numpy as np

from datos.cwlc import Oracion, es_abreviada
from evaluacion import metricas

TIPOS = ["Disease", "Medication", "Abbreviation"]
NOMBRE_TIPO = {"Disease": "Enfermedad", "Medication": "Medicamento", "Abbreviation": "Abreviatura"}


# --------------------------------------------------------------------------- carga de predicciones

def cargar_e1(cache: Path, clave: str, semilla: int) -> dict[str, list] | None:
    """Predicciones de un encoder de E1 (las guardó el notebook 02)."""
    pred = {}
    for t in TIPOS:
        ruta = cache / f"{clave}_{t}_s{semilla}.pkl"
        if not ruta.exists():
            return None
        pred[t] = list(pickle.loads(ruta.read_bytes()))
    return pred


def cargar_llm(ruta: Path, test: list[Oracion]) -> tuple[dict[str, list], dict] | None:
    """Predicciones de una corrida de LLM a partir de su caché de respuestas.

    Devuelve None si la corrida no cubre todo el test (por ejemplo, Gemini mientras avanza por cuota).
    """
    from modelos import e2_llm as E2

    if not ruta.exists():
        return None
    resp = E2.Cache(ruta).datos
    ids = {o.id for o in test}
    if not ids <= set(resp):
        return None
    ev = E2.evaluar_respuestas({i: resp[i] for i in ids}, test)
    return ev["pred"], {"tasa_alucinacion": ev["tasa_alucinacion"], "json_invalidos": ev["json_invalidos"]}


def cobertura(ruta: Path, test: list[Oracion]) -> int:
    """Cuántas oraciones del test tiene ya respondidas una corrida."""
    from modelos import e2_llm as E2

    if not ruta.exists():
        return 0
    ids = {o.id for o in test}
    return len(ids & set(E2.Cache(ruta).datos))


def gold_por_tipo(test: list[Oracion]) -> dict[str, list]:
    return {t: [e for o in test for e in o.entidades if e[3] == t] for t in TIPOS}


# --------------------------------------------------------------------------- 1. tipología de errores

CATEGORIAS = ["correcta", "más larga", "más corta", "desplazada", "espuria", "omitida"]


def _contiene(a, b) -> bool:
    return a[1] <= b[1] and b[2] <= a[2]


def tipologia(gold: list, pred: list) -> Counter:
    """Clasifica cada predicción y cada entidad gold no encontrada (mismo tipo).

    - correcta: coincide exacto (VP estricto).
    - más larga / más corta / desplazada: se superpone con una entidad gold pero con otros límites
      (FP estricto que sería VP en F1 laxo). "Más larga" = la predicción contiene a la gold.
    - espuria: predicción que no toca ninguna entidad gold (FP puro).
    - omitida: entidad gold que ninguna predicción toca (FN puro).
    """
    g_doc, p_doc = defaultdict(list), defaultdict(list)
    for e in set(gold):
        g_doc[e[0]].append(e)
    for e in set(pred):
        p_doc[e[0]].append(e)
    c = Counter()
    gset = set(gold)
    for d, ps in p_doc.items():
        for p in ps:
            if p in gset:
                c["correcta"] += 1
                continue
            sup = [g for g in g_doc[d] if p[1] < g[2] and g[1] < p[2]]
            if not sup:
                c["espuria"] += 1
            elif any(_contiene(p, g) for g in sup):
                c["más larga"] += 1
            elif any(_contiene(g, p) for g in sup):
                c["más corta"] += 1
            else:
                c["desplazada"] += 1
    for d, gs in g_doc.items():
        for g in gs:
            if g not in set(p_doc[d]) and not any(p[1] < g[2] and g[1] < p[2] for p in p_doc[d]):
                c["omitida"] += 1
    return c


# --------------------------------------------------------------------------- 2. palabras mal escritas

def normalizar(s: str) -> str:
    """Minúsculas y sin tildes (el corpus mezcla 'CRÓNICA' y 'CRONICA'; eso no es un error)."""
    return "".join(ch for ch in unicodedata.normalize("NFD", s.lower()) if unicodedata.category(ch) != "Mn")


def distancia(a: str, b: str, maximo: int = 2) -> int:
    """Distancia de edición con trasposiciones (Damerau-Levenshtein restringida), con corte temprano."""
    if abs(len(a) - len(b)) > maximo:
        return maximo + 1
    prev2, prev = None, list(range(len(b) + 1))
    for i, ca in enumerate(a, 1):
        cur = [i] + [0] * len(b)
        for j, cb in enumerate(b, 1):
            cur[j] = min(prev[j] + 1, cur[j - 1] + 1, prev[j - 1] + (ca != cb))
            if prev2 is not None and j > 1 and ca == b[j - 2] and a[i - 2] == cb:
                cur[j] = min(cur[j], prev2[j - 2] + 1)
        if min(cur) > maximo:
            return maximo + 1
        prev2, prev = prev, cur
    return prev[-1]


# Palabras correctas que la heurística marcaba por no estar en el diccionario general
# (revisión manual de la lista que entrega `palabras_mal_escritas` sobre el test).
CORRECTAS_REVISADAS = {"perimenopausico", "endotropia", "onicofagia", "esperado", "ascendido", "miocardica"}


@lru_cache(maxsize=1)
def _diccionario_es() -> frozenset:
    """Diccionario general de español (pyspellchecker), normalizado sin tildes. Vacío si no está instalado."""
    try:
        from spellchecker import SpellChecker
    except ImportError:
        return frozenset()
    return frozenset(normalizar(w) for w in SpellChecker(language="es").word_frequency.dictionary)


def _variantes(w: str) -> set[str]:
    """Formas cercanas por plural y género (CAMARAS → camara), para no confundirlas con errores."""
    v = {w}
    for suf in ("es", "s"):
        if w.endswith(suf):
            v.add(w[: -len(suf)])
    for x in list(v):
        if x and x[-1] in "aoe":
            v |= {x[:-1] + "o", x[:-1] + "a", x[:-1]}
        v |= {x + "o", x + "a"}
    return v


class DetectorOrtografia:
    """Marca palabras probablemente mal escritas, comparando contra el vocabulario de train.

    Una palabra (≥5 letras, solo letras) se considera mal escrita si:
    1. no está en el diccionario general de español ni en train (≥2 veces), ni siquiera en plural o
       con otro género, y
    2. está a distancia de edición 1 (palabras de <8 letras) o 2 (≥8 letras) de una palabra
       frecuente de train (≥3 veces) que empieza o termina igual.

    Es una heurística: se revisó a mano su lista sobre el test (ver CORRECTAS_REVISADAS).
    """

    def __init__(self, train: list[Oracion], diccionario: frozenset | None = None):
        self.voc = Counter(normalizar(t) for o in train for t in o.tokens if t.isalpha())
        self.dic = _diccionario_es() if diccionario is None else diccionario
        self.por_largo = defaultdict(list)
        for w, n in self.voc.items():
            if n >= 3 and len(w) >= 4:
                self.por_largo[len(w)].append(w)
        self._memo = {}

    def conocida(self, w: str) -> bool:
        return w in CORRECTAS_REVISADAS or any(x in self.dic or self.voc[x] >= 2 for x in _variantes(w))

    def correccion(self, token: str) -> str | None:
        """La palabra de train más probable si `token` parece mal escrito; si no, None."""
        w = normalizar(token)
        if not token.isalpha() or len(w) < 5 or self.conocida(w):
            return None
        if w in self._memo:
            return self._memo[w]
        d = 1 if len(w) < 8 else 2
        mejor = None
        for largo in range(len(w) - d, len(w) + d + 1):
            for r in self.por_largo.get(largo, []):
                if r[0] != w[0] and r[-1] != w[-1]:
                    continue
                if distancia(w, r, d) <= d and (mejor is None or self.voc[r] > self.voc[mejor]):
                    mejor = r
        self._memo[w] = mejor
        return mejor


def menciones_mal_escritas(test: list[Oracion], detector: DetectorOrtografia, tipos=("Disease", "Medication")):
    """Entidades gold con al menos una palabra mal escrita → {entidad: [(palabra, corrección), ...]}."""
    salida = {}
    for o in test:
        for e in o.entidades:
            if e[3] not in tipos:
                continue
            errores = [(t, detector.correccion(t)) for t in o.mencion(e).split()]
            errores = [(t, c) for t, c in errores if c]
            if errores:
                salida[e] = errores
    return salida


# --------------------------------------------------------------------------- 3. lenguaje local

def frecuencia_en_train(train: list[Oracion], tipo: str) -> Counter:
    return Counter(normalizar(o.mencion(e)) for o in train for e in o.entidades if e[3] == tipo)


def grupo_frecuencia(n: int) -> str:
    return "frecuente (≥10 en train)" if n >= 10 else ("rara (1–9 en train)" if n >= 1 else "nunca vista en train")


# --------------------------------------------------------------------------- recall por grupo

def recall_grupo(gold_grupo: list, pred: list) -> tuple[int, float]:
    """(n, recall estricto) de un subconjunto de entidades gold."""
    p = set(pred)
    n = len(gold_grupo)
    return n, (sum(g in p for g in gold_grupo) / n if n else float("nan"))


def ic_recall(gold_grupo: list, pred: list, n_boot: int = 1000, semilla: int = 42) -> tuple[float, float]:
    """IC 95% del recall remuestreando oraciones (las menciones de una oración van juntas)."""
    p = set(pred)
    por_doc = defaultdict(lambda: [0, 0])
    for g in gold_grupo:
        por_doc[g[0]][0] += g in p
        por_doc[g[0]][1] += 1
    if not por_doc:
        return float("nan"), float("nan")
    arr = np.array(list(por_doc.values()))
    rng = np.random.default_rng(semilla)
    rs = []
    for _ in range(n_boot):
        s = arr[rng.integers(0, len(arr), len(arr))].sum(0)
        rs.append(s[0] / s[1])
    lo, hi = np.percentile(rs, [2.5, 97.5])
    return float(lo), float(hi)


# --------------------------------------------------------------------------- 4. cruce encoder × LLM

def cruce(gold: list, pred_a: list, pred_b: list) -> dict:
    """Para cada entidad gold: la encuentran ambos, solo A, solo B o ninguno (coincidencia exacta)."""
    a, b = set(pred_a), set(pred_b)
    c = Counter()
    for g in set(gold):
        c[("ambos" if g in b else "solo A") if g in a else ("solo B" if g in b else "ninguno")] += 1
    n = sum(c.values())
    return {"n": n, **c, "recall_A": (c["ambos"] + c["solo A"]) / n, "recall_B": (c["ambos"] + c["solo B"]) / n,
            "recall_oraculo": (n - c["ninguno"]) / n}


def union(pred_a: list, pred_b: list) -> list:
    """Híbrido simple: todo lo que marque cualquiera de los dos (sube recall, puede bajar precisión)."""
    return sorted(set(pred_a) | set(pred_b))


def interseccion(pred_a: list, pred_b: list) -> list:
    """Híbrido conservador: solo lo que marcan ambos (sube precisión, baja recall)."""
    return sorted(set(pred_a) & set(pred_b))


def rescate_sin_choque(pred_a: list, pred_b: list) -> list:
    """Híbrido 'el encoder manda': se agregan las predicciones de B que no tocan ninguna de A.

    Así el LLM solo aporta donde el encoder no marcó nada, sin cambiarle los límites a lo que
    el encoder ya encontró.
    """
    por_doc = defaultdict(list)
    for p in pred_a:
        por_doc[p[0]].append(p)
    extra = [q for q in set(pred_b) if not any(q[1] < p[2] and p[1] < q[2] for p in por_doc[q[0]])]
    return sorted(set(pred_a) | set(extra))


def rescate_dirigido(pred_a: list, pred_b: list, test: list[Oracion], vocabulario: Counter) -> list:
    """Como `rescate_sin_choque`, pero el LLM solo aporta menciones con alguna palabra nunca vista en train
    (posible error de tipeo o sigla nueva), que es donde el encoder falla más."""
    por_id = {o.id: o for o in test}

    def desconocida(e):
        return any(t.isalpha() and len(t) >= 3 and vocabulario[normalizar(t)] == 0
                   for t in por_id[e[0]].mencion(e).split())

    por_doc = defaultdict(list)
    for p in pred_a:
        por_doc[p[0]].append(p)
    extra = [q for q in set(pred_b)
             if desconocida(q) and not any(q[1] < p[2] and p[1] < q[2] for p in por_doc[q[0]])]
    return sorted(set(pred_a) | set(extra))


def espurias_sobre_otros_tipos(test: list[Oracion], tipo: str, pred: list) -> Counter:
    """Predicciones espurias de `tipo` (no tocan ninguna entidad gold de ese tipo), según con qué
    otra entidad gold se superponen. Ej.: 'Finding' = el sistema marcó como enfermedad un hallazgo."""
    por_id = {o.id: o for o in test}
    c = Counter()
    for p in set(pred):
        ents = por_id[p[0]].entidades
        if any(g[3] == tipo and p[1] < g[2] and g[1] < p[2] for g in ents):
            continue
        otros = sorted({g[3] for g in ents if g[3] != tipo and p[1] < g[2] and g[1] < p[2]})
        c[" + ".join(otros) if otros else "ninguna entidad"] += 1
    return c


def dif_recall_pareada(gold_grupo: list, pred_a: list, pred_b: list, n_boot: int = 1000,
                       semilla: int = 42) -> tuple[float, float, float]:
    """Recall(A) − Recall(B) en un grupo de entidades gold, con IC 95% remuestreando oraciones."""
    a, b = set(pred_a), set(pred_b)
    por_doc = defaultdict(lambda: [0, 0, 0])
    for g in gold_grupo:
        por_doc[g[0]][0] += g in a
        por_doc[g[0]][1] += g in b
        por_doc[g[0]][2] += 1
    if not por_doc:
        return float("nan"), float("nan"), float("nan")
    arr = np.array(list(por_doc.values()))
    tot = arr.sum(0)
    obs = (tot[0] - tot[1]) / tot[2]
    rng = np.random.default_rng(semilla)
    ds = []
    for _ in range(n_boot):
        s = arr[rng.integers(0, len(arr), len(arr))].sum(0)
        ds.append((s[0] - s[1]) / s[2])
    lo, hi = np.percentile(ds, [2.5, 97.5])
    return float(obs), float(lo), float(hi)


def f1_con_ic(gold: list, pred: list, n_boot: int = 1000) -> dict:
    c = metricas.contar(gold, pred, "estricto")
    f1, lo, hi = metricas.bootstrap_f1(metricas.por_documento(gold, pred, "estricto"), n=n_boot)
    return {"precision": c.precision, "recall": c.recall, "f1": f1, "ic95": [lo, hi]}


def diferencia_pareada(gold: list, pred_a: list, pred_b: list, n_boot: int = 1000) -> tuple[float, float, float]:
    """F1(A) − F1(B) con IC 95% (bootstrap pareado por oración)."""
    return metricas.bootstrap_pareado(metricas.por_documento(gold, pred_a, "estricto"),
                                      metricas.por_documento(gold, pred_b, "estricto"), n=n_boot)


def perfil(entidades: list, test: list[Oracion], mal_escritas: dict, vistas: set) -> dict:
    """Qué tienen de especial un grupo de entidades: % mal escritas, % abreviadas, % nunca vistas en train."""
    por_id = {o.id: o for o in test}
    n = len(entidades)
    if not n:
        return {"n": 0}
    return {"n": n,
            "mal_escritas": sum(e in mal_escritas for e in entidades) / n,
            "abreviadas": sum(es_abreviada(e, por_id[e[0]]) for e in entidades) / n,
            "nunca_vistas": sum(normalizar(por_id[e[0]].mencion(e)) not in vistas for e in entidades) / n}


def guardar(ruta: Path, datos: dict) -> None:
    ruta.parent.mkdir(parents=True, exist_ok=True)
    ruta.write_text(json.dumps(datos, indent=2, ensure_ascii=False, default=float))
