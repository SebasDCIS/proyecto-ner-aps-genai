"""Corridas del techo de referencia (LLM de nube), compartidas por el notebook 03b y por scripts/correr_nube.py.

Cada corrida (modelo × estrategia) avanza oración por oración y guarda cada respuesta al llegar. Si el
proveedor corta por cuota diaria, se detiene limpio y la próxima ejecución sigue donde quedó. Cuando una
corrida completa todas sus oraciones, se evalúa y se guarda su JSON con huella.
"""
from __future__ import annotations

import json
from collections import Counter
from pathlib import Path

from modelos import e2_llm as E2
from modelos.e1_encoder import evaluar
from reproducibilidad import huella_completa, sha256_bytes


def nombre_corrida(m: dict, est: str) -> str:
    return f"{m['proveedor']}_{m['modelo'].replace(':', '-').replace('/', '-')}_{est}"


def correr_corridas(nube, estrategias, oraciones, train, test, dinamico, carpeta_datos, k, modo,
                    salida: Path, cache_dir: Path, registro=print) -> list[dict]:
    """Ejecuta todas las corridas pendientes. Devuelve un estado por corrida (hecha / parcial / ya existía)."""
    import openai

    estados = []
    for m in nube:
        llamar = E2.crear_llamador_api(m["proveedor"], m.get("parametros_extra"))
        for est in estrategias:
            n = nombre_corrida(m, est)
            ruta = salida / f"{n}.json"
            ors = oraciones[: m["max_oraciones"]] if m.get("max_oraciones") else oraciones
            if ruta.exists():
                estados.append({"corrida": n, "estado": "ya existía", "hechas": len(ors), "total": len(ors)})
                registro(f"(ya existe) {ruta.name}")
                continue
            cache = E2.Cache(cache_dir / f"{n}.jsonl")
            registro(f"\n=== {m['proveedor']}:{m['modelo']} · {est} · {sum(o.id in cache for o in ors)}/{len(ors)} hechas ===")
            try:
                resp = E2.correr(m["modelo"], ors, dinamico if est == "few_shot_dinamico" else None, cache, llamar=llamar,
                                 cada=100, registro=registro)
            except openai.RateLimitError as e:
                hechas = sum(o.id in cache for o in ors)
                registro(f"  Cuota del proveedor alcanzada: {hechas}/{len(ors)} guardadas. Seguirá en la próxima ejecución.")
                estados.append({"corrida": n, "estado": "parcial (cuota)", "hechas": hechas, "total": len(ors)})
                if m["proveedor"] == "gemini":   # la cuota es por modelo y día: no tiene sentido seguir con este modelo hoy
                    break
                continue
            ev = E2.evaluar_respuestas(resp, ors)
            tok_e = sum(r.get("tokens", {}).get("entrada", 0) for r in resp.values())
            tok_s = sum(r.get("tokens", {}).get("salida", 0) for r in resp.values())
            versiones = Counter(r.get("modelo_servido") for r in resp.values())
            fechas = sorted(r["fecha"] for r in resp.values() if r.get("fecha"))
            res = {"modelo": f"{m['proveedor']}:{m['modelo']}", "estrategia": est, "tasa_alucinacion": ev["tasa_alucinacion"],
                   "json_invalidos": ev["json_invalidos"], "segundos_por_oracion": ev["segundos_por_oracion"],
                   "tokens_entrada": tok_e, "tokens_salida": tok_s,
                   "costo_usd": (tok_e * m["precio_entrada"] + tok_s * m["precio_salida"]) / 1e6,
                   "parametros_omitidos": llamar.parametros_omitidos,
                   "versiones_servidas": dict(versiones), "periodo": [fechas[0], fechas[-1]] if fechas else None,
                   "por_tipo": {}}
            for tipo in E2.TIPOS_E2:
                gold = [e for o in ors for e in o.entidades if e[3] == tipo]
                res["por_tipo"][tipo] = evaluar(gold, ev["pred"][tipo], ors, tipo, train=train)
            config = {**m, "estrategia": est, "k": k, "temperatura": 0, "guia": sha256_bytes(E2.GUIA.encode()), "modo": modo,
                      "n_oraciones": len(ors), "oraciones": sha256_bytes(json.dumps([o.id for o in ors]).encode())}
            huella = huella_completa(config, carpeta_datos, splits={"train": train, "test": test})
            salida.mkdir(parents=True, exist_ok=True)
            ruta.write_text(json.dumps({"config": config, "resultados": res, "huella": huella}, indent=2, ensure_ascii=False, default=str))
            registro("  F1 estricto: " + "  ".join(f"{t[:4]}={res['por_tipo'][t]['estricto']['f1']:.3f}" for t in E2.TIPOS_E2)
                     + f" · USD {res['costo_usd']:.2f} · versiones {dict(versiones)}")
            estados.append({"corrida": n, "estado": "hecha", "hechas": len(ors), "total": len(ors)})
    return estados
