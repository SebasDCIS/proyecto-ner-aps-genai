# Verificación de datos para arrancar NER clínico con el CWLC

Fecha de verificación: 2026-10-25. Leyenda: **[C]** confirmado · **[NC]** no confirmado · **[X]** contradictorio.
Fuentes: WebFetch/WebSearch, PubMed y Consensus. Zenodo y Hugging Face no respondieron por curl (proxy), así que todo se leyó vía WebFetch. Los conteos que entrega WebFetch deben revisarse localmente (`wc -l` o un conteo con pandas) una vez descargados los archivos.

---

## 1. Chilean Waiting List Corpus (CWLC): versiones

| Versión | Derivaciones | Entidades | Splits | Formato | Licencia | Estado |
|---|---|---|---|---|---|---|
| Zenodo 3926705 (v1, 01-07-2020) | 900 (32,2 % anidadas) | no se listan en la página | no indicado | archivos **restringidos** | no indicada | [C] https://zenodo.org/records/3926705 |
| Zenodo 5518225 (v3, fechada 23-11-2020) | 5.000 (58,6 % médicas, 41,4 % dentales), 110.771 tokens | 10 tipos + 6 atributos + relaciones | train/dev/test en `cwlc.zip` (IOB2), sin tamaños | `cwlc_raw.zip` = standoff (brat); `cwlc.zip` = IOB2 | CC BY-NC-SA 4.0 en la descripción, pero "Other (Not Open)" en Rights | [C] datos / [X] licencia. https://zenodo.org/records/5518225 |
| Zenodo 5591011 (v4, creado 21-10-2021) | 5.000 (igual que v3) | 10 tipos | train/dev/test (IOB2) + `cwlc_folds.zip` (10 folds, 31,9 MB) | standoff + IOB2. `cwlc.zip` tiene el **mismo md5 que v3** (d16cc094…) | CC BY-NC-SA 4.0 / "Other (Not Open)" | [C] / [X] licencia. https://zenodo.org/records/5591011 |
| Zenodo 7555181 (v5, creado 20-01-2023) | **9.000** derivaciones, >48 % anidadas | 10 tipos, 6 atributos, relaciones | **no indicados** | `cwlc.zip` (standoff, 6,8 MB) + `cwlc_conll-format.zip` (5,3 MB) | CC BY-NC-SA 4.0 / "Other (Not Open)" | [C] tamaño / [NC] splits / [X] licencia. https://zenodo.org/records/7555181 |
| HF `plncmm/wl` (6 commits, 25-05-2022) | no indicado; train.conll 2,28 MB, dev 259 kB, test 292 kB | 11 tipos BIO **planos**: Disease, Medication, Abbreviation, Body_Part, Family_Member, Sign_or_Symptom, Laboratory_or_Test_Result, Clinical_Finding, Diagnostic_Procedure, Laboratory_Procedure, Therapeutic_Procedure. Último commit: "procedure tag deleted". El loader lee solo la última columna, así que no hay anidamiento. | train/validation/test | CoNLL + script `wl.py` (el visor está deshabilitado) | `wl.py` dice CC BY 4.0; el repo no tiene etiqueta de licencia | [C] archivos / [X] licencia frente a Zenodo. https://huggingface.co/datasets/plncmm/wl , https://huggingface.co/datasets/plncmm/wl/blob/main/wl.py |
| HF `plncmm/wl-disease`, `-medication`, `-body-part`, `-finding`, `-procedure`, `-abbreviation`, `-family-member` | un repo por tipo de entidad (wl-disease: train 2,55 MB / dev 287 kB / test 308 kB) | 1 tipo por repo | train/dev/test (.conll) | CoNLL + script | CC BY-NC 4.0 (etiqueta en HF) | [C] https://huggingface.co/plncmm , https://huggingface.co/datasets/plncmm/wl-disease/tree/main |

### Artículos de referencia

