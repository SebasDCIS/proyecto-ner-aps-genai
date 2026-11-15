"""Diagrama de la metodología (etapas KDD) para el manuscrito, a una columna."""
from pathlib import Path
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch

plt.rcParams.update({"font.family": "DejaVu Sans"})
etapas = [
    ("1. Selección", "CWLC v4 con la partición oficial;\nenfermedad, medicamento y abreviatura"),
    ("2. Preprocesamiento", "Auditoría de fugas y duplicados;\nhuellas SHA-256 de los archivos"),
    ("3. Transformación", "Encoders: etiquetas BIO por palabra.\nLLM: prompt con guía y salida JSON"),
    ("4. Modelado", "E1 encoders, E2 LLM locales y en la nube,\nE4 destilación, votación entre encoders"),
    ("5. Evaluación", "F1 estricto y laxo con IC 95 %, bootstrap\npareado, 3 semillas, recall por subgrupo"),
]
n = len(etapas); alto, gap = 1.25, 0.38
fig, ax = plt.subplots(figsize=(3.2, 3.3))
ax.set_xlim(0, 10); ax.set_ylim(0, n * (alto + gap)); ax.axis("off")
for k, (t, d) in enumerate(etapas):
    y = (n - 1 - k) * (alto + gap) + gap / 2
    ax.add_patch(FancyBboxPatch((0.05, y), 9.9, alto, boxstyle="round,pad=0.02,rounding_size=0.12",
                                fc="#eaf1f8", ec="#00629B", lw=0.9))
    ax.text(0.3, y + alto - 0.27, t, ha="left", va="center", fontsize=7, weight="bold", color="#00629B")
    ax.text(0.3, y + 0.4, d, ha="left", va="center", fontsize=6.3, linespacing=1.25)
    if k < n - 1:
        ax.annotate("", xy=(5, y - gap + 0.04), xytext=(5, y - 0.02),
                    arrowprops=dict(arrowstyle="-|>", color="#58595B", lw=0.9))
d = Path(__file__).resolve().parents[1] / "docs/manuscrito/figuras"
fig.savefig(d / "fig_metodologia.png", dpi=300, bbox_inches="tight"); fig.savefig(d / "fig_metodologia.pdf", bbox_inches="tight")
