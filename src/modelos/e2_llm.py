"""E2 — LLM local (Ollama) con prompt estructurado: zero-shot, few-shot fijo y few-shot dinámico.

Aquí el modelo NO se entrena: se le dan instrucciones (una guía de anotación) y, según la
estrategia, algunos ejemplos resueltos sacados SOLO de train:

- zero_shot:          solo la guía.
- few_shot_fijo:      la guía + los mismos k ejemplos para todas las oraciones (elegidos al azar
                      con una semilla; se repite con 3 semillas = 3 sets de ejemplos distintos).
- few_shot_dinamico:  la guía + los k ejemplos de train más parecidos a cada oración (BM25),
                      es decir, recuperación de ejemplos (RAG aplicado a few-shot).

El LLM responde un JSON con las menciones copiadas del texto; luego se ubican en la oración
para obtener posiciones de carácter y evaluarlas con las mismas métricas que E1.
Las menciones que no aparecen en la oración se cuentan como alucinaciones.
"""
from __future__ import annotations

import json
import random
import re
import time
from pathlib import Path

from datos.auditoria import normalizar
from datos.cwlc import Oracion
from reproducibilidad import sha256_bytes

TIPOS_E2 = ["Disease", "Medication", "Abbreviation"]

# Tope de tokens que el LLM puede generar por oración. La respuesta correcta más larga de train+test
# tiene ~1.600 caracteres (~700 tokens); 2.048 deja margen aun si el modelo indenta el JSON.
# Sin tope, un modelo que entra en bucle ("X", "X", "X"...) puede generar hasta llenar su memoria:
# en la primera corrida rápida, 3 oraciones tardaron 35–70 minutos cada una por esto.
NUM_PREDICT = 2048

# Guía de anotación resumida. Se redactó mirando SOLO ejemplos de train (nunca dev ni test).
GUIA = """Eres un anotador clínico experto. Recibirás una oración de una derivación escrita por un médico o dentista de Atención Primaria de Salud en Chile. Marca todas las menciones de estos tres tipos:

- Disease: enfermedades, diagnósticos y síndromes, incluidas sus abreviaturas (HTA, DM2, DLP, ERC) y los diagnósticos CIE-10 completos tal como aparecen (por ejemplo "ANOMALÍAS DENTOFACIALES ( INCLUSO LA MALOCLUSIÓN )"). Incluye los calificadores que forman parte del diagnóstico ("DM NIR", "ERC etapa III", "Periodontitis cronica").
- Medication: fármacos, familias de fármacos y materiales de uso terapéutico, por nombre genérico, comercial o abreviado (LOSARTAN, aas, atv, enl, AINES, TACO, insulina cristalina, eugenato, hidróxido de calcio). Solo el nombre: sin dosis, unidades ni frecuencia.
- Abbreviation: toda abreviatura, sigla o acrónimo (APS, pcte, tto, obs, pza, rx, HTA, DM2, mg, cm, UI), incluido el signo "+" cuando reemplaza a "y" o "más".

Reglas:
1. Copia cada mención EXACTAMENTE como aparece en la oración (mismas mayúsculas, tildes, espacios y errores de ortografía). No corrijas ni expandas nada.
2. Una misma mención puede tener más de un tipo: "HTA" es Disease y también Abbreviation. Inclúyela una vez por cada tipo.
3. Si una mención se repite en la oración, inclúyela cada vez que aparece, en orden.
4. Si no hay menciones, devuelve una lista vacía.
5. Responde solo con el JSON pedido."""

ESQUEMA = {
    "type": "object",
    "properties": {
        "entidades": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {"tipo": {"type": "string", "enum": TIPOS_E2}, "texto": {"type": "string"}},
                "required": ["tipo", "texto"],
            },
        }
    },
    "required": ["entidades"],
}


# ----------------------------------------------------------------------------- ejemplos

def respuesta_gold(o: Oracion, tipos=TIPOS_E2) -> str:
    """La respuesta 'ideal' de una oración de train, en el mismo JSON que se le pide al LLM."""
    ents = sorted((e for e in o.entidades if e[3] in tipos), key=lambda e: (e[1], tipos.index(e[3])))
    return json.dumps({"entidades": [{"tipo": e[3], "texto": o.mencion(e)} for e in ents]}, ensure_ascii=False)


