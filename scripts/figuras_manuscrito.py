"""Figuras del manuscrito y de la presentación (PDF vectorial + PNG).

Lee solo resultados ya guardados en results/ (no entrena ni consulta modelos).
Uso: python scripts/figuras_manuscrito.py
"""
from __future__ import annotations

import glob
import json
import statistics as st
import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ / "src"))
SALIDA = RAIZ / "docs" / "manuscrito" / "figuras"
SALIDA.mkdir(parents=True, exist_ok=True)

# Paleta categórica validada (slots 1-3 pasan todos los pares en CVD) + violeta para la votación
AZUL, NARANJA, AQUA, VIOLETA = "#2a78d6", "#eb6834", "#1baf7a", "#6250d6"
TINTA, TINTA2, GRILLA = "#0b0b0b", "#52514e", "#e4e3df"

plt.rcParams.update({
    "font.family": "DejaVu Sans", "font.size": 8, "axes.edgecolor": TINTA2, "axes.labelcolor": TINTA,
    "xtick.color": TINTA2, "ytick.color": TINTA2, "axes.spines.top": False, "axes.spines.right": False,
    "axes.grid": True, "grid.color": GRILLA, "grid.linewidth": 0.6, "axes.axisbelow": True,
    "pdf.fonttype": 42, "legend.frameon": False,
})
TIPOS = ["Disease", "Medication", "Abbreviation"]
NOMBRE = {"Disease": "Enfermedad", "Medication": "Medicamento", "Abbreviation": "Abreviatura"}


def guardar(fig, nombre):
    fig.savefig(SALIDA / f"{nombre}.pdf", bbox_inches="tight")
    fig.savefig(SALIDA / f"{nombre}.png", dpi=220, bbox_inches="tight")
    plt.close(fig)


def e1(clave, tipo):
    rs = [json.load(open(f))["resultados"] for f in sorted(glob.glob(str(RAIZ / f"results/e1_completo/{clave}_{tipo}_s*.json")))]
    f1 = st.mean(r["estricto"]["f1"] for r in rs)
    lo = st.mean(r["estricto"]["ic95"][0] for r in rs)
    hi = st.mean(r["estricto"]["ic95"][1] for r in rs)
    return f1, lo, hi


def llm(archivo, tipo):
    v = json.load(open(RAIZ / archivo))["resultados"]["por_tipo"][tipo]["estricto"]
    return v["f1"], v["ic95"][0], v["ic95"][1]


VOTO6 = {"Disease": (0.837, 0.815, 0.857), "Medication": (0.831, 0.759, 0.889), "Abbreviation": (0.957, 0.945, 0.968)}
SISTEMAS = [  # (etiqueta, familia, función)
    ("Votación (2 encoders × 3 semillas)", "voto", lambda t: VOTO6[t]),
    ("E1 · encoder chileno", "enc", lambda t: e1("chileno_clinico", t)),
    ("E1 · encoder español", "enc", lambda t: e1("espanol_clinico", t)),
    ("E1 · RigoBERTa Clinical (large)", "enc", lambda t: e1("rigoberta_clinico", t)),
    ("Gemini 3.1 Pro · dinámico", "nube", lambda t: llm("results/e2nube_completo/gemini_gemini-3.1-pro-preview_few_shot_dinamico.json", t)),
    ("GPT-5.2 · dinámico", "nube", lambda t: llm("results/e2nube_completo/openai_gpt-5.2_few_shot_dinamico.json", t)),
    ("Gemini 3.1 Pro · zero-shot", "nube", lambda t: llm("results/e2nube_completo/gemini_gemini-3.1-pro-preview_zero_shot.json", t)),
    ("GPT-5.2 · zero-shot", "nube", lambda t: llm("results/e2nube_completo/openai_gpt-5.2_zero_shot.json", t)),
    ("Qwen 2.5 7B · dinámico", "local", lambda t: llm("results/e2_completo/qwen2.5-7b_few_shot_dinamico.json", t)),
    ("Llama 3.1 8B · dinámico", "local", lambda t: llm("results/e2_completo/llama3.1-8b_few_shot_dinamico.json", t)),
    ("Qwen 2.5 7B · zero-shot", "local", lambda t: llm("results/e2_completo/qwen2.5-7b_zero_shot.json", t)),
    ("Llama 3.1 8B · zero-shot", "local", lambda t: llm("results/e2_completo/llama3.1-8b_zero_shot.json", t)),
]
COLOR = {"voto": VIOLETA, "enc": AZUL, "nube": AQUA, "local": NARANJA}
LEYENDA = {"voto": "Votación de encoders", "enc": "Encoder ajustado (E1)", "nube": "LLM comercial (E2 nube)", "local": "LLM local 7–8B (E2)"}


