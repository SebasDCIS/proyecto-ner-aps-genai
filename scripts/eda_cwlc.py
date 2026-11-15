"""Estudio descriptivo del CWLC (sección III.B del manuscrito): cifras y figura."""
import json, statistics as st, sys
from collections import Counter
from pathlib import Path
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
RAIZ = Path(__file__).resolve().parents[1]; sys.path.insert(0, str(RAIZ))
from src.datos.cwlc import cargar_split, es_abreviada

CARP = RAIZ / "data/raw/cwlc"; TIP = ["Disease", "Medication", "Abbreviation"]
NOM = {"Disease": "Enfermedad", "Medication": "Medicamento", "Abbreviation": "Abreviatura"}
out = {}
splits = {s: cargar_split(CARP, s) for s in ["train", "dev", "test"]}
for s, ors in splits.items():
    lon = [len(o.tokens) for o in ors]
    d = {"oraciones": len(ors), "tokens": sum(lon), "mediana_tokens": st.median(lon),
         "p90_tokens": sorted(lon)[int(.9*len(lon))], "max_tokens": max(lon)}
    for t in TIP:
        ents = [(e, o) for o in ors for e in o.entidades if e[3] == t]
        d[f"n_{t}"] = len(ents)
        d[f"oraciones_con_{t}_%"] = round(100*sum(any(e[3]==t for e in o.entidades) for o in ors)/len(ors), 1)
        ltok = [len(o.texto[e[1]:e[2]].split()) for e, o in ents]
        d[f"mediana_tokens_{t}"] = st.median(ltok)
        d[f"unica_{t}_%"] = round(100*sum(1 for x in ltok if x == 1)/len(ltok), 1)
        if t != "Abbreviation":
            d[f"{t}_abreviada_%"] = round(100*sum(es_abreviada(e, o) for e, o in ents)/len(ents), 1)
    d["oraciones_sin_entidad_3tipos_%"] = round(100*sum(not any(e[3] in TIP for e in o.entidades) for o in ors)/len(ors), 1)
    out[s] = d
tr, te = splits["train"], splits["test"]
abrev_tr = Counter(o.texto[e[1]:e[2]].lower() for o in tr for e in o.entidades if e[3] == "Abbreviation")
abrev_te = [o.texto[e[1]:e[2]].lower() for o in te for e in o.entidades if e[3] == "Abbreviation"]
out["abreviaturas"] = {"distintas_train": len(abrev_tr), "top15_train": abrev_tr.most_common(15),
    "test_no_vistas_en_train_%": round(100*sum(a not in abrev_tr for a in abrev_te)/len(abrev_te), 1),
    "top15_cubre_train_%": round(100*sum(c for _, c in abrev_tr.most_common(15))/sum(abrev_tr.values()), 1)}
med_tr = Counter(o.texto[e[1]:e[2]].lower() for o in tr for e in o.entidades if e[3] == "Medication")
med_te = [o.texto[e[1]:e[2]].lower() for o in te for e in o.entidades if e[3] == "Medication"]
dis_tr = Counter(o.texto[e[1]:e[2]].lower() for o in tr for e in o.entidades if e[3] == "Disease")
dis_te = [o.texto[e[1]:e[2]].lower() for o in te for e in o.entidades if e[3] == "Disease"]
out["no_vistas_test_%"] = {"Medication": round(100*sum(m not in med_tr for m in med_te)/len(med_te),1),
                            "Disease": round(100*sum(m not in dis_tr for m in dis_te)/len(dis_te),1)}
(RAIZ/"results/e5_analisis/eda_cwlc.json").write_text(json.dumps(out, ensure_ascii=False, indent=2))

# figura (una columna): (a) largo de oración, (b) 12 abreviaturas más frecuentes
plt.rcParams.update({"font.size": 8, "font.family": "DejaVu Sans"})
fig, ax = plt.subplots(2, 1, figsize=(3.4, 3.9), gridspec_kw={"height_ratios": [1, 1.15]})
ax[0].hist([min(len(o.tokens), 80) for o in tr], bins=40, color="#1f3b73")
ax[0].set_xlabel("Tokens por oración (80 = 80 o más)"); ax[0].set_ylabel("Oraciones")
ax[0].set_title("(a) Largo de las oraciones de entrenamiento", fontsize=8)
top = abrev_tr.most_common(12)[::-1]
ax[1].barh([a for a, _ in top], [c for _, c in top], color="#5b7fb8")
ax[1].set_xlabel("Menciones en entrenamiento"); ax[1].set_title("(b) Las 12 abreviaturas más frecuentes", fontsize=8)
for a in ax: a.spines[["top", "right"]].set_visible(False)
fig.tight_layout()
d = RAIZ/"docs/manuscrito/figuras"; fig.savefig(d/"fig_eda_cwlc.pdf"); fig.savefig(d/"fig_eda_cwlc.png", dpi=300)
print(json.dumps(out, ensure_ascii=False, indent=1))