class SelectorFijo:
    """k ejemplos fijos de train, al azar con semilla, cuidando que aparezcan los 3 tipos."""

    def __init__(self, train: list[Oracion], k: int = 5, semilla: int = 42, tipos=TIPOS_E2):
        cands = [o for o in train if 8 <= len(o.tokens) <= 40 and any(e[3] in tipos for e in o.entidades)]
        random.Random(semilla).shuffle(cands)
        elegidos, cubiertos = [], set()
        for o in cands:  # primero, cubrir todos los tipos
            nuevos = {e[3] for e in o.entidades if e[3] in tipos} - cubiertos
            if nuevos:
                elegidos.append(o); cubiertos |= nuevos
            if cubiertos == set(tipos):
                break
        for o in cands:  # luego, completar hasta k
            if len(elegidos) >= k:
                break
            if o not in elegidos:
                elegidos.append(o)
        self.ejemplos = elegidos[:k]

    def __call__(self, o: Oracion) -> list[Oracion]:
        return self.ejemplos


class SelectorDinamico:
    """Los k ejemplos de train más parecidos a la oración (BM25 sobre texto normalizado).

    Ojo con la fuga: si la oración del test está repetida en train, el ejemplo más parecido es
    ella misma con su respuesta. Por eso se reporta también el F1 sin duplicados.
    """

    def __init__(self, train: list[Oracion], k: int = 5):
        from rank_bm25 import BM25Okapi

        self.train = [o for o in train if o.tokens]
        self.bm25 = BM25Okapi([normalizar(o.texto).split() for o in self.train])
        self.k = k

    def __call__(self, o: Oracion) -> list[Oracion]:
        import numpy as np

        puntajes = self.bm25.get_scores(normalizar(o.texto).split())
        mejores = np.argsort(-puntajes, kind="stable")[: self.k]
        return [self.train[i] for i in mejores[::-1]]  # el más parecido queda al final, junto a la pregunta


def mensajes(o: Oracion, ejemplos: list[Oracion]) -> list[dict]:
    """Conversación que se envía al LLM: guía, ejemplos (pregunta/respuesta) y la oración."""
    m = [{"role": "system", "content": GUIA}]
    for ej in ejemplos:
        m.append({"role": "user", "content": f"Oración: {ej.texto}"})
        m.append({"role": "assistant", "content": respuesta_gold(ej)})
    m.append({"role": "user", "content": f"Oración: {o.texto}"})
    return m


# ----------------------------------------------------------------------------- respuesta → entidades

def parsear(respuesta: str) -> tuple[list[tuple[str, str]], bool]:
    """Lee el JSON del LLM. Devuelve ([(tipo, mención)], json_valido)."""
    try:
        datos = json.loads(respuesta)
    except (json.JSONDecodeError, TypeError):
        m = re.search(r"\{.*\}", respuesta or "", re.S)
        try:
            datos = json.loads(m.group(0)) if m else None
        except json.JSONDecodeError:
            datos = None
    if not isinstance(datos, dict) or not isinstance(datos.get("entidades"), list):
        # JSON cortado (p. ej. por el tope de tokens): se rescatan los objetos completos
        objs = re.findall(r'\{\s*"tipo"\s*:\s*"([^"]+)"\s*,\s*"texto"\s*:\s*"((?:[^"\\]|\\.)*)"\s*\}', respuesta or "")
        return [(t, x.strip()) for t, x in objs if t in TIPOS_E2 and x.strip()], False
    items = []
    for x in datos["entidades"]:
        if isinstance(x, dict) and x.get("tipo") in TIPOS_E2 and isinstance(x.get("texto"), str) and x["texto"].strip():
            items.append((x["tipo"], x["texto"].strip()))
    return items, True


def ubicar(o: Oracion, items: list[tuple[str, str]]) -> tuple[list[tuple[str, int, int, str]], int]:
    """Posiciona cada mención en la oración, por tipo (un tipo no bloquea a otro: anidamiento).

    Prefiere coincidencias de palabras completas ("DM" no debe caer dentro de "DM2"), sin
    distinguir mayúsculas y sin reutilizar una posición del mismo tipo. Devuelve
    (entidades, n_no_encontradas = alucinaciones).
    """
    texto = o.texto
    bajo = f" {texto.lower()} "
    ocupadas = {t: [] for t in TIPOS_E2}
    salida, faltan = [], 0
    for tipo, mencion in items:
        m = mencion.lower()
        hallado = None
        for patron in (f" {m} ", m):  # 1) palabra completa, 2) cualquier subcadena
            ini = 0
            while hallado is None:
                i = bajo.find(patron, ini)
                if i < 0:
                    break
                a = i + (1 if patron.startswith(" ") else 0) - 1   # -1 por el espacio agregado al inicio
                b = a + len(m)
                if all(b <= x or a >= y for x, y in ocupadas[tipo]):
                    hallado = (a, b)
                ini = i + 1
            if hallado:
                break
        if hallado:
            ocupadas[tipo].append(hallado)
            salida.append((o.id, hallado[0], hallado[1], tipo))
        else:
            faltan += 1
    return salida, faltan


