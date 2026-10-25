# Bitácora del proyecto

Registro de decisiones, avances y pendientes. Cada entrada responde tres preguntas: qué se decidió, por qué y qué queda abierto. La más reciente va primero.

---

## 2026-10-25 (noche) · E2 preparado

- `src/modelos/e2_llm.py` + notebook `03`: LLM local vía Ollama (`llama3.1:8b`, `qwen2.5:7b`) con guía de anotación redactada solo desde train, salida JSON restringida a un esquema, temperatura 0 y semilla fija. Estrategias: zero-shot, few-shot fijo (k = 5; 3 semillas = 3 sets de ejemplos) y few-shot dinámico (5 ejemplos de train más parecidos por BM25).
- Las menciones devueltas se ubican en la oración prefiriendo palabras completas ("DM" no cae dentro de "DM2") y por tipo (permite anidamiento). Control: con respuestas perfectas el F1 tras la lectura es 0,999 / 1,000 / 0,995 (Disease / Medication / Abbreviation): la lectura casi no pierde nada.
- **Fuga propia del few-shot dinámico:** en el 8,3% del test el ejemplo recuperado más parecido es la misma oración (duplicado en train). Se reporta el F1 sin duplicados como métrica clave de E2.
- Se evalúa con las mismas funciones que E1 y se compara con E1 sobre las mismas oraciones. Huella: digest del modelo en Ollama, hash de la guía y de las oraciones evaluadas.
- Modo rápido: 100 oraciones del test al azar (semilla 42); en ese subconjunto hay pocos fármacos, así que su F1 es solo orientativo.

**Pendientes**
- [ ] Correr el notebook 03 en modo rápido en el Mac y estimar el tiempo del modo completo

---

## 2026-10-25 (tarde) · Resultados de E1: 18 entrenamientos

Corrida completa en el Mac (MPS), de 11:07 a ~15:25, unos 15 min por entrenamiento. Código en `20f9730`, datos verificados por huella (`a507e8d9…`), `max_len` 512, revisiones exactas de los modelos guardadas en cada JSON.

**F1 estricto en test, media ± DE de 3 semillas**

| Entidad | Español (bsc-bio-ehr-es) | Chileno (roberta-clinical-wl-es) | Báez 2020 (piloto) |
|---|---|---|---|
| Abbreviation | 0,950 ± 0,004 | 0,952 ± 0,002 | 0,92 |
| Disease | 0,798 ± 0,006 | 0,815 ± 0,010 | 0,77 |
| Medication | 0,840 ± 0,012 | 0,794 ± 0,046 | 0,75 |

**Hallazgos**
- Sin las oraciones duplicadas, el F1 baja ≤ 0,007: la fuga detectada en la auditoría no infla los resultados.
- Chileno vs español (bootstrap pareado por semilla): en Disease el chileno gana +2,6 y +2,4 puntos (significativo en 2 de 3 semillas; +0,2 en la tercera). En Abbreviation no hay diferencia. En Medication el español gana, pero solo es significativo en la semilla 42, donde el chileno tuvo una corrida inestable (F1 0,741). Con la regla fijada de antemano (afirmar solo si se repite en las 3 semillas), **ninguna diferencia es robusta**; Disease es una tendencia consistente a favor del chileno.
- **Enfermedades abreviadas (H3):** el español rinde peor en ellas (recall 0,790 vs 0,816 en no abreviadas); el chileno no muestra brecha (0,843 vs 0,835) y supera al español en abreviadas por 5,3 puntos (n = 119). Es la señal más clara a favor de la adaptación local, con la cautela de la contaminación posible.
- **Generalización:** el recall cae mucho en menciones que no aparecen en train. Disease: 0,88–0,90 vistas vs 0,70–0,73 nuevas; Abbreviation: 0,97–0,98 vs ~0,60 (n = 66). El alto F1 en abreviaturas es en buena parte memoria.
- F1 laxo ≈ 0,90 en Disease vs 0,80 estricto: ~10 puntos son errores de límites.
- Variación entre semillas: ~0,5–1 punto en Disease y Abbreviation, hasta 4,6 en Medication (solo 92 entidades en test; IC95 de ±7 puntos).
- Con la misma semilla 42, Disease del modelo español dio F1 dev 0,744 en la primera época en esta corrida y 0,755 en el intento anterior (código viejo en memoria + MPS no determinista): diferencias de ~1 punto, del orden de la DE entre semillas.
- En varias corridas el mejor F1 en dev fue en la época 5: podría ganar algo con más épocas (no se cambia para no tocar la configuración ya fijada).
- La huella marcó "cambios sin commit" en todas las corridas porque los notebooks tenían salidas; se corrigió `huella_codigo` para ignorar `.ipynb`.

