"""E4 — El LLM como anotador ("destilación"): etiquetas silver + pocas etiquetas gold.

Simulamos un escenario con texto sin anotar y un esfuerzo humano pequeño:

1. Gold simulado: de train se toman al azar N = 0, 10, 50 o 100 oraciones CON su anotación real
   (hecha por médicos). Los conjuntos están anidados: las 10 están dentro de las 50, y estas en las 100.
2. Silver: otro grupo fijo de oraciones de train, a las que se les "borra" la anotación, es anotado por
   el LLM (qwen2.5:7b). Si N = 0, el LLM trabaja sin ejemplos (zero-shot); si N > 0, recibe los 5 ejemplos
   más parecidos, buscados SOLO entre las N oraciones gold (nunca en el resto de train: sería fuga).
3. Se entrena un encoder (como E1) con silver + gold. Para no suponer etiquetas que en la práctica no
   existirían, no se usa dev para elegir la época: se usa la última (`seleccion="ultima"`).
4. Se evalúa en el mismo test que E1 y E2.

Además se entrena un encoder SOLO con las N oraciones gold, para ver cuánto aporta el silver.
"""
from __future__ import annotations

import random
from dataclasses import replace

from datos.cwlc import Oracion
from modelos import e2_llm as E2


def seleccionar_gold(train: list[Oracion], n: int, semilla: int = 42) -> list[Oracion]:
    """N oraciones gold al azar (con al menos 3 palabras). Anidadas: el orden aleatorio es siempre el mismo."""
    cands = [o for o in train if len(o.tokens) >= 3]
    random.Random(semilla).shuffle(cands)
    return cands[:n]


def pool_silver(train: list[Oracion], n: int, max_gold: int = 100, semilla: int = 42) -> list[Oracion]:
    """Oraciones que anotará el LLM: disjuntas de cualquier conjunto gold posible (las primeras max_gold)."""
    excluir = {o.id for o in seleccionar_gold(train, max_gold, semilla)}
    resto = [o for o in train if o.id not in excluir and len(o.tokens) >= 3]
    random.Random(semilla + 1).shuffle(resto)
    return resto[:n]


def selector_para(gold: list[Oracion], k: int = 5):
    """Sin gold: zero-shot. Con gold: los k ejemplos más parecidos, buscados solo entre el gold."""
    if not gold:
        return None
    return E2.SelectorDinamico(gold, k=min(k, len(gold)))


def oraciones_silver(pool: list[Oracion], respuestas: dict) -> tuple[list[Oracion], dict]:
    """Reemplaza las entidades de cada oración por las que marcó el LLM (solo los 3 tipos de E2)."""
    ev = E2.evaluar_respuestas(respuestas, pool)
    por_id = {o.id: [] for o in pool}
    for tipo in E2.TIPOS_E2:
        for e in ev["pred"][tipo]:
            por_id[e[0]].append(e)
    silver = [replace(o, entidades=sorted(por_id[o.id], key=lambda e: (e[1], e[3]))) for o in pool]
    return silver, ev


def calidad_silver(pool: list[Oracion], silver: list[Oracion]) -> dict:
    """F1 de las etiquetas del LLM contra la anotación real de esas mismas oraciones (el 'maestro')."""
    from evaluacion import metricas

    res = {}
    for tipo in E2.TIPOS_E2:
        g = [e for o in pool for e in o.entidades if e[3] == tipo]
        p = [e for o in silver for e in o.entidades if e[3] == tipo]
        c = metricas.contar(g, p, "estricto")
        res[tipo] = {"precision": c.precision, "recall": c.recall, "f1": c.f1}
    return res
