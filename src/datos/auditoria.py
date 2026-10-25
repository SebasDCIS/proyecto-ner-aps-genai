"""Auditoría de fuga de datos y calidad del corpus.

Cada función devuelve un diccionario o DataFrame pequeño, para mostrarlo en el
notebook 01b y guardarlo en results/auditoria_datos.json.

Fugas que se revisan:
1. Oraciones idénticas (o casi) repetidas entre train y test/dev.
2. Mismas oraciones con etiquetas distintas (ruido de anotación).
3. Menciones del test ya vistas como entidad en train (memorización; no es fuga, pero
   explica parte del rendimiento y conviene reportarla).

Errores de datos que se revisan: etiquetas BIO inválidas, caracteres extraños o
Unicode no normalizado, oraciones vacías o muy largas, oraciones truncadas por el
límite de subpalabras del modelo.
"""
from __future__ import annotations

import re
import unicodedata
from collections import Counter, defaultdict
from pathlib import Path

from datos.cwlc import TIPOS, Oracion, leer_conll


def normalizar(texto: str) -> str:
    """Minúsculas, sin tildes, espacios simples. Sirve para detectar duplicados 'disfrazados'."""
    t = unicodedata.normalize("NFKD", texto.lower())
    t = "".join(c for c in t if not unicodedata.combining(c))
    return re.sub(r"\s+", " ", t).strip()


def firma_etiquetas(o: Oracion) -> tuple:
    return tuple(sorted((a, b, t) for _, a, b, t in o.entidades))


# --------------------------------------------------------------------------- duplicados

def duplicados_entre_splits(splits: dict[str, list[Oracion]], min_tokens: int = 1) -> dict:
    """Oraciones del split B cuyo texto normalizado aparece también en el split A."""
    indice = {s: defaultdict(list) for s in splits}
    for s, ors in splits.items():
        for o in ors:
            if len(o.tokens) >= min_tokens:
                indice[s][normalizar(o.texto)].append(o)
    res = {}
    for a, b in [("train", "dev"), ("train", "test"), ("dev", "test")]:
        comunes = set(indice[a]) & set(indice[b])
        ors_b = [o for k in comunes for o in indice[b][k]]
        ent_b = sum(len(o.entidades) for o in ors_b)
        total_ent_b = sum(len(o.entidades) for o in splits[b])
        res[f"{a}∩{b}"] = {
            "oraciones_repetidas_en_" + b: len(ors_b),
            "%_de_" + b: round(100 * len(ors_b) / len(splits[b]), 2),
            "entidades_afectadas": ent_b,
            "%_entidades_de_" + b: round(100 * ent_b / max(total_ent_b, 1), 2),
            "ejemplos": sorted(comunes, key=len, reverse=True)[:8],
        }
    return res


def casi_duplicados(train: list[Oracion], otro: list[Oracion], umbral: float = 0.8, min_tokens: int = 6) -> dict:
    """Oraciones de `otro` con similitud de Jaccard (trigramas de palabras) >= umbral con alguna de train.

    Usa un índice invertido de trigramas para no comparar todo contra todo.
    """
    def trigramas(o):
        w = normalizar(o.texto).split()
        return {" ".join(w[i:i + 3]) for i in range(len(w) - 2)}

    tri_train = [trigramas(o) for o in train]
    indice = defaultdict(set)
    for i, tg in enumerate(tri_train):
        for g in tg:
            indice[g].add(i)
    hallados = []
    for o in otro:
        if len(o.tokens) < min_tokens:
            continue
        tg = trigramas(o)
        if not tg:
            continue
        candidatos = Counter(i for g in tg for i in indice.get(g, ()))
        mejor = 0.0
        for i, comun in candidatos.most_common(20):
            j = comun / len(tg | tri_train[i])
            mejor = max(mejor, j)
        if mejor >= umbral:
            hallados.append((round(mejor, 3), o.texto[:120]))
    hallados.sort(reverse=True)
    elegibles = sum(1 for o in otro if len(o.tokens) >= min_tokens)
    return {"umbral_jaccard": umbral, "oraciones_elegibles": elegibles, "casi_duplicadas": len(hallados),
            "%": round(100 * len(hallados) / max(elegibles, 1), 2), "ejemplos": hallados[:8]}