# ----------------------------------------------------------------------------- llamada y caché

def llamar_ollama(modelo: str, msgs: list[dict], semilla: int = 42, num_ctx: int = 8192) -> str:
    """Una llamada determinista (temperatura 0, semilla fija) con salida JSON restringida al esquema."""
    import ollama

    opciones = {"temperature": 0, "seed": semilla, "num_ctx": num_ctx, "num_predict": NUM_PREDICT}
    kwargs = dict(model=modelo, messages=msgs, format=ESQUEMA, options=opciones)
    if modelo.startswith("qwen3"):
        kwargs["think"] = False  # sin "razonamiento" visible: más rápido y comparable
    try:
        r = ollama.chat(**kwargs)
    except TypeError:  # versiones antiguas del cliente sin `think`
        kwargs.pop("think", None)
        r = ollama.chat(**kwargs)
    return r["message"]["content"]


# ----------------------------------------------------------------------------- LLM de nube (techo de referencia)

PROVEEDORES = {
    "openai": {"base_url": None, "variable": "OPENAI_API_KEY"},
    # Gemini acepta el mismo formato que OpenAI en este endpoint
    "gemini": {"base_url": "https://generativelanguage.googleapis.com/v1beta/openai/", "variable": "GEMINI_API_KEY"},
}


def cargar_claves(ruta_env: Path) -> list[str]:
    """Lee claves desde un archivo .env (NOMBRE=valor), que git ignora. Devuelve los nombres cargados."""
    import os

    cargadas = []
    if Path(ruta_env).exists():
        for linea in Path(ruta_env).read_text().splitlines():
            if "=" in linea and not linea.strip().startswith("#"):
                k, v = linea.split("=", 1)
                os.environ[k.strip()] = v.strip().strip('"').strip("'")
                cargadas.append(k.strip())
    return cargadas


def _esquema_estricto() -> dict:
    """El mismo esquema, con las restricciones que exige el modo 'strict' de OpenAI."""
    import copy

    e = copy.deepcopy(ESQUEMA)
    e["additionalProperties"] = False
    e["properties"]["entidades"]["items"]["additionalProperties"] = False
    return e


def crear_llamador_api(proveedor: str):
    """Devuelve una función llamar(modelo, mensajes, semilla) -> str para la API del proveedor.

    Mismos parámetros que el LLM local cuando el modelo los acepta (temperatura 0, semilla, JSON con
    esquema). Si el modelo rechaza alguno (p. ej. los modelos de razonamiento no aceptan temperatura),
    se reintenta sin él y queda registrado en `llamar.parametros_omitidos`. Los tokens usados de la
    última llamada quedan en `llamar.ultimo_uso` (para calcular el costo).
    """
    import os

    from openai import BadRequestError, OpenAI

    cfg = PROVEEDORES[proveedor]
    clave = os.environ.get(cfg["variable"])
    if not clave:
        raise RuntimeError(f"Falta la clave {cfg['variable']} (agregarla al archivo .env de la raíz del proyecto)")
    cliente = OpenAI(api_key=clave, base_url=cfg["base_url"], max_retries=6, timeout=120)
    omitidos: set[str] = set()

    def llamar(modelo: str, msgs: list[dict], semilla: int = 42) -> str:
        params = {"temperature": 0, "seed": semilla, "max_completion_tokens": NUM_PREDICT * 2,
                  "response_format": {"type": "json_schema",
                                      "json_schema": {"name": "entidades", "schema": _esquema_estricto(), "strict": True}}}
        for k in omitidos:
            params.pop(k, None)
        for _ in range(4):
            try:
                r = cliente.chat.completions.create(model=modelo, messages=msgs, **params)
                break
            except BadRequestError as e:
                texto = str(e).lower()
                culpable = next((k for k in ["temperature", "seed", "max_completion_tokens"] if k in texto), None)
                if culpable is None and "response_format" in texto or culpable is None and "schema" in texto:
                    params["response_format"] = {"type": "json_object"}; omitidos.add("json_schema")
                    continue
                if culpable is None:
                    raise
                params.pop(culpable, None); omitidos.add(culpable)
        else:
            raise RuntimeError("La API rechazó la llamada incluso con parámetros mínimos")
        u = getattr(r, "usage", None)
        llamar.ultimo_uso = {"entrada": getattr(u, "prompt_tokens", 0) or 0, "salida": getattr(u, "completion_tokens", 0) or 0}
        llamar.parametros_omitidos = sorted(omitidos)
        return r.choices[0].message.content or ""

    llamar.ultimo_uso, llamar.parametros_omitidos = {}, []
    return llamar


