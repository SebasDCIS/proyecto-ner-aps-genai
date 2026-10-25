# Propuesta de proyecto de investigación

**Curso:** Inteligencia Artificial Generativa y Modelos Fundacionales — Prof. Dr. Ing. Rodrigo Salas
**Equipo:** Sebastián Inostroza, Maite Bahamondes, Ruth Vergara
**Fecha:** octubre de 2026

## Título

¿Lo que funciona afuera funciona en la APS chilena? Transferibilidad de estrategias de reconocimiento de entidades clínicas con encoders y LLM generativos sobre derivaciones reales de Atención Primaria.

## Problema y justificación

Gran parte de la información clínica de la Atención Primaria está en texto libre, escrito con abreviaturas, siglas locales y estilo telegráfico ("pcte c/ DM2 desc, s/ ctrl hace 6m"). La literatura internacional reporta qué estrategias funcionan mejor para reconocer entidades clínicas (NER):

- encoders ajustados (BERT/RoBERTa);
- LLM con prompts estructurados;
- selección dinámica de ejemplos (RAG);
- ajuste fino con LoRA;
- LLM como anotador para entrenar modelos pequeños.

En español, los encoders ajustados superan a los LLM con prompting por 3 a 15 puntos de F1. Sin embargo, esa evidencia viene casi siempre de casos clínicos publicados en España o de notas en inglés. **Nadie ha comparado estas estrategias con texto real de la APS chilena.** No hay NER con LLM ajustados sobre el Chilean Waiting List Corpus, ni comparación entre LLM locales y comerciales en texto clínico chileno, ni métricas separadas para entidades abreviadas.

Además, ya hay IA generativa entrando en la APS chilena a través de proveedores de ficha electrónica, sin métricas públicas. La Ley 21.719 (vigente desde el 1 de diciembre de 2026) restringe el envío de datos de salud a servicios externos. Saber **qué estrategia local funciona y cuánta anotación necesita** tiene valor práctico inmediato.

## Pregunta e hipótesis

**Pregunta:** ¿Se mantiene, con derivaciones reales de APS chilena, el desempeño relativo que la literatura reporta para las principales estrategias de NER clínico, y cuánto de la capacidad de un encoder ajustado se recupera con LLM locales y poca anotación?

- **H1.** El encoder clínico ajustado obtiene el mayor F1 estricto, igual que en la literatura.
- **H2.** El few-shot dinámico (RAG con ejemplos chilenos) reduce la brecha del LLM respecto del zero-shot y del few-shot fijo.
- **H3.** La brecha entre LLM y encoder es mayor en las entidades abreviadas que en las escritas completas.
- **H4.** Un encoder entrenado con etiquetas generadas por un LLM, más 50 documentos gold, queda a pocos puntos del encoder entrenado con todo el gold.

## Datos

- **Chilean Waiting List Corpus (CWLC):** derivaciones de APS desidentificadas, anotadas por médicos y dentistas. Incluye enfermedades, fármacos, abreviaturas y otras entidades. Licencia CC BY-NC-SA 4.0.
- **No se requiere anotación humana nueva:** el gold standard del CWLC es la referencia. El escenario "con poca anotación" (H4) se **simula** ocultando etiquetas existentes.
- No se usan datos institucionales ni de pacientes identificables.

## Métodos

| Experimento | Estrategia | Detalle |
|---|---|---|
| E1 | Encoder ajustado (línea base) | RoBERTa clínico español (BSC) y RoBERTa adaptado a derivaciones chilenas (PLN@CMM), ajustados para NER |
| E2 | LLM local con prompt estructurado | LLM de 7–8B cuantizados (Llama, Qwen): zero-shot → few-shot fijo → few-shot dinámico por similitud (RAG). Un LLM comercial como techo de referencia |
| E4 | LLM como anotador + destilación | El LLM etiqueta parte del entrenamiento; se entrena un encoder con esas etiquetas y con 0/10/50/100 documentos gold |
| E3, E5 (opcionales) | QLoRA de un LLM de 7–8B; normalización de abreviaturas antes de extraer | Según tiempo disponible |

**Métricas:**
- F1 estricto y laxo, micro y por entidad, con IC 95% por bootstrap y comparación pareada entre sistemas.
- F1 en entidades abreviadas frente a no abreviadas.
- Tasa de alucinación y de salidas mal formadas.
- Reproducibilidad entre corridas.
- Costo, tiempo y memoria.