**Pendientes**
- [ ] Subir `results/e1_completo/*.json` desde el Mac
- [ ] Completar las conclusiones del notebook 02
- [ ] E2: LLM local con prompting

---

## 2026-10-25 (cierre) · Auditoría de fuga y reproducibilidad

**Hallazgos** (notebook `01b`, resultados en `results/auditoria_datos.json`)
- **Oraciones repetidas** (texto normalizado): el 9,7% de las oraciones del test (96) está también en train, pero solo afectan al 2,7% de las entidades del test; con ≥ 5 palabras baja a 3,5%. Son sobre todo plantillas ("se deriva para evaluación y manejo") y descripciones CIE-10. train∩dev 10,5%; dev∩test 4,4%.
- **Casi duplicados** (Jaccard de trigramas ≥ 0,8): 2,9% del test.
- **Anotación inconsistente:** 42 textos idénticos anotados distinto (22 cruzan splits). Es ruido de etiquetas y pone techo al F1.
- **Menciones del test ya vistas en train:** Disease 61%, Medication 62%, Abbreviation 93%.
- **Partición original secuencial** (81/9/10 por oración): como máximo ~2 derivaciones quedan partidas entre splits. Riesgo mínimo.
- **Contaminación posible:** `plncmm/roberta-clinical-wl-es` se preentrenó con derivaciones chilenas sin detalle de cuáles; pudo leer el texto del test. Los LLM pudieron ver el CWLC público.
- **Calidad:** 8 etiquetas I- huérfanas, sin problemas de Unicode, 9 oraciones de train truncadas a 256 subpalabras y ninguna a 512.

**Decisiones**
- Se mantienen los splits oficiales (comparables con Báez 2022) y se agregan dos análisis de sensibilidad: F1 en el test sin oraciones repetidas en train y recall en menciones vistas vs nuevas.
- `max_len` = 512.
- **3 semillas (42, 43, 44)** por cada experimento entrenable, reportando media ± DE; las comparaciones entre modelos se hacen con bootstrap pareado por semilla y solo se afirman si se repiten en las 3. Motivo: la semilla cambia el resultado del ajuste fino (Dodge 2020; Mosbach 2021) y pocos trabajos reportan varias corridas.
- **Huellas digitales:** `configs/huellas_datos.json` guarda el SHA-256 de los 21 archivos del CWLC, y cada notebook lo verifica antes de entrenar. Cada resultado guarda la huella de datos, config, commit, revisión del modelo en HF, entorno y predicciones.
- Determinismo comprobado en CPU: misma semilla, misma pérdida y mismas predicciones bit a bit; otra semilla, otras. En MPS puede haber diferencias mínimas.

**Pendientes**
- [ ] Correr `01b` y luego `02` en modo completo en el Mac (2 modelos × 3 entidades × 3 semillas = 18 entrenamientos)
- [ ] Declarar la contaminación posible y el ruido de etiquetas en las limitaciones del manuscrito

---

## 2026-10-25 (noche) · E1 implementado y probado

- Módulo `src/modelos/e1_encoder.py`: un etiquetador por tipo de entidad (MLC), ciclo de entrenamiento PyTorch explícito, early stopping por F1 en dev.
- **Prueba de humo** (CPU, solo 800 oraciones de train y 3 épocas, `bsc-bio-ehr-es`, Disease, 300 oraciones de test): F1 estricto **0,747** (IC95 0,696–0,784), F1 laxo **0,881**. Recall en enfermedades abreviadas 0,72 vs no abreviadas 0,76 (n = 47 vs 285). El pipeline aprende; el modo completo se corre en el Mac con MPS.
- La gran diferencia entre F1 laxo y estricto (≈ 0,13) indica que muchos errores son de límites de la entidad, no de no reconocerla.
- `plncmm/roberta-clinical-wl-es` usa el mismo tokenizador que el modelo del BSC ("pcte" → "pc" + "te").

**Pendientes**
- [ ] Correr el notebook 02 en modo completo en el Mac y completar sus conclusiones

---

## 2026-10-25 (tarde) · Datos descargados y primeros notebooks