def huella_ollama(modelo: str) -> dict:
    """Digest exacto del modelo instalado en Ollama (equivale a la 'revisión' de Hugging Face)."""
    try:
        import ollama

        for m in ollama.list()["models"]:
            nombre = m.get("model") or m.get("name")
            if nombre == modelo:
                return {"modelo": modelo, "digest": m.get("digest"), "tamano": m.get("size")}
    except Exception as e:
        return {"modelo": modelo, "digest": None, "error": type(e).__name__}
    return {"modelo": modelo, "digest": None}


class Cache:
    """Respuestas guardadas en JSONL (una línea por oración). Permite interrumpir y retomar."""

    def __init__(self, ruta: Path):
        self.ruta = Path(ruta)
        self.ruta.parent.mkdir(parents=True, exist_ok=True)
        self.datos = {}
        if self.ruta.exists():
            for linea in self.ruta.read_text(encoding="utf-8").splitlines():
                if linea.strip():
                    d = json.loads(linea)
                    self.datos[d["id"]] = d

    def __contains__(self, k):
        return k in self.datos

    def guardar(self, d: dict):
        self.datos[d["id"]] = d
        with open(self.ruta, "a", encoding="utf-8") as f:
            f.write(json.dumps(d, ensure_ascii=False) + "\n")


def correr(modelo: str, oraciones: list[Oracion], selector, cache: Cache, semilla: int = 42,
           llamar=llamar_ollama, cada: int = 50, registro=print) -> dict:
    """Pide al LLM las entidades de cada oración (salta las que ya están en caché)."""
    pendientes = [o for o in oraciones if o.id not in cache]
    t0 = time.time()
    for n, o in enumerate(pendientes, 1):
        msgs = mensajes(o, selector(o) if selector else [])
        t = time.time()
        resp = llamar(modelo, msgs, semilla)
        registro_cache = {"id": o.id, "respuesta": resp, "segundos": round(time.time() - t, 2),
                          "huella_prompt": sha256_bytes(json.dumps(msgs, ensure_ascii=False).encode())[:16]}
        if getattr(llamar, "ultimo_uso", None):  # solo en APIs de nube: tokens para calcular costo
            registro_cache["tokens"] = dict(llamar.ultimo_uso)
        cache.guardar(registro_cache)
        if n % cada == 0 or n == len(pendientes):
            vel = (time.time() - t0) / n
            registro(f"  {n}/{len(pendientes)} oraciones · {vel:.1f} s/oración · faltan ~{vel * (len(pendientes) - n) / 60:.0f} min")
    return {o.id: cache.datos[o.id] for o in oraciones}


def evaluar_respuestas(respuestas: dict, oraciones: list[Oracion]) -> dict:
    """Convierte respuestas en entidades por tipo y cuenta JSON inválidos y alucinaciones."""
    pred = {t: [] for t in TIPOS_E2}
    n_items = n_aluc = n_json_malo = 0
    por_id = {o.id: o for o in oraciones}
    for i, r in respuestas.items():
        items, ok = parsear(r["respuesta"])
        n_json_malo += not ok
        ents, faltan = ubicar(por_id[i], items)
        n_items += len(items); n_aluc += faltan
        for e in ents:
            pred[e[3]].append(e)
    seg = [r["segundos"] for r in respuestas.values()]
    return {"pred": pred, "tasa_alucinacion": n_aluc / max(n_items, 1), "menciones_predichas": n_items,
            "json_invalidos": n_json_malo, "segundos_por_oracion": sum(seg) / max(len(seg), 1)}
