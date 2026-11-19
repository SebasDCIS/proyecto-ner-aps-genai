# Tecnologías, herramientas y terminología del proyecto (proyecto cerrado, noviembre de 2026)

Este documento describe, una por una, las tecnologías y herramientas que se usaron en el proyecto "Evaluación comparativa de encoders ajustados y modelos de lenguaje generativos para el reconocimiento de entidades clínicas de atención primaria chilena", y para qué sirvió cada una. Complementa al manuscrito final y a la guía de estudio desde cero.

## Lenguaje y entorno de trabajo

Python 3.13 es el lenguaje de todo el código. El proyecto se organizó como un repositorio en GitHub (SebasDCIS/proyecto-ner-aps-genai), con git para el control de versiones: cada resultado guarda el identificador del commit con que se produjo. El código está en la carpeta src, los experimentos se corrieron en notebooks de Jupyter (archivos .ipynb, abiertos en VS Code) y los análisis finales en scripts de Python. Las configuraciones de cada experimento están en archivos YAML en la carpeta configs. Las claves de las API se guardan solo en un archivo .env que no se sube al repositorio, y el corpus y los pesos de los modelos tampoco se suben.

Los notebooks siguen el orden del trabajo: 00 prepara el entorno y los datos, 01 explora el corpus, 01b audita fugas y calidad, 02 entrena los encoders (02b y 02c son las versiones para RigoBERTa en el Mac y en Colab), 03 corre los LLM locales, 03b los LLM comerciales, 04 la destilación y 05 el análisis de errores.

## Hardware

Los encoders base y los LLM locales corrieron en un Mac con chip M5 y 24 GB de memoria unificada. En los Mac con chip Apple, PyTorch usa la GPU a través de MPS (Metal Performance Shaders). RigoBERTa Clinical, un modelo large de unos 560 millones de parámetros, no cupo en esa memoria: el sistema empezó a usar el disco como memoria (swap) y cada época pasaba de dos horas. Se entrenó en Google Colab, primero en una GPU T4 de 16 GB, que se quedó sin memoria, y finalmente en una GPU A100 de 80 GB con unidades de cómputo de Google AI Pro. Ahí cada modelo tardó unos 11 minutos con lote de 16. Para pruebas intermedias se usó la variable PYTORCH_CUDA_ALLOC_CONF con expandable_segments, que reduce la fragmentación de memoria en GPU NVIDIA.

## Bibliotecas para los encoders

PyTorch (torch) es la biblioteca de aprendizaje profundo que hace los cálculos de las redes neuronales y su entrenamiento. Hugging Face Transformers carga los modelos preentrenados y sus tokenizadores (AutoTokenizer, AutoModelForTokenClassification) y entrega el calendario de tasa de aprendizaje con calentamiento lineal (get_linear_schedule_with_warmup). Hugging Face Hub es el repositorio en línea desde donde se descargaron los tres encoders, y cada resultado guarda la revisión exacta del modelo descargado. Las bibliotecas datasets y accelerate, del mismo ecosistema, quedaron instaladas como dependencias de apoyo. seqeval es la referencia estándar para calcular métricas de NER sobre etiquetas BIO; el proyecto implementó además su propio cálculo por spans en src/evaluacion/metricas.py, para medir F1 estricto y laxo con entidades superpuestas.

Los tres encoders fueron bsc-bio-ehr-es (PlanTL/BSC, RoBERTa clínico español de unos 125 millones de parámetros), roberta-clinical-wl-es (PLN@CMM, el mismo modelo con preentrenamiento continuo en derivaciones chilenas de lista de espera) y RigoBERTa Clinical (IIC, XLM-RoBERTa large preentrenado con el corpus ClinText-SP).

El entrenamiento usó el optimizador AdamW, tasa de aprendizaje 3×10⁻⁵ (2×10⁻⁵ para RigoBERTa), lote de 16, hasta cinco épocas, calentamiento del 10 %, detención temprana con paciencia 2 y tres semillas (42, 43 y 44). La acumulación de gradientes, que se agregó al código para el Mac, procesa lotes más chicos y corrige los pesos cada cierto número de lotes, simulando un lote mayor con menos memoria.