- **Báez et al. 2020, ClinicalNLP**: 900 derivaciones, 9.029 entidades. Corresponde a v1. [C] https://aclanthology.org/2020.clinicalnlp-1.32 (DOI 10.18653/v1/2020.clinicalnlp-1.32)
- **Báez et al. 2022, ACM HEALTH 3(3)**, "Automatic Extraction of Nested Entities in Clinical Referrals in Spanish". Usa 5.000 derivaciones con 10 tipos (la mejor es Abbreviation y la más difícil Finding) y un modelo Multiple Single-entity con embeddings clínicos + Flair. [C] DOI 10.1145/3498324 (resumen vía Consensus; dl.acm.org no cargó). Rojas et al. citan para Báez 2022 un F1 de **80,27**: [C], solo como cita secundaria.
- **Rojas et al. 2022, LOUHI**: F1 **83,16** (P 84,31 / R 82,04, media de 3 semillas, F1 micro estricto). Modelo MLC (Multiple LSTM-CRF) + Clinical Flair. Usa **7 tipos de entidad** (el paper no los nombra), 87.024 menciones, 48,23 % anidadas. Splits: train 15.290 / dev 1.911 / test 1.912 **oraciones**, con 69.847 / 8.340 / 8.837 entidades. Cita Zenodo 3926705 como fuente y dice usar "los mismos splits" que Báez 2022. Código: github.com/TeMU-BSC/clinical-nested-ner. [C] https://aclanthology.org/2022.louhi-1.2/ (PDF: https://aclanthology.org/2022.louhi-1.2.pdf)
  - [X] El paper reporta 7 tipos, mientras que Zenodo y Báez 2022 hablan de 10. Lo más probable es que Rojas haya excluido algunos tipos, pero el paper no dice cuáles. Hay que revisar `datasets/` del repo TeMU-BSC (GitHub bloquea WebFetch).

### Recomendación

- **Usar Zenodo v4 (5591011), `cwlc.zip` en IOB2 con train/dev/test.** El archivo es idéntico al de v3 y es la versión vigente cuando se escribieron Báez 2022 y Rojas 2022 (los dos con 5.000 derivaciones). Después de descargarlo, verificar que haya 15.290 / 1.911 / 1.912 oraciones y quedarse con los 7 tipos que usa Rojas. Si los conteos no calzan, pedir los splits a los autores o sacarlos del repo TeMU-BSC. [NC] (esto es una inferencia).
- **No usar v5 (9.000 derivaciones) para comparar** con esos dos papers, porque el corpus es distinto y no trae splits oficiales.
- **No usar HF `plncmm/wl` para comparar**: el NER es plano, tiene otro esquema de 11 tipos y se pierde el anidamiento. Sí sirve como baseline rápido de NER plano.
- Licencia: tratarla como **no comercial (CC BY-NC-SA 4.0)** por precaución, aunque HF diga CC BY 4.0. [X]

## 2. ¿Hay NER con LLM generativos sobre el CWLC (2023–2026)?

- **Naguib et al. 2024, EMNLP Findings**: el CWLC es uno de sus 14 corpus. Usaron la versión de 900 derivaciones y un split 80/10/10 propio. Las **100 oraciones son el tamaño few-shot de entrenamiento (k=100)**, no el del test. Mejor LLM: Llama-3-8B-Instruct, micro-F1 0,437. Mejor modelo enmascarado: BSC-BioEHR, 0,578. Entidades: el paper dice "10 tipos" pero enumera 12. [C] https://aclanthology.org/2024.findings-emnlp.400.pdf
- **Villena, Bravo-Marquez, Dunstan 2025, BMC MIDM 25:116**: hace clasificación de derivaciones (priorización y especialidad), con few-shot LLM. No es NER. [C] según PubMed, https://doi.org/10.1186/s12911-025-02948-2
- **llmNER (Villena, Miranda, Aracena 2024, preprint en arXiv)**: lo validan solo en CoNLL-2002/2003. No evalúa el CWLC. [C] https://arxiv.org/abs/2406.04528
- **Dunstan et al. 2024, BMC MIDM 24:204**: aplica un NER entrenado en derivaciones a narrativas de salud ocupacional. No usa LLM generativo. [C] según PubMed, https://doi.org/10.1186/s12911-024-02609-w
- Publicaciones 2023–2024 de Rojas y Villena en ClinicalNLP (codificación de derivaciones, corpus ocupacional con GPT-3.5 para PII): ninguna hace NER con LLM sobre el CWLC. [C] https://aclanthology.org/people/matias-rojas , https://aclanthology.org/people/fabian-villena/unverified/
- Pan et al. 2026 (CMC) compara prompting, QLoRA y encoders para NER en español, pero sobre MEDDOCAN, MEDDOPROF, MEDDOPLACE y SympTEMIST, sin el CWLC. [C] DOI 10.32604/cmc.2026.077501
- **Conclusión: no encontré ningún trabajo con prompting completo, RAG o LoRA sobre el CWLC aparte de Naguib 2024.** [NC] La ausencia no se puede probar. Busqué en PubMed (2 resultados), Consensus (2 consultas), web y las páginas ACL de los autores. Clinical-ShiftEval 2026 no lo verifiqué.

## 3. DisTEMIST

