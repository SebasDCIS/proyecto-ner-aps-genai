# Mapa guía del proyecto

Para Maite y Ruth: qué haremos, para qué, cómo, cuándo y quién hace qué.

## Qué haremos (en una frase)

Vamos a probar, con derivaciones reales escritas en la APS chilena, las estrategias de IA que la literatura dice que funcionan mejor para "leer" fichas clínicas. Así sabremos si lo que funciona en otros países también funciona aquí.

## Para qué

- **Para el ramo:** un manuscrito con estado del arte, metodología y resultados (40% de la nota). Usa casi todas las unidades: Transformers, transfer learning, LLM, RAG, LoRA y métricas.
- **Para la salud pública:** ya hay IA generativa entrando a los CESFAM sin métricas públicas, y la nueva ley de datos (diciembre 2026) obliga a usar modelos locales. Vamos a mostrar qué estrategia local funciona y cuánta anotación necesita.
- **Para la tesis de Sebastián:** le dice qué estrategia usar más adelante con los planes consensuados ECICEP.

## La tarea: NER, explicado en 10 segundos

El NER (reconocimiento de entidades) consiste en que el modelo **subraye en el texto las cosas importantes y diga qué son**:

> "pcte c/ **DM2** [enfermedad] en tto c/ **metformina** [fármaco]"

Lo comparamos con lo que subrayaron médicos de verdad y calculamos cuánto coincide (**F1**, de 0 a 1).

**No tenemos que etiquetar nada**: el corpus ya viene subrayado por médicos.

## Los datos

**Chilean Waiting List Corpus (CWLC):** miles de derivaciones a especialista escritas por médicos de APS, públicas y anonimizadas, con enfermedades, fármacos, abreviaturas, etc. ya marcadas.

## Cómo: los 3 experimentos principales

| | Qué es | Analogía |
|---|---|---|
| **E1** | Un BERT clínico **entrenado** con derivaciones chilenas | El especialista formado para esta tarea. La literatura dice que gana |
| **E2** | Un LLM local (tipo ChatGPT, pero en el computador) al que **solo le damos instrucciones**: sin ejemplos, con ejemplos fijos o con los ejemplos más parecidos a cada texto (RAG) | El interno brillante al que le explicas la tarea y le muestras casos parecidos |
| **E4** | El LLM **etiqueta solo** muchas derivaciones, y con eso entrenamos un BERT, agregando 0, 10, 50 o 100 derivaciones bien etiquetadas | El interno pre-informa y el especialista aprende de eso más unos pocos casos revisados |

Opcionales, si hay tiempo: **E3** (ajustar el LLM con LoRA) y **E5** (que un LLM expanda las abreviaturas antes de extraer).

Un LLM comercial (tipo GPT) se usa solo como **techo de comparación**.

## Qué mediremos

- **F1:** cuánto coincide cada modelo con los médicos, en modo estricto (exacto) y laxo (parecido).
- **F1 en palabras abreviadas** ("DM2") frente a escritas completas ("diabetes mellitus tipo 2"). Esto nadie lo ha medido.
- **Inventos:** enfermedades que el LLM nombra y que no están en el texto.
- **Costo y tiempo,** y si los datos salen o no del computador.

## Cuándo

| Semana | Fechas | Qué | Entregable |
|---|---|---|---|
| 1 | 26 oct – 1 nov | Propuesta a Salas, entorno, datos, splits | Tema aprobado; datos listos |
| 2 | 2 – 8 nov | E1: entrenar los BERT | Tabla de línea base |
| 3 | 9 – 15 nov | E2: prompts sin ejemplos y con ejemplos fijos | Resultados E2 parte 1 |
| 4 | 16 – 22 nov | E2: RAG y LLM comercial | Resultados E2 completos |
| 5 | 23 – 29 nov | E4: LLM anotador + curva de gold | Resultados E4 |
| 6 | 30 nov – 6 dic | Análisis, figuras, errores | Tablas y figuras finales |
| 7 | 7 – 13 dic | Escribir el manuscrito y la presentación | Manuscrito y presentación |

La fecha exacta de entrega está por confirmar con Salas.

## Quién (propuesta, la conversamos)

| Persona | Foco principal | También |
|---|---|---|
| **Sebastián** | E1 y E4 (entrenamientos en su Mac), coordinación y repositorio | Metodología del manuscrito |
| **Maite** | E2: diseño de prompts, RAG y LLM comercial | Sección de resultados de LLM |
| **Ruth** | Datos y evaluación: explorar el CWLC, contar abreviaturas, correr las métricas, figuras | Estado del arte |

Todos: revisar la redacción final y preparar la presentación.

## Herramientas

- **GitHub:** repositorio `proyecto-ner-aps-genai`. Ahí está todo: código, bitácora y documentos.
- **Python:** `transformers` (BERT), `ollama` (LLM locales) y un script de métricas ya probado.
- **Mac de Sebastián:** entrenamientos y LLM locales. **Colab** como alternativa si alguien quiere correr cosas por su cuenta.
- **Bitácora** (`docs/bitacora.md`): cada decisión con fecha.

## Reglas del equipo

1. El **test no se toca** hasta el final: los ejemplos para los prompts salen solo del entrenamiento.
2. **No se suben datos** al repositorio (ya está configurado).
3. Cada experimento queda con su configuración y semilla, para poder repetirlo.
4. Toda decisión importante va a la bitácora.

## Para profundizar

- `docs/propuesta.md`: la propuesta formal para Salas.
- `docs/revision_literatura.md`: la revisión de literatura completa.
- Guía NLP desde cero con audios (NotebookLM): la comparte Sebastián.