def fig_comparacion():
    fig, ejes = plt.subplots(1, 3, figsize=(7.16, 3.3), sharey=True)
    ys = list(range(len(SISTEMAS)))[::-1]
    for ax, t in zip(ejes, TIPOS):
        for y, (etq, fam, fn) in zip(ys, SISTEMAS):
            f1, lo, hi = fn(t)
            ax.plot([lo, hi], [y, y], color=COLOR[fam], lw=1.6, solid_capstyle="round")
            ax.plot(f1, y, "o", ms=4.6, color=COLOR[fam], mec="white", mew=0.8, zorder=3)
        ref = e1("chileno_clinico", t)[0] if t == "Disease" else max(e1("chileno_clinico", t)[0], e1("espanol_clinico", t)[0])
        ax.axvline(ref, color=TINTA2, lw=0.6, ls=(0, (3, 3)))
        ax.set_xlim(0.38, 1.0)
        ax.set_title(NOMBRE[t], fontsize=8.5, color=TINTA, loc="left")
        ax.set_xlabel("F1 estricto (IC 95 %)")
        ax.grid(axis="y", visible=False)
    ejes[0].set_yticks(ys)
    ejes[0].set_yticklabels([s[0] for s in SISTEMAS])
    manijas = [plt.Line2D([], [], marker="o", ls="-", color=COLOR[k], label=v, ms=4.5) for k, v in LEYENDA.items()]
    fig.legend(handles=manijas, loc="lower center", ncol=4, bbox_to_anchor=(0.55, -0.06), fontsize=7.2)
    fig.tight_layout(rect=(0, 0.04, 1, 1))
    guardar(fig, "fig_comparacion_f1")


def fig_estrategias():
    """Efecto de la estrategia de prompting en cada LLM (F1 estricto)."""
    def media_fijo(modelo, t):
        return st.mean(json.load(open(f))["resultados"]["por_tipo"][t]["estricto"]["f1"]
                       for f in sorted(glob.glob(str(RAIZ / f"results/e2_completo/{modelo}_few_shot_fijo_s*.json"))))
    modelos = [("Llama 3.1 8B", "llama3.1-8b", "#b8471c", "o"), ("Qwen 2.5 7B", "qwen2.5-7b", NARANJA, "s")]
    nube = [("GPT-5.2", "openai_gpt-5.2", "#0f7f57", "o"), ("Gemini 3.1 Pro", "gemini_gemini-3.1-pro-preview", AQUA, "s")]
    fig, ejes = plt.subplots(1, 3, figsize=(7.16, 2.3), sharey=True)
    for ax, t in zip(ejes, TIPOS):
        for nom, arch, col, mk in modelos:
            ys = [llm(f"results/e2_completo/{arch}_zero_shot.json", t)[0], media_fijo(arch, t),
                  llm(f"results/e2_completo/{arch}_few_shot_dinamico.json", t)[0]]
            ax.plot([0, 1, 2], ys, marker=mk, color=col, lw=1.6, ms=4.5, mec="white", label=nom)
        for nom, arch, col, mk in nube:
            ys = [llm(f"results/e2nube_completo/{arch}_zero_shot.json", t)[0],
                  llm(f"results/e2nube_completo/{arch}_few_shot_dinamico.json", t)[0]]
            ax.plot([0, 2], ys, marker=mk, color=col, lw=1.6, ms=4.5, mec="white", label=nom, ls=(0, (4, 2)))
        mejor = max(e1("chileno_clinico", t)[0], e1("espanol_clinico", t)[0])
        ax.axhline(mejor, color=AZUL, lw=1.0)
        ax.text(-0.15, mejor + 0.012, "mejor E1", color=TINTA2, fontsize=6.5, va="bottom")
        ax.set_xticks([0, 1, 2]); ax.set_xticklabels(["zero-shot", "fijo", "dinámico"])
        ax.set_title(NOMBRE[t], fontsize=8.5, loc="left"); ax.set_ylim(0.38, 1.0); ax.set_xlim(-0.2, 2.6)
        ax.grid(axis="x", visible=False)
    ejes[0].set_ylabel("F1 estricto")
    h, l = ejes[0].get_legend_handles_labels()
    fig.legend(h, l, loc="lower center", ncol=4, bbox_to_anchor=(0.5, -0.1), fontsize=7.2)
    fig.tight_layout(rect=(0, 0.05, 1, 1))
    guardar(fig, "fig_estrategias_llm")


