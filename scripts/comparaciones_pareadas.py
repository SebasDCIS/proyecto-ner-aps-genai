"""Comparaciones pareadas citadas en el manuscrito, guardadas en un solo JSON.

No entrena ni consulta ningún modelo: lee las predicciones ya guardadas
(results/cache/e1_completo/*.pkl y las cachés de respuestas de E2 / E2 nube).
Uso: python scripts/comparaciones_pareadas.py  ->  results/e5_analisis/comparaciones_pareadas.json
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ / "src"))

from analisis import errores as A  # noqa: E402
from datos.cwlc import cargar_split  # noqa: E402

TIPOS = ["Disease", "Medication", "Abbreviation"]
SEMILLAS = [42, 43, 44]
N_BOOT = 1000


def fila(a, b, tipo, dif, lo, hi, **extra):
    return {"A": a, "B": b, "tipo": tipo, "dif_F1": round(dif, 4), "ic95": [round(lo, 4), round(hi, 4)],
            "significativa": bool(lo > 0 or hi < 0), **extra}


def main():
    carpeta = RAIZ / "data" / "raw" / "cwlc"
    train, test = cargar_split(carpeta, "train"), cargar_split(carpeta, "test")
    G = A.gold_por_tipo(test)

    cache_e1 = RAIZ / "results" / "cache" / "e1_completo"
    e1 = {(k, s): A.cargar_e1(cache_e1, k, s) for k in ["espanol_clinico", "chileno_clinico", "rigoberta_clinico"] for s in SEMILLAS}

    def llm(carpeta_res, nombre):
        r = A.cargar_llm(RAIZ / "results" / "cache" / carpeta_res / f"{nombre}.jsonl", test)
        assert r is not None, f"corrida incompleta: {nombre}"
        return r[0]

    L = {
        "Gemini dinámico": llm("e2nube_completo", "gemini_gemini-3.1-pro-preview_few_shot_dinamico"),
        "Gemini zero-shot": llm("e2nube_completo", "gemini_gemini-3.1-pro-preview_zero_shot"),
        "GPT-5.2 dinámico": llm("e2nube_completo", "openai_gpt-5.2_few_shot_dinamico"),
        "GPT-5.2 zero-shot": llm("e2nube_completo", "openai_gpt-5.2_zero_shot"),
        "Qwen dinámico": llm("e2_completo", "qwen2.5-7b_few_shot_dinamico"),
        "Llama dinámico": llm("e2_completo", "llama3.1-8b_few_shot_dinamico"),
    }
    for m in ["qwen2.5-7b", "llama3.1-8b"]:
        for s in SEMILLAS:
            L[f"{'Qwen' if m.startswith('qwen') else 'Llama'} fijo s{s}"] = llm("e2_completo", f"{m}_few_shot_fijo_s{s}")

    salida = {"descripcion": "Bootstrap pareado por oración (1.000 remuestreos), F1 estricto salvo que se indique otra cosa.",
              "llm_vs_llm": [], "llm_vs_e1": [], "dinamico_vs_fijo": [], "e1_vs_e1": [], "votacion_6": [], "mal_escritas": []}

    for t in TIPOS:
        salida["llm_vs_llm"].append(fila("Gemini dinámico", "GPT-5.2 dinámico", t, *A.diferencia_pareada(G[t], L["Gemini dinámico"][t], L["GPT-5.2 dinámico"][t], N_BOOT)))
        for nombre in ["Gemini dinámico", "GPT-5.2 dinámico", "Qwen dinámico", "Llama dinámico"]:
            for k in ["espanol_clinico", "chileno_clinico"]:
                for s in SEMILLAS:
                    salida["llm_vs_e1"].append(fila(nombre, f"{k} s{s}", t, *A.diferencia_pareada(G[t], L[nombre][t], e1[(k, s)][t], N_BOOT)))
        for mod in ["Qwen", "Llama"]:
            for s in SEMILLAS:
                salida["dinamico_vs_fijo"].append(fila(f"{mod} dinámico", f"{mod} fijo s{s}", t, *A.diferencia_pareada(G[t], L[f"{mod} dinámico"][t], L[f"{mod} fijo s{s}"][t], N_BOOT)))
        for s in SEMILLAS:
            salida["e1_vs_e1"].append(fila(f"chileno_clinico s{s}", f"espanol_clinico s{s}", t, *A.diferencia_pareada(G[t], e1[("chileno_clinico", s)][t], e1[("espanol_clinico", s)][t], N_BOOT)))
            for k in ["espanol_clinico", "chileno_clinico"]:
                salida["e1_vs_e1"].append(fila(f"rigoberta_clinico s{s}", f"{k} s{s}", t, *A.diferencia_pareada(G[t], e1[("rigoberta_clinico", s)][t], e1[(k, s)][t], N_BOOT)))
        modelos6 = [e1[(k, s)][t] for k in ["espanol_clinico", "chileno_clinico"] for s in SEMILLAS]
        voto = A.votacion(modelos6)
        r = A.f1_con_ic(G[t], voto)
        salida["votacion_6"].append({"tipo": t, "f1": round(r["f1"], 4), "ic95": [round(x, 4) for x in r["ic95"]],
                                     "precision": round(r["precision"], 4), "recall": round(r["recall"], 4)})
        for (k, s), p in e1.items():
            if k == "rigoberta_clinico":
                continue
            salida["votacion_6"].append(fila("votación 6", f"{k} s{s}", t, *A.diferencia_pareada(G[t], voto, p[t], N_BOOT)))

    detector = A.DetectorOrtografia(train)
    mal = A.menciones_mal_escritas(test, detector)
    grupo = [e for e in mal if e[3] == "Disease"]
    for nombre in ["Gemini zero-shot", "Gemini dinámico", "GPT-5.2 dinámico"]:
        for k in ["espanol_clinico", "chileno_clinico", "rigoberta_clinico"]:
            for s in SEMILLAS:
                obs, lo, hi = A.dif_recall_pareada(grupo, L[nombre]["Disease"], e1[(k, s)]["Disease"], N_BOOT)
                salida["mal_escritas"].append({"A": nombre, "B": f"{k} s{s}", "n": len(grupo), "dif_recall": round(obs, 4),
                                               "ic95": [round(lo, 4), round(hi, 4)], "significativa": bool(lo > 0 or hi < 0)})

    destino = RAIZ / "results" / "e5_analisis" / "comparaciones_pareadas.json"
    destino.write_text(json.dumps(salida, ensure_ascii=False, indent=1))
    print("guardado", destino)


if __name__ == "__main__":
    main()