**Decisiones**
- Fuente del CWLC: los archivos CoNLL que publicó PLN@CMM con Báez et al. 2022 (GitHub `plncmm/acm_health_msen`, `src/wl_files`). Son 7 tipos de entidad (Abbreviation, Body_Part, Disease, Family_Member, Finding, Medication, Procedure), un archivo por tipo, con splits fijos de **8.014 / 890 / 990 oraciones**. Zenodo queda como respaldo.
- Se trabaja en **VS Code con notebooks** (`notebooks/`), cada uno explicado para un lector externo.

**Hallazgos de la exploración (notebook 01)**
- Entrenamiento: 35.480 entidades; test: 4.289 (1.071 enfermedades).
- 1.113 abreviaturas distintas; las más frecuentes son aps, tto, hta, pza, obs, pcte, rx y dm2.
- El 11,1% de las enfermedades del test (119) se superpone con una abreviatura anotada. Alcanza para H3, con IC más anchos.
- Oraciones cortas: mediana de 15 palabras.

**Pendientes**
- [ ] Comparar con Báez 2022, que usa estos mismos splits, no con Rojas 2022 (otra partición)
- [ ] Notebook 02: línea base E1

---

## 2026-10-25 · Arranque del proyecto

**Decisiones**
- Tema definitivo: **estudio de transferibilidad**. Se implementan con texto real de APS chilena (CWLC) las estrategias que la literatura internacional reporta como mejores para NER clínico, y se mide si sus resultados se mantienen.
- Alcance base: **E1** (encoder ajustado), **E2** (LLM local con zero-shot, few-shot fijo y few-shot dinámico/RAG) y **E4** (LLM como anotador + 10/50/100 documentos gold simulados). Opcionales: E3 (QLoRA) y E5 (normalización).
- Un LLM comercial solo como techo de referencia, porque el CWLC es público y anonimizado.
- **Sin anotación humana nueva**: el gold standard es el del CWLC, anotado por médicos y dentistas.
- Repositorio: `SebasDCIS/proyecto-ner-aps-genai`. Datos y pesos fuera de git.

**Por qué**
- La revisión de literatura (`docs/revision_literatura.md`) muestra que en español los encoders ajustados superan a los LLM con prompting en 3–15 puntos de F1. El prompting estructurado y el few-shot dinámico achican la brecha. Nadie lo ha probado con texto de APS chilena.
- Un LLM grande probablemente "entiende" abreviaturas, pero en un CESFAM habrá que usar modelos locales (Ley 21.719). La pregunta útil es qué estrategia local funciona y cuánta anotación necesita.

**Pendientes**
- [ ] Validar el tema con el prof. Salas (propuesta en `docs/propuesta.md`)
- [ ] Presentar el mapa guía a Maite y Ruth (`docs/mapa_guia.md`) y acordar roles
- [x] Versión del CWLC: **v4 (Zenodo 5591011)**, IOB2 con train/dev/test; comparable con Báez 2022 y Rojas 2022 (ver `docs/verificacion_arranque.md`)
- [ ] Confirmar los 7 tipos de entidad que usó Rojas 2022 (F1 83,16) para comparar en igualdad
- [x] DisTEMIST v5.1 (Zenodo 7614764, CC BY 4.0) como contraste
- [x] Verificado: no hay trabajos publicados de NER con LLM generativos sobre el CWLC, salvo Naguib 2024 (few-shot, 100 oraciones; Llama-3-8B 0,437 vs BSC-BioEHR 0,578)
- [ ] Confirmar la fecha de entrega del manuscrito

---

## 2026-10-24 · Descarte de diseños con validación humana

- Se descartó el diseño del "generador de ruido CESFAM", porque requería revisión humana del texto generado.
- Se evaluaron alternativas sin validación humana: datos sintéticos para entrenar, normalización inversa y auditoría de LLM.
- Contexto revisado: en Chile ya hay IA generativa en APS (EMILIA, de Rayen Salud: resúmenes de ficha) sin métricas públicas, y en octubre de 2026 se lanzó el Sandbox Nacional de IA en Salud. Refuerza el valor de evaluar con evidencia local.

## 2026-10-21 · Recursos y estado del arte inicial

- Se identificaron los recursos chilenos: CWLC (derivaciones escritas por médicos de APS), dataset GES, corpus ACHS, embeddings y modelos de PLN@CMM.
- No existe un corpus público de evoluciones de CESFAM ni de planes consensuados: es una limitación declarada y el vacío que justifica la tesis.
- Se preparó la guía de estudio NLP desde cero (9 módulos más audios en NotebookLM).

## 2026-10-20 · Definición del tema

- Se buscó un proyecto del ramo vinculado a la tesis (NLP en APS, seguimiento del plan consensuado ECICEP).