**Reporte:** se sigue la guía TRIPOD-LLM. Todo corre localmente en un Mac M5 (24 GB), salvo la referencia comercial.

## Relación con las unidades del curso

| Unidad del programa | Dónde aparece en el proyecto |
|---|---|
| U1 · IA generativa y modelos fundacionales (IA predictiva vs generativa; GPT, LLaMA) | Comparación central: encoder predictivo (BERT) frente a LLM generativos (Llama, Qwen, GPT) |
| U2 · Redes neuronales (pérdida, optimización, regularización, PyTorch) | Ajuste del cabezal de clasificación del encoder con AdamW, early stopping y regularización, en PyTorch |
| U3 · Deep learning y transfer learning | E1 es transfer learning: modelos preentrenados ajustados a NER clínico |
| U4 · Transformers, atención encoder-decoder, modelos híbridos, métricas | Todos los modelos son Transformers (encoder vs decoder). E4 es un sistema híbrido LLM + encoder. Evaluación con F1 estricto/laxo y bootstrap |
| U5 · Explicabilidad | Análisis de errores interpretable: dónde fallan los modelos (abreviaturas, límites, alucinaciones) |
| U7 · Aprendizaje auto-supervisado | Preentrenamiento por lenguaje enmascarado de los encoders y efecto de la adaptación de dominio a texto chileno (encoder español vs chileno) |
| U8 · IA generativa | LLM como generadores: salidas estructuradas y generación de etiquetas sintéticas ("silver") para entrenar otro modelo (E4) |
| U9 · Adaptación de modelos fundacionales: fine-tuning, LoRA, RAG | Núcleo del proyecto: prompting, few-shot dinámico tipo RAG (E2), LoRA/QLoRA (E3) y destilación (E4) |

Competencias del perfil de egreso:
- **CE1 y CE3:** investigación aplicada en una línea definida.
- **CG3:** solución a una necesidad del sector público de salud.
- **CG5:** ética, privacidad y uso responsable de IA con datos de salud.

## Cronograma (fecha de entrega por confirmar)

| Semana | Actividad |
|---|---|
| 1 (26 oct – 1 nov) | Validación del tema, entorno, descarga de datos, versión y splits del CWLC |
| 2 (2 – 8 nov) | E1: ajuste de encoders y línea base |
| 3 (9 – 15 nov) | E2: prompt estructurado, zero-shot y few-shot fijo |
| 4 (16 – 22 nov) | E2: few-shot dinámico (RAG) y referencia comercial |
| 5 (23 – 29 nov) | E4: LLM anotador y curva de 0/10/50/100 gold |
| 6 (30 nov – 6 dic) | Análisis: tablas, IC, abreviadas vs no, errores. Opcionales E3/E5 |
| 7 (7 – 13 dic) | Redacción del manuscrito y presentación |

## Entregables

1. Manuscrito con estado del arte, metodología y resultados (formato artículo).
2. Repositorio público con código, prompts y configuración reproducible.
3. Presentación final.

## Consideraciones éticas

- Se usan solo corpus públicos y desidentificados.
- Los modelos corren localmente. Solo el texto público del CWLC se envía a una API comercial, como referencia, y se declara en la metodología.
- Se reportan las limitaciones: las derivaciones no son fichas completas de CESFAM, y los LLM pueden haber visto el corpus en su preentrenamiento.

## Referencias clave

- Báez P, et al. Automatic extraction of nested entities in clinical referrals in Spanish. ACM Trans Comput Healthcare. 2022. doi:10.1145/3498324
- Rojas M, et al. Assessing the limits of straightforward models for nested NER in Spanish clinical narratives. LOUHI 2022. doi:10.18653/v1/2022.louhi-1.2
- Naguib M, et al. Few-shot clinical entity recognition in English, French and Spanish: masked language models outperform generative model prompting. Findings of EMNLP 2024. doi:10.18653/v1/2024.findings-emnlp.400
- Hu Y, et al. Improving large language models for clinical named entity recognition via prompt engineering. JAMIA. 2024. doi:10.1093/jamia/ocad259
- Ge Y, et al. Improving few-shot NER for LLMs using structured dynamic prompting with retrieval augmented generation. npj Artif Intell. 2026. doi:10.1038/s44387-025-00062-2
- Chen Q, et al. Benchmarking large language models for biomedical NLP applications and recommendations. Nat Commun. 2025. doi:10.1038/s41467-025-56989-2
- Gallifant J, et al. The TRIPOD-LLM reporting guideline. Nat Med. 2025.