## Herramientas para los LLM

Ollama es un programa que descarga y corre LLM dentro del propio computador, sin enviar datos afuera. Con Ollama se corrieron Llama 3.1 de 8B (Meta) y Qwen 2.5 de 7B (Alibaba), ambos cuantizados, es decir, con sus parámetros guardados en menor precisión para que quepan en memoria. Ollama guarda un digest (huella) de cada modelo, que también quedó registrado.

Para los LLM comerciales se usó la biblioteca openai de Python. GPT-5.2 se llamó por la API de OpenAI, con esfuerzo de razonamiento bajo y sin temperatura, porque la API no acepta ese parámetro. Gemini 3.1 Pro (versión preliminar gemini-3.1-pro-preview) se llamó a través del punto de acceso compatible con OpenAI que ofrece la API de Gemini de Google. Gemini tiene un límite de 250 consultas diarias, así que se programó una tarea diaria en el Mac (scripts/instalar_tarea_diaria.sh y scripts/correr_nube.py) que avanzaba oración por oración, guardaba cada respuesta al llegar y retomaba al día siguiente. El costo total fue 4,26 dólares con GPT-5.2 y 4,46 con Gemini para las 990 oraciones con dos estrategias.

Las salidas de los LLM se piden en JSON con un esquema fijo de pares {tipo, texto}. Un localizador escrito en el proyecto busca cada texto dentro de la oración y lo convierte en posiciones; lo que no aparece se cuenta como alucinación.

rank-bm25 implementa BM25, el buscador por palabras compartidas que eligió los cinco ejemplos más parecidos para el few-shot dinámico.

## Análisis, estadística y figuras

NumPy y SciPy hacen los cálculos numéricos. pandas maneja tablas de resultados. El bootstrap y el bootstrap pareado se implementaron en el proyecto, con 1.000 remuestreos por oración. pyspellchecker, un corrector ortográfico con diccionario de español, ayudó a detectar palabras mal escritas en el análisis de errores, junto con la distancia de edición; la lista final se revisó a mano. matplotlib generó todas las figuras del manuscrito. pytest corre las pruebas automáticas del código (métricas, lectura del corpus, LLM, destilación, análisis y reproducibilidad).

## Reproducibilidad

Cada resultado guarda la huella SHA-256 de los 21 archivos del corpus, de la configuración, del código y de las predicciones. Una huella SHA-256 es un código de 64 caracteres que identifica un archivo: si cambia un solo byte, cambia la huella. Cada notebook verifica la huella de los datos antes de entrenar, lo que permitió comprobar que Colab y el Mac usaron exactamente los mismos datos. El script scripts/comparaciones_pareadas.py regenera todas las comparaciones desde las predicciones guardadas, sin volver a entrenar ni a pagar API. El reporte sigue la guía TRIPOD-LLM, una lista de lo que debe informar un estudio que evalúa LLM en salud.

## Metodología general

El trabajo siguió las etapas del proceso KDD (Knowledge Discovery in Databases): selección del corpus y de las entidades, preprocesamiento y auditoría, transformación al formato de cada modelo (etiquetas BIO para encoders, prompt y JSON para LLM), modelado (E1, E2, E2 nube, E4 y votación) y evaluación (F1 estricto y laxo, intervalos bootstrap, regla de las tres semillas y recall por subgrupo).

## Documentos y entrega

El manuscrito final se escribió en el formato Word entregado por el profesor del curso (plantilla de dos columnas con logo de la Universidad de Valparaíso), generado con la biblioteca python-docx a partir de la plantilla, y convertido a PDF con LibreOffice. Tiene 9 páginas y 34 referencias. La presentación de 17 diapositivas se generó con pptxgenjs. El material de estudio se compartió por Google Drive y este cuaderno de NotebookLM.