def conflictos_de_etiqueta(splits: dict[str, list[Oracion]]) -> dict:
    """Mismo texto exacto anotado de formas distintas (en todo el corpus)."""
    por_texto = defaultdict(set)
    ubic = defaultdict(set)
    for s, ors in splits.items():
        for o in ors:
            por_texto[o.texto].add(firma_etiquetas(o))
            ubic[o.texto].add(s)
    conflictos = [t for t, f in por_texto.items() if len(f) > 1]
    return {"textos_con_anotacion_inconsistente": len(conflictos),
            "que_cruzan_splits": sum(1 for t in conflictos if len(ubic[t]) > 1),
            "ejemplos": sorted(conflictos, key=len, reverse=True)[:6]}


def menciones_vistas(train: list[Oracion], test: list[Oracion], tipo: str) -> dict:
    """Proporción de entidades del test cuya mención (normalizada) ya aparece como entidad en train."""
    vistas = {normalizar(o.mencion(e)) for o in train for e in o.entidades if e[3] == tipo}
    ents = [(o, e) for o in test for e in o.entidades if e[3] == tipo]
    n_vistas = sum(normalizar(o.mencion(e)) in vistas for o, e in ents)
    return {"tipo": tipo, "entidades_test": len(ents), "ya_vistas_en_train": n_vistas,
            "%_vistas": round(100 * n_vistas / max(len(ents), 1), 1)}


# --------------------------------------------------------------------------- calidad

def bio_invalidas(carpeta: Path, tipos: list[str] | None = None) -> dict:
    """Cuenta etiquetas I- 'huérfanas' (sin B- o I- del mismo tipo antes) por archivo."""
    res = {}
    for tipo in tipos or TIPOS:
        for split in ["train", "dev", "test"]:
            n = 0
            for _, tags in leer_conll(carpeta / tipo / f"{tipo}_{split}.conll"):
                previo = "O"
                for t in tags:
                    if t.startswith("I-") and previo[2:] != t[2:]:
                        n += 1
                    previo = t
            res[f"{tipo}/{split}"] = n
    return res


def caracteres_raros(splits: dict[str, list[Oracion]]) -> dict:
    """Caracteres de control, de reemplazo (�) y texto no normalizado NFC."""
    control = reemplazo = no_nfc = 0
    ejemplos = Counter()
    for ors in splits.values():
        for o in ors:
            for tok in o.tokens:
                if "�" in tok:
                    reemplazo += 1
                if any(unicodedata.category(c) in ("Cc", "Cf") for c in tok):
                    control += 1
                    ejemplos[repr(tok)] += 1
                if unicodedata.normalize("NFC", tok) != tok:
                    no_nfc += 1
    return {"tokens_con_caracteres_de_control": control, "tokens_con_caracter_reemplazo": reemplazo,
            "tokens_no_NFC": no_nfc, "ejemplos_control": ejemplos.most_common(5)}


def largos(splits: dict[str, list[Oracion]], tokenizer=None, max_len: int = 512) -> dict:
    """Oraciones vacías/de 1 token y oraciones que superan el límite de subpalabras del modelo."""
    res = {}
    for s, ors in splits.items():
        d = {"oraciones": len(ors), "de_1_token": sum(len(o.tokens) == 1 for o in ors),
             "max_palabras": max(len(o.tokens) for o in ors)}
        if tokenizer is not None:
            n_sub = [len(tokenizer(o.tokens, is_split_into_words=True)["input_ids"]) for o in ors]
            d["max_subpalabras"] = max(n_sub)
            d[f"truncadas_a_{max_len}"] = sum(n > max_len for n in n_sub)
            d["truncadas_a_256"] = sum(n > 256 for n in n_sub)
        res[s] = d
    return res
