# ¿Lo que funciona afuera funciona en la APS chilena?

**Estudio de transferibilidad de estrategias de NER clínico, encoders y LLM generativos, sobre texto real de Atención Primaria chilena.**

Proyecto de investigación del curso *Inteligencia Artificial Generativa y Modelos Fundacionales* (prof. Rodrigo Salas, Doctorado en Ciencias e Ingeniería para la Salud, Universidad de Valparaíso), 2.º semestre 2026.

Equipo: Sebastián Inostroza, Maite Bahamondes, Ruth Vergara.

## Pregunta

La literatura internacional dice qué estrategias funcionan mejor para reconocer entidades clínicas (NER) en fichas. ¿Se mantiene ese resultado con las derivaciones reales escritas por médicos de APS en Chile, que vienen llenas de abreviaturas y siglas locales?

## Experimentos

| ID | Estrategia | Qué se compara |
|---|---|---|
| E1 | Encoder clínico ajustado (BERT/RoBERTa) | Línea base: lo que la literatura dice que gana |
| E2 | LLM local con prompt estructurado: zero-shot, few-shot fijo y few-shot dinámico (RAG) | Cuánto mejora un LLM al adaptarlo con ejemplos chilenos |
| E4 | LLM como anotador → entrena un encoder (+10/50/100 documentos gold) | Cuánta anotación humana se necesita realmente |
| E3 (opc.) | QLoRA de un LLM de 7–8B con MLX | Ajuste fino del propio LLM |
| E5 (opc.) | Normalización de abreviaturas con LLM antes de extraer | Preprocesamiento |

Un LLM comercial se usa solo como **techo de referencia**: el corpus es público y anonimizado.

**Examen:** test del Chilean Waiting List Corpus (CWLC), anotado por médicos. **No se requiere anotación humana nueva.**

**Métricas:** F1 estricto y laxo (micro y por entidad) con IC 95% por bootstrap; F1 en entidades abreviadas vs no abreviadas; tasa de alucinación; salidas mal formadas; reproducibilidad (3–5 corridas); costo, tiempo y memoria. El reporte sigue TRIPOD-LLM.

## Estructura

```
configs/      datos.yaml, experimentos.yaml
data/         raw/ y processed/ (NO se versionan; ver data/README.md)
docs/         bitácora, propuesta, mapa guía, revisión de literatura
notebooks/    exploración y figuras
results/      tablas y figuras finales (sin datos de pacientes)
scripts/      instalación del entorno
src/datos/    descarga y preprocesamiento
src/modelos/  E1–E5
src/evaluacion/ métricas (estricto/laxo, bootstrap, alucinaciones)
src/reproducibilidad.py  semillas deterministas, huellas SHA-256, media ± DE entre semillas
src/datos/auditoria.py   fuga de datos y calidad del corpus
configs/huellas_datos.json  huellas esperadas de los archivos del corpus
tests/        pruebas de métricas, lector, auditoría y reproducibilidad
```

## Instalación (Mac con Apple Silicon)

```bash
git clone https://github.com/SebasDCIS/proyecto-ner-aps-genai.git
cd proyecto-ner-aps-genai
bash scripts/setup_mac.sh          # crea .venv, instala dependencias y descarga los LLM locales
source .venv/bin/activate
python src/datos/descargar.py      # descarga los corpus a data/raw/
python -m pytest -q tests          # verifica las métricas
```

### Trabajar en VS Code

1. Abrir la carpeta del proyecto en VS Code (*File → Open Folder*). VS Code sugerirá instalar las extensiones recomendadas (Python y Jupyter): aceptar.
2. Abrir un notebook de `notebooks/` y elegir el kernel **.venv** (arriba a la derecha).
3. Los notebooks van en orden y cada paso está explicado para alguien externo al proyecto:

| Notebook | Qué hace |
|---|---|
| `00_preparacion_entorno_y_datos.ipynb` | Verifica el entorno, la GPU del Mac (MPS), Ollama; descarga y valida el corpus |
| `01_exploracion_cwlc.ipynb` | Conoce el corpus: tamaños, tipos de entidad, abreviaturas, enfermedades abreviadas |
| `01b_auditoria_fuga_y_calidad.ipynb` | Fuga de datos (duplicados, menciones vistas, contaminación), errores de datos y prueba de reproducibilidad |
| `02_e1_encoder_ajustado.ipynb` | Línea base E1 con 3 semillas (media ± DE), F1 sin duplicados y recall en menciones vistas vs nuevas |
| `03_e2_llm_prompting.ipynb` | E2: LLM local (Ollama) con guía de anotación; zero-shot, few-shot fijo (3 semillas) y dinámico (BM25); alucinaciones y comparación con E1 en las mismas oraciones |
| `04_e4_llm_anotador.ipynb` | E4: el LLM anota 2.000 oraciones (silver) y se entrena un encoder con silver + 0/10/50/100 oraciones gold simuladas; curva frente a E1 y E2 |

**Reproducibilidad:** cada experimento entrenable se corre con las semillas 42, 43 y 44 y se reporta media ± DE. Cada JSON de `results/` guarda su huella (datos, config, commit, revisión del modelo en Hugging Face, entorno), y los notebooks verifican que el corpus coincida con `configs/huellas_datos.json` antes de entrenar.

Antes de hacer *commit*, limpiar las salidas de los notebooks (*Clear All Outputs*) para no subir fragmentos del corpus.

Repositorio local recomendado: `~/Proyectos/proyecto-ner-aps-genai`, fuera de carpetas sincronizadas con la nube. Los datos y los pesos de modelos no se suben a git.

## Datos y licencias

- **CWLC**: CC BY-NC-SA 4.0. Uso académico. Los derivados que se redistribuyan mantienen la licencia.
- **DisTEMIST**: ver `configs/datos.yaml`.
- Ningún dato de pacientes identificables. El proyecto no usa datos institucionales.

## Documentos

- [Bitácora](docs/bitacora.md)
- [Mapa guía del equipo](docs/mapa_guia.md)
- [Propuesta para el profesor](docs/propuesta.md)
- [Revisión de literatura](docs/revision_literatura.md)