- Descarga en Zenodo: última versión 5.1, record 7614764 (DOI genérico 10.5281/zenodo.6408476), archivo `distemist_zenodo.zip` de 15,8 MB. [C] https://zenodo.org/records/7614764 , https://temu.bsc.es/distemist/
- Licencia **CC BY 4.0**. [C] (Zenodo 7614764)
- Tamaño: 1.000 casos clínicos y 10.665 menciones de enfermedad (con mapeo a SNOMED-CT). Train: 750 docs / 8.066 anotaciones. Test: 250 docs / 2.599 anotaciones. Incluye un background de 3.000 docs sin anotar y recursos multilingües. [C] https://ceur-ws.org/Vol-3180/paper-11.pdf
  - [X] Detalle menor: Zenodo menciona "584 in the case of subtrack2" para el test de linking.
- No hay split dev oficial (solo train/test). [C]
- Ganador de DisTEMIST-entities (BioASQ 2022): **PICUSLab, F1 0,7770** (P 0,7915 / R 0,7629). En linking ganó HPI-DHC con F1 0,5657. Participaron 9 equipos. [C] https://ceur-ws.org/Vol-3180/paper-11.pdf ; Moscato et al. 2022 (PICUSLab) dice ganar por alrededor de 3 puntos de F1.
- También está en BigBio: [C] https://huggingface.co/datasets/bigbio/distemist

## 4. Modelos en Hugging Face

| Modelo | Existe | Licencia | Notas | Estado |
|---|---|---|---|---|
| PlanTL-GOB-ES/bsc-bio-ehr-es | sí, sin gating | Apache-2.0 | La página no avisa de ningún traslado. BSC-NLP4BIA aloja **derivados** (p. ej. `bsc-bio-ehr-es-drugtemist`), no el modelo base renombrado. | [C] https://huggingface.co/PlanTL-GOB-ES/bsc-bio-ehr-es ; renombre [NC] |
| plncmm/roberta-clinical-wl-es | sí | Apache-2.0 | Fine-tune de PlanTL-GOB-ES/roberta-base-biomedical-clinical-es con el WL. | [C] https://huggingface.co/plncmm/roberta-clinical-wl-es |
| plncmm/beto-clinical-wl-es | sí | **sin etiqueta de licencia** | Base: dccuchile/bert-base-spanish-wwm-**uncased**. | [C] existe / [NC] licencia. https://huggingface.co/plncmm/beto-clinical-wl-es |
| dccuchile/bert-base-spanish-wwm-cased | sí | sin etiqueta. El card dice que "CC BY 4.0 best describes our intentions", con una advertencia sobre las licencias de los corpus de entrenamiento. | | [C] https://huggingface.co/dccuchile/bert-base-spanish-wwm-cased |
| IIC/RigoBERTa-Clinical | sí, **público y sin gating**; model.safetensors de 2,24 GB | `rigoclinical-nc` (no comercial, pensado para investigación) | | [C] https://huggingface.co/IIC/RigoBERTa-Clinical/tree/main |

## 5. Herramientas

- **mlx-lm**: soporta LoRA (por defecto), DoRA y full fine-tuning. Si `--model` apunta a un modelo cuantizado, entrena con QLoRA. Acepta datos `.jsonl` en formato chat, tools, completions o text. Corre en Apple Silicon. [C] https://github.com/ml-explore/mlx-lm/blob/main/mlx_lm/LORA.md , https://github.com/ml-explore/mlx-lm
  - Versión actual: **0.32.2 (16-10-2026)**. [C] https://pypi.org/project/mlx-lm/
- **Ollama**: tiene salida estructurada con `format: "json"` y con un JSON schema en `format`. También funciona por la API compatible con OpenAI (`response_format`). Ollama cloud no la soporta. [C] https://docs.ollama.com/capabilities/structured-outputs ; anuncio del 06-12-2024: https://ollama.com/blog/structured-outputs
  - Desde qué versión existe el JSON schema: aparentemente 0.5.0 (diciembre 2024). [NC] Ni la documentación ni el blog indican la versión.
  - Versión actual: **v0.40.11 (24-10-2026)**. [C] https://github.com/ollama/ollama/releases

## 6. GES classification dataset (Zenodo 4737751)

- v1 del 04-05-2021, CC BY 4.0, autores Villena y Dunstan (CMM, U. de Chile). Un solo archivo `ground_truth.csv` de 32,3 kB. [C] https://zenodo.org/records/4737751
- Columnas: `id, diagnostic, age, ges`. `ges` es booleano (True/False) y `diagnostic` es texto libre corto. [C]
- Filas: **941** (IDs del 1 al 941), conteo hecho por WebFetch. [C], pero conviene recontar localmente.
- Ojo: es un ground truth pequeño validado por 3 expertos, no el set de entrenamiento completo del clasificador (AUC 0,94).