# Calidad del maestro (F1 de las etiquetas silver contra el gold de esas mismas oraciones), media de 3 semillas.
# Se calcula en el notebook 04 y quedó registrada en docs/bitacora.md (entrada del 2026-10-27).
MAESTRO = {"Disease": [0.532, 0.524, 0.586, 0.595], "Medication": [0.662, 0.663, 0.660, 0.687],
           "Abbreviation": [0.526, 0.496, 0.547, 0.550]}


def fig_e4():
    """Curva de destilación (E4): F1 estricto medio de 3 semillas según el número de oraciones gold."""
    import collections
    datos = collections.defaultdict(list)
    for f in glob.glob(str(RAIZ / "results/e4_completo/*.json")):
        d = json.load(open(f))
        nombre = Path(f).stem  # p.ej. silver_gold_n50_Disease_s42
        partes = nombre.split("_")
        cond = "solo_gold" if nombre.startswith("solo_gold") else "silver_gold"
        n = int([p for p in partes if p.startswith("n") and p[1:].isdigit()][0][1:])
        tipo = partes[-2]
        datos[(cond, tipo, n)].append(d["resultados"]["estricto"]["f1"])
    fig, ejes = plt.subplots(1, 3, figsize=(7.16, 2.3), sharey=True)
    ns = [0, 10, 50, 100]
    for ax, t in zip(ejes, TIPOS):
        sg = [st.mean(datos[("silver_gold", t, n)]) for n in ns]
        so = [st.mean(datos[("solo_gold", t, n)]) for n in ns[1:]]
        ax.plot(ns, sg, "o-", color=AQUA, lw=1.6, ms=4.5, mec="white", label="Alumno: silver + gold")
        ax.plot(ns[1:], so, "s-", color=NARANJA, lw=1.6, ms=4.5, mec="white", label="Solo gold")
        ax.plot(ns, MAESTRO[t], "^--", color=TINTA2, lw=1.0, ms=4, label="Maestro (Qwen 7B anotador)")
        e1ref = e1("espanol_clinico", t)[0]
        ax.axhline(e1ref, color=AZUL, lw=1.0)
        ax.text(102, e1ref, "E1 (8.014 gold)", color=TINTA2, fontsize=6.5, va="bottom", ha="right")
        ax.set_xticks(ns); ax.set_xlabel("Oraciones gold"); ax.set_title(NOMBRE[t], fontsize=8.5, loc="left")
        ax.set_ylim(0, 1.0); ax.grid(axis="x", visible=False)
    ejes[0].set_ylabel("F1 estricto")
    h, l = ejes[0].get_legend_handles_labels()
    fig.legend(h, l, loc="lower center", ncol=3, bbox_to_anchor=(0.5, -0.12), fontsize=7.2)
    fig.tight_layout(rect=(0, 0.06, 1, 1))
    guardar(fig, "fig_destilacion_e4")
    return datos


def fig_tipologia():
    d = json.load(open(RAIZ / "results/e5_analisis/analisis_errores.json"))
    tip, esp = d["tipologia"]["Disease"], d["espurias_enfermedad"]
    sistemas = ["E1 chileno (s42)", "E1 español (s42)", "E1 RigoBERTa (s42)", "GPT-5.2 ej. parecidos",
                "Gemini 3.1 Pro ej. parecidos", "Qwen 7B ej. parecidos", "Llama 8B ej. parecidos"]
    etiquetas = ["E1 chileno", "E1 español", "E1 RigoBERTa", "GPT-5.2 dinámico", "Gemini dinámico", "Qwen 7B dinámico", "Llama 8B dinámico"]
    cats = [("correcta", "Correcta", AZUL), ("más larga", "Límite más largo", "#8fb8ea"), ("más corta", "Límite más corto", "#c3d8f2"),
            ("omitida", "Omitida", "#b9b8b2"), ("esp_finding", "Espuria sobre un hallazgo", NARANJA), ("esp_otra", "Otra espuria", "#f3a684")]
    fig, ax = plt.subplots(figsize=(3.5, 2.6))
    for i, s in enumerate(sistemas):
        finding = esp["Finding"][s] + esp.get("Body_Part + Finding", {}).get(s, 0) + esp.get("Abbreviation + Finding", {}).get(s, 0)
        vals = {"correcta": tip["correcta"][s], "más larga": tip["más larga"][s], "más corta": tip["más corta"][s] + tip["desplazada"][s],
                "omitida": tip["omitida"][s], "esp_finding": finding, "esp_otra": tip["espuria"][s] - finding}
        izq = 0
        for k, _, col in cats:
            ax.barh(i, vals[k], left=izq, color=col, height=0.62, edgecolor="white", linewidth=0.8)
            izq += vals[k]
    ax.set_yticks(range(len(sistemas))); ax.set_yticklabels(etiquetas); ax.invert_yaxis()
    ax.set_xlabel("Menciones de enfermedad (test, 1.071 en el gold)"); ax.grid(axis="y", visible=False)
    manijas = [plt.Rectangle((0, 0), 1, 1, color=c) for _, _, c in cats]
    ax.legend(manijas, [n for _, n, _ in cats], loc="upper center", bbox_to_anchor=(0.42, -0.2), ncol=2, fontsize=6.6)
    guardar(fig, "fig_tipologia_errores")


def fig_subgrupos():
    d = json.load(open(RAIZ / "results/e5_analisis/analisis_errores.json"))
    me = d["mal_escritas"]["enfermedad"]; ab = d["abreviaturas_por_frecuencia"]["recall"]
    sist = [("E1 chileno (3 semillas)", "E1 chileno", AZUL), ("E1 RigoBERTa (3 semillas)", "E1 RigoBERTa", "#8fb8ea"),
            ("GPT-5.2 ej. parecidos", "GPT-5.2 dinámico", AQUA), ("Gemini 3.1 Pro sin ejemplos", "Gemini zero-shot", "#7fd3b4")]
    grupos = [("Enfermedad\nbien escrita\n(n = 1.040)", lambda k: me["recall bien escritas"][k]),
              ("Enfermedad\nmal escrita\n(n = 31)", lambda k: me["recall mal escritas"][k]),
              ("Abreviatura\nfrecuente\n(n = 774)", lambda k: ab["frecuente (≥10 en train)"][k]),
              ("Abreviatura\nnunca vista\n(n = 66)", lambda k: ab["nunca vista en train"][k])]
    fig, ax = plt.subplots(figsize=(3.5, 2.4))
    w = 0.19
    for j, (k, etq, col) in enumerate(sist):
        xs = [i + (j - 1.5) * w for i in range(len(grupos))]
        ax.bar(xs, [g[1](k) for g in grupos], width=w - 0.02, color=col, label=etq)
    ax.set_xticks(range(len(grupos))); ax.set_xticklabels([g[0] for g in grupos], fontsize=6.4)
    ax.set_ylabel("Recall estricto"); ax.set_ylim(0, 1.05); ax.grid(axis="x", visible=False)
    ax.legend(loc="upper center", bbox_to_anchor=(0.5, -0.3), ncol=2, fontsize=6.6)
    guardar(fig, "fig_subgrupos_recall")


if __name__ == "__main__":
    fig_comparacion()
    fig_estrategias()
    datos = fig_e4()
    fig_tipologia()
    fig_subgrupos()
    print("figuras en", SALIDA)
