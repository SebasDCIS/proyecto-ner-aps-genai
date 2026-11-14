# Guía de estudio del proyecto NER en APS chilena (versión final, 9 de noviembre de 2026)

Esta guía explica el proyecto completo desde cero, en el orden en que conviene estudiarlo. Cada capítulo corresponde a un audio del cuaderno de NotebookLM. Las cifras son las del manuscrito final y salen de los archivos de resultados del repositorio (github.com/SebasDCIS/proyecto-ner-aps-genai).

Equipo: Sebastián Inostroza Hurtado, Maite Bahamondes y Ruth Vergara. Curso: Inteligencia Artificial Generativa y Modelos Fundacionales, profesor Rodrigo Salas, Doctorado en Ciencias e Ingeniería para la Salud, Universidad de Valparaíso. Entrega en diciembre de 2026: manuscrito en formato IEEE y presentación de 15 a 20 minutos.

---

## Capítulo 1. El problema y la pregunta

### De qué se trata

En la Atención Primaria de Salud (APS) chilena, casi toda la información clínica queda escrita como texto libre. Un médico que deriva a un paciente escribe algo como "pcte c/ DM2 desc, s/ ctrl hace 6m". Cualquier clínico entiende que el paciente tiene diabetes tipo 2 descompensada y lleva seis meses sin control. Un sistema informático no lo entiende.

Para convertir esa nota en datos, el primer paso es el reconocimiento de entidades nombradas, NER por su sigla en inglés (Named Entity Recognition). Hacer NER es ubicar, dentro de la oración, qué palabras exactas son una enfermedad, un medicamento o una abreviatura. No es resumir ni clasificar la oración completa: es marcar trozos de texto con su inicio, su fin y su tipo.

Un ejemplo real del corpus:

> "- ENFERMEDAD DE PARKINSON / - Fundamento Clínico APS : paciente autovalente , en control en APS por HTA , DM , DLP y artrosis ."

Las anotaciones humanas de esa oración son:
- Enfermedad: "ENFERMEDAD DE PARKINSON", "HTA", "DM", "DLP" y "artrosis".
- Abreviatura: "APS" (dos veces), "HTA", "DM" y "DLP".
- Hallazgo (Finding): "autovalente".

Fíjate en dos cosas. Primero, "HTA" es a la vez enfermedad y abreviatura: las entidades pueden superponerse o ir una dentro de otra (se dice que están anidadas). Segundo, "autovalente" no es enfermedad sino hallazgo. Esa distinción entre hallazgo y enfermedad aparece de nuevo en el análisis de errores.

### Por qué importa ahora

Hay dos motivos prácticos.
- Algunos proveedores de ficha clínica electrónica ya ofrecen herramientas de IA generativa en la APS chilena, sin publicar cómo rinden.
- La Ley 21.719 de protección de datos personales entra en vigencia en diciembre de 2026 y restringe enviar datos de salud a servicios externos. Un CESFAM necesita modelos que pueda correr en sus propios computadores.

### Qué dice la literatura

La literatura internacional sobre NER clínico es bastante consistente:
- Un encoder (un modelo tipo BERT o RoBERTa) ajustado con datos anotados supera a un LLM generativo usado solo con instrucciones (prompting). En español la diferencia es de 3 a 15 puntos de F1 (Naguib et al. 2024; Chen et al. 2025).
- Si el prompt incluye la guía de anotación, la distancia se reduce cerca de la mitad (Hu et al. 2024).
- Si los ejemplos del prompt se eligen por parecido con la oración que hay que anotar (few-shot dinámico), el LLM gana entre 5 y 9 puntos frente a ejemplos fijos (Ge et al. 2026).
- Cuando hay poca anotación, se propone que un LLM etiquete el texto y que un encoder pequeño aprenda de esas etiquetas. Eso se llama destilación.

El problema es de dónde viene esa evidencia: casi siempre de casos clínicos publicados en revistas o de notas en inglés. Una derivación de APS chilena es distinta: oraciones cortas, siglas locales, faltas de ortografía y plantillas repetidas.

### La pregunta del proyecto

¿Qué modelos, y usados de qué forma, reconocen mejor las entidades clínicas en derivaciones reales de APS chilena? ¿Coincide ese orden con el que reporta la literatura? Por eso es una evaluación comparativa: no proponemos un método nuevo, medimos con un mismo protocolo qué funciona mejor con nuestro texto.

Título del trabajo: *Evaluación comparativa de encoders ajustados y modelos de lenguaje generativos para el reconocimiento de entidades clínicas de atención primaria chilena*. El corpus son derivaciones a especialista (lista de espera), y eso se especifica dentro del manuscrito.

### Las cinco hipótesis

Las fijamos antes de correr cada experimento:
- H1. El encoder clínico ajustado obtiene el mayor F1 estricto.
- H2. El few-shot dinámico mejora al LLM frente al zero-shot y al few-shot con ejemplos fijos.
- H3. La distancia entre LLM y encoder es mayor en las entidades abreviadas.
- H4. Un encoder entrenado con etiquetas de un LLM más 50 oraciones anotadas queda a pocos puntos del encoder entrenado con todo el conjunto.
- H5. Un LLM comercial grande achica la distancia con el encoder, pero no la cierra. (Esta se agregó al incorporar GPT-5.2 y Gemini, antes de correrlos.)

---

## Capítulo 2. El corpus: Chilean Waiting List Corpus (CWLC)

### Qué es

El CWLC es el único corpus público chileno de este tipo. Lo publicaron Báez, Villena, Rojas, Durán y Dunstan (2020, versión piloto; 2022, versión completa). Contiene derivaciones desidentificadas de la lista de espera no GES, escritas y anotadas por médicos y dentistas. Tiene siete tipos de entidad: enfermedad, medicamento, abreviatura, hallazgo, parte del cuerpo, procedimiento y familiar. La licencia es CC BY-NC-SA 4.0 (uso no comercial). Usamos la versión 4 (Zenodo 5591011), en los archivos CoNLL que publicaron los autores.

### La partición

Mantuvimos la partición oficial, para poder comparar con Báez et al.:

| | Entrenamiento | Validación | Prueba |
|---|---|---|---|
| Oraciones | 8.014 | 890 | 990 |
| Palabras | 149.574 | 16.754 | 18.436 |
| Enfermedad | 8.860 | 981 | 1.071 |
| Medicamento | 823 | 95 | 92 |
| Abreviatura | 8.402 | 942 | 993 |

- Entrenamiento: con esto aprenden los modelos y de aquí salen los ejemplos de los prompts.
- Validación: sirve para decidir cuándo parar de entrenar (early stopping).
- Prueba (test): se usa una sola vez, al final, para reportar resultados. Nunca se usa para ajustar nada.

Medicamento tiene solo 92 menciones en el test. Con tan pocas, los intervalos de confianza son anchos (más o menos 7 puntos) y cualquier conclusión sobre medicamento es más débil.

### Por qué estas tres entidades

- Enfermedad y medicamento tienen valor clínico directo.
- Abreviatura es lo más propio del texto de APS.
- En el test, 119 enfermedades (11,1 %) contienen una abreviatura anotada. Con esos casos se mide H3.

Del test, el 61 % de las enfermedades, el 62 % de los medicamentos y el 93 % de las abreviaturas ya aparecían escritas igual en entrenamiento. Por eso también medimos aparte las menciones "nuevas", las que el modelo nunca vio.

### La auditoría antes de entrenar

Antes de entrenar revisamos fugas entre particiones:
- 96 oraciones del test (9,7 %) también están en entrenamiento. Casi todas son plantillas, como "se deriva para evaluación y manejo", o descripciones de la CIE-10. Contienen el 2,7 % de las entidades del test. Por eso reportamos todo también sin esas oraciones ("test sin duplicados").
- 42 textos idénticos están anotados de forma distinta. Es ruido de etiquetas: pone un techo al F1 que cualquier modelo puede alcanzar.

---

## Capítulo 3. Fundamentos: de la palabra al encoder ajustado

### Tokens y subpalabras

Un modelo de lenguaje no lee palabras: lee tokens. El tokenizador corta el texto en piezas frecuentes. Una palabra común como "furosemida" puede ser una sola pieza, mientras que una mal escrita como "FUSROSEMIDA" se parte en varias piezas que el modelo casi nunca vio juntas. Esto explica por qué los encoders fallan más con palabras mal escritas.

Cada token se convierte en un vector de números (embedding). El modelo trabaja con esos vectores.

### Transformers y atención

El transformer (Vaswani et al. 2017) procesa todos los tokens a la vez. Su pieza central es la autoatención: cada token mira a todos los demás y decide cuánto le importa cada uno. Así "desc" se interpreta según que esté al lado de "DM2" (descompensada) y no de otra cosa.

Hay dos familias principales:
- Encoders, como BERT (Devlin et al. 2019) y RoBERTa (Liu et al. 2019). Leen la oración completa en ambas direcciones y producen una representación de cada token. Son buenos para marcar o clasificar.
- Decoders generativos, los LLM como Llama, Qwen, GPT o Gemini. Generan texto palabra a palabra. Para hacer NER hay que pedirles que escriban la lista de entidades.

### Preentrenamiento y ajuste fino

Un encoder se preentrena primero con mucho texto sin anotar, adivinando palabras tapadas. Después se ajusta (fine-tuning) con pocos miles de oraciones anotadas para una tarea concreta. Usamos tres encoders:
- bsc-bio-ehr-es (Carrino et al. 2022): RoBERTa clínico español, unos 125 millones de parámetros, preentrenado con texto biomédico y clínico de España.
- roberta-clinical-wl-es (PLN@CMM): el mismo modelo con preentrenamiento continuo en derivaciones chilenas de lista de espera. No tenía una evaluación NER publicada.
- RigoBERTa Clinical (Subies et al. 2025): XLM-RoBERTa tamaño large, unos 560 millones de parámetros (4,5 veces más), preentrenado con ClinText-SP, el corpus clínico abierto más grande en español. Licencia no comercial.

### Etiquetado BIO, un modelo por entidad

Para que el encoder marque trozos de texto, cada palabra recibe una etiqueta:
- B (Begin): primera palabra de una entidad.
- I (Inside): palabras siguientes de la misma entidad.
- O (Outside): fuera de cualquier entidad.

"ENFERMEDAD DE PARKINSON" queda B, I, I. Como las entidades pueden superponerse ("HTA" es enfermedad y abreviatura), entrenamos un etiquetador separado por tipo de entidad. Rojas, Bravo-Marquez y Dunstan (2022) mostraron que, en el CWLC, esta arquitectura simple rinde mejor que las diseñadas para entidades anidadas.

El tokenizador divide cada palabra en subpalabras y solo la primera subpalabra lleva la etiqueta.

### Cómo entrenamos (E1)

- Optimizador AdamW, tasa de aprendizaje 3×10⁻⁵ (2×10⁻⁵ para RigoBERTa, porque los modelos grandes son más inestables).
- Lote de 16 oraciones, hasta 5 épocas, calentamiento lineal del 10 %.
- Early stopping con paciencia 2: si el F1 en validación no mejora en dos épocas seguidas, se detiene y se queda con la mejor época.
- Tres semillas aleatorias (42, 43 y 44) por modelo.

Los encoders base se entrenaron en un Mac M5 de 24 GB, unos 15 minutos por modelo. RigoBERTa no cupo en esa memoria: con lote 16, y también con lote 8 y acumulación de gradientes, el computador empezó a usar el disco como memoria y cada época pasaba de dos horas. Se entrenó en una GPU A100 de 80 GB en Google Colab, con el mismo código y los mismos datos (verificados con huella digital), en unos 11 minutos por modelo. La acumulación de gradientes procesa lotes chicos y actualiza los pesos cada cierto número de lotes, para mantener el lote efectivo en 16 sin usar tanta memoria.

---

## Capítulo 4. LLM generativos y prompting (E2 y E2 nube)

### Qué es un prompt para NER

El prompt es la instrucción que recibe el LLM. El nuestro tiene:
1. La tarea: "Eres un anotador clínico experto. Recibirás una oración de una derivación escrita por un médico o dentista de APS en Chile..."
2. La guía de anotación, redactada solo con el conjunto de entrenamiento. Por ejemplo: incluir los diagnósticos CIE-10 completos, marcar fármacos sin dosis, marcar "+" como abreviatura cuando reemplaza a "y", copiar cada mención exactamente como aparece aunque tenga errores de ortografía.
3. Un esquema JSON que obliga a responder con una lista de pares {tipo, texto}.

Usamos temperatura 0 (respuestas lo más deterministas posible) y semilla fija.

### Del texto a posiciones: el localizador

El LLM devuelve textos, no posiciones. Un programa busca cada texto dentro de la oración, de preferencia como palabra completa, y lo convierte en posiciones de carácter. Si el texto no está en la oración, se descarta y se cuenta como alucinación. Probado con respuestas perfectas, este paso pierde menos de 0,5 puntos de F1, así que no explica las diferencias.

### Tres estrategias

- Zero-shot: solo la tarea y la guía, sin ejemplos.
- Few-shot fijo: cinco ejemplos de entrenamiento elegidos al azar, siempre los mismos. Probamos tres sets distintos y reportamos la media.
- Few-shot dinámico: para cada oración del test, BM25 busca las cinco oraciones de entrenamiento más parecidas y las pone como ejemplos. BM25 es un buscador clásico por palabras compartidas (Robertson y Zaragoza 2009). Es una forma de recuperación aumentada (RAG).

En el 8,3 % del test, el ejemplo recuperado era la misma oración, repetida en entrenamiento. El análisis sin duplicados controla esa fuga.

### Los modelos

- E2 local: Llama 3.1 8B y Qwen 2.5 7B, cuantizados, corriendo en el Mac con Ollama. No sacan datos del computador.
- E2 nube (techo comercial): GPT-5.2 (esfuerzo de razonamiento bajo; la API no acepta temperatura) y Gemini 3.1 Pro (versión preliminar, gemini-3.1-pro-preview; no acepta semilla). Recibieron el mismo prompt, la misma guía y los mismos ejemplos. Solo se corrieron zero-shot y dinámico. Gemini tiene un límite de 250 consultas diarias, así que el test se corrió durante varios días.

Mandar el test a una API es aceptable porque el CWLC es público y desidentificado. Con fichas reales no lo sería.

---

## Capítulo 5. Cómo medimos

### Precisión, recall y F1

- Precisión: de todo lo que marcó el modelo, qué fracción era correcta.
- Recall (sensibilidad): de todo lo que había que marcar, qué fracción encontró.
- F1: la media armónica de ambas. Si una de las dos es baja, el F1 baja.

### Estricto y laxo

- F1 estricto (la métrica principal): una predicción cuenta solo si coinciden exactamente el inicio, el fin y el tipo. Si el gold es "caries profunda" y el modelo marca "caries", es un error.
- F1 laxo: basta con que se superponga y tenga el tipo correcto. "caries" contaría como acierto.
- La diferencia entre ambos dice cuántos errores son de límite.

### Bootstrap e intervalos

Con un solo test no sabemos cuánto cambiaría el resultado con otras oraciones. El bootstrap remuestrea las 990 oraciones 1.000 veces, con reposición, y recalcula el F1 cada vez. Con eso sale un intervalo de confianza del 95 %.

Para comparar dos sistemas usamos bootstrap pareado: en cada remuestreo se usan las mismas oraciones para ambos y se mira la diferencia. Si el intervalo de la diferencia no incluye el cero, la diferencia es significativa.

### Semillas y la regla de las tres

El ajuste fino cambia según la semilla aleatoria (Dodge et al. 2020; Mosbach et al. 2021). Por eso repetimos cada modelo entrenable tres veces y reportamos media ± desviación estándar. Regla: solo afirmamos que un encoder supera a otro si la comparación pareada es significativa en las tres semillas. Los LLM con temperatura 0 tienen una corrida por estrategia, que comparamos contra cada semilla del encoder.

### Subgrupos

Medimos el recall en:
- menciones vistas o nuevas respecto del entrenamiento;
- enfermedades con y sin abreviatura (H3);
- palabras mal escritas (31 enfermedades y 5 medicamentos del test, detectadas con diccionario y distancia de edición y revisadas a mano);
- abreviaturas según su frecuencia en entrenamiento.

En los LLM registramos también la tasa de alucinación, los JSON inválidos, el tiempo por oración y el costo.

### Reproducibilidad

Cada resultado guarda la huella SHA-256 de los 21 archivos del corpus, de la configuración, del código (commit de git) y de las predicciones, más la versión exacta del modelo y del entorno. Cada notebook verifica la huella de los datos antes de entrenar. Todas las comparaciones pareadas se regeneran desde las predicciones guardadas con scripts/comparaciones_pareadas.py, sin entrenar ni pagar nada de nuevo. El reporte sigue la guía TRIPOD-LLM (Gallifant et al. 2025).

---

## Capítulo 6. Resultados de encoders y LLM

### Tabla general (F1 estricto en las 990 oraciones de prueba)

| Sistema | Enfermedad | Medicamento | Abreviatura |
|---|---|---|---|
| E1 español | 0,798 ± 0,006 | 0,840 ± 0,012 | 0,950 ± 0,004 |
| E1 chileno | 0,815 ± 0,010 | 0,794 ± 0,046 | 0,952 ± 0,002 |
| E1 RigoBERTa | 0,803 ± 0,004 | 0,780 ± 0,015 | 0,946 ± 0,013 |
| Llama 8B zero-shot | 0,446 | 0,451 | 0,524 |
| Llama 8B fijo | 0,526 | 0,393 | 0,603 |
| Llama 8B dinámico | 0,650 | 0,697 | 0,703 |
| Qwen 7B zero-shot | 0,537 | 0,589 | 0,516 |
| Qwen 7B fijo | 0,560 | 0,617 | 0,554 |
| Qwen 7B dinámico | 0,663 | 0,670 | 0,642 |
| GPT-5.2 zero-shot | 0,645 | 0,768 | 0,776 |
| GPT-5.2 dinámico | 0,727 | 0,772 | 0,887 |
| Gemini 3.1 zero-shot | 0,618 | 0,765 | 0,888 |
| Gemini 3.1 dinámico | 0,717 | 0,844 | 0,901 |
| Votación 6 encoders | 0,837 | 0,831 | 0,957 |

### Encoders

- Ganan en enfermedad y abreviatura. El chileno llega a 0,815 en enfermedad; los tres encoders quedan entre 0,946 y 0,952 en abreviatura.
- Sin las oraciones duplicadas, su F1 baja menos de un punto (0,009 como máximo). La fuga no explica los resultados.
- Superan al piloto del CWLC (0,77, 0,75 y 0,92). El mejor resultado publicado con el CWLC (83,16 micro-F1, Rojas et al. 2022) usa otra partición y otras entidades, por lo que no se compara directo.
- Chileno contra español en enfermedad: +2,6 y +2,4 puntos significativos en dos semillas, +0,2 en la tercera. Con la regla de las tres semillas no podemos afirmar que sea mejor, aunque la tendencia va siempre a favor del chileno.
- En medicamento rindió más el español; el chileno tuvo una corrida inestable (0,741 con la semilla 42).

### LLM locales

- Sin ejemplos quedan lejos (0,45 a 0,59). Llama zero-shot inventó el 52,5 % de lo que devolvió y entregó 22 JSON inválidos.
- Los ejemplos dinámicos mejoraron a los cuatro LLM en las tres entidades. Frente a los fijos sumaron 12,4 puntos en enfermedad y 10,0 en abreviatura con Llama, y 10,3 y 8,8 con Qwen, todos significativos. Sin duplicados, la ventaja casi no cambia. H2 se cumple.
- Aun así, el mejor LLM local queda 13,5 a 15,2 puntos bajo los encoders en enfermedad, 14,3 bajo el encoder español en medicamento y unos 25 en abreviatura. Todo significativo.
- Su problema es la precisión: Qwen dinámico encontró el 71 % de las enfermedades, pero solo el 62 % de lo que marcó era correcto.
- Qwen fue más confiable: con ejemplos dinámicos inventó el 5,2 % de las menciones (Llama, el 19,4 %) y no rompió ningún JSON.

### LLM comerciales

- GPT-5.2 dinámico: 0,727 en enfermedad y 0,887 en abreviatura, casi sin alucinaciones (0,4 %).
- Gemini 3.1 Pro dinámico: 0,717 y 0,901, y empata con el encoder en medicamento (0,844 contra 0,840, sin diferencia significativa).
- Gemini supera a GPT-5.2 en medicamento por 0,073 (IC 95 % de 0,027 a 0,135); en las otras entidades no hay diferencia entre ellos.
- Contra E1, Gemini queda 7 a 11 puntos abajo en enfermedad y 4 a 5 en abreviatura, significativo en las tres semillas.
- Gemini tuvo un recall en enfermedad de 0,839 (a la par del encoder chileno), pero una precisión de 0,626 y una tasa de alucinación del 14 %.
- Costo de las 990 oraciones con ambas estrategias: 4,26 dólares con GPT-5.2 y 4,46 con Gemini.
- H5 se cumple en dos de tres entidades.

### Abreviaturas (H3)

Con ejemplos dinámicos, todos los LLM reconocieron peor las enfermedades escritas con abreviatura:
- Llama: 0,655 con abreviatura y 0,764 sin ella.
- Qwen: 0,647 y 0,723.
- GPT-5.2: 0,748 y 0,804.
- Gemini: 0,824 y 0,841.

El encoder chileno no tiene esa brecha (0,843 y 0,835); el español sí, aunque menor (0,790 y 0,816). En enfermedades abreviadas, el chileno supera al español por 5,3 puntos. H3 se cumple en enfermedad, y es el resultado que más apoya adaptar el modelo al texto local.

En la entidad abreviatura, los LLM locales quedan 25 a 31 puntos bajo los encoders: no aprenden solos las convenciones del corpus (anotar "APS" o "+" como abreviaturas).

---

## Capítulo 7. Escala del modelo y destilación (RigoBERTa y E4)

### ¿Un encoder más grande sube el techo?

No. RigoBERTa Clinical, 4,5 veces más grande, no superó a los encoders base en ninguna entidad:
- Enfermedad: empata con el español (+0,003 a +0,008, sin significancia) y pierde contra el chileno en dos de tres semillas (−0,018 y −0,019).
- Medicamento: queda bajo el español en las tres semillas, significativo en una.
- Abreviatura: empata, salvo con la semilla 42.

Conclusión: en este corpus importó más que el modelo hubiera visto derivaciones chilenas que su tamaño.

La excepción son las 66 abreviaturas nunca vistas en entrenamiento: RigoBERTa tuvo un recall de 0,662, contra 0,601 del chileno y 0,606 del español. Tiene sentido para un modelo con preentrenamiento clínico más amplio, pero el subgrupo es chico.

Hay un costo práctico: el modelo grande no se pudo ajustar en el computador del proyecto y necesitó una GPU de 80 GB. Un CESFAM tampoco tendría ese equipo.

### E4: el LLM como anotador

Simula un centro con mucho texto y poca anotación:
1. Qwen 2.5 7B (el maestro) etiqueta 2.000 oraciones de entrenamiento. Esas son las etiquetas silver.
2. Se toman N oraciones anotadas por humanos (gold): 0, 10, 50 o 100.
3. Un encoder (el alumno, bsc-bio-ehr-es) se entrena con silver + gold.
4. Se compara con el mismo encoder entrenado solo con las N oraciones gold.

Como en ese centro no habría validación, se usa la última época y un mínimo de 300 actualizaciones de pesos.

Resultados en enfermedad:
- El alumno supera a su maestro: con 50 gold llega a 0,644; las etiquetas del propio Qwen tenían 0,586.
- Las silver ayudan cuando hay poco gold: con 10 oraciones, el alumno llega a 0,571 y el modelo solo con gold, a 0,278.
- Entre 50 y 100 oraciones la curva se aplana (0,644 a 0,650).

H4 no se cumple: con 50 gold, el alumno queda 15 a 17 puntos bajo E1 en enfermedad, 23 en medicamento y 36 en abreviatura. En abreviatura las silver incluso empeoran: con 100 oraciones, solo gold da 0,729 y agregar silver baja a 0,634. El maestro tuvo precisión alta (0,90) y recall bajo (0,49) en abreviatura, y el alumno heredó ese sesgo. El techo del alumno lo puso la calidad del maestro (F1 entre 0,50 y 0,69 según la entidad).

En medicamento, una semilla colapsó (F1 0, pérdida estancada): es la inestabilidad del ajuste fino en clases poco frecuentes. Se reporta tal cual.

Dato útil: con 100 oraciones anotadas, el alumno (0,650) casi iguala al LLM local con ejemplos dinámicos (0,663), que necesita las 8.014 oraciones de entrenamiento para buscar ejemplos y tarda más de un segundo por oración.

---

## Capítulo 8. Errores, híbridos y votación

### Tipología de errores en enfermedad

Clasificamos cada predicción como correcta, límite más largo, límite más corto, espuria (marcó algo que no es enfermedad) u omitida.

- Con ejemplos dinámicos, los LLM comerciales aciertan casi tantas enfermedades exactas como el encoder: 899 Gemini y 854 GPT-5.2, contra 895 del encoder chileno.
- La diferencia está en las espurias: 112 del encoder chileno, 286 de GPT-5.2, 406 de Gemini dinámico y 636 de Gemini zero-shot.
- Entre el 67 % y el 93 % de las espurias se superponen con un hallazgo anotado, como "dolor", "vómitos" o "mordida invertida".
- La guía del CWLC separa hallazgo (signo o síntoma) de enfermedad, y los LLM no siguieron esa separación aunque la guía estaba en el prompt. Parte del "error" de los LLM es un desacuerdo de criterio con la anotación.

### Donde el LLM grande gana

- Palabras mal escritas (31 enfermedades): el recall de los encoders baja de 0,82 a 0,84 a entre 0,52 y 0,56; Gemini sin ejemplos se mantiene en 0,77. La diferencia pareada fue de +0,19 a +0,32, significativa en tres de seis comparaciones.
- Abreviaturas nunca vistas (66): encoders base 0,60; LLM comerciales entre 0,71 y 0,76.
- Abreviaturas frecuentes (774): encoders entre 0,97 y 0,99.

El encoder reconoce casi siempre la jerga que vio en entrenamiento; la que no vio, los LLM grandes la deducen mejor. Los LLM locales no tienen esa ventaja.

### ¿Y un sistema híbrido?

Si se juntan las enfermedades que encuentra el encoder con las que encuentra un LLM, el recall llega a entre 0,87 y 0,92 (el encoder solo, entre 0,81 y 0,84). Probamos tres combinaciones simples:
1. Unión de ambas predicciones.
2. Agregar solo las del LLM que no chocan con las del encoder.
3. Agregar solo las que caen en palabras que el encoder nunca vio.

Las tres empeoraron el F1 de forma significativa, porque cada acierto del LLM trae varios falsos positivos. Un híbrido útil necesitaría la confianza del encoder o un paso de verificación. Queda como trabajo futuro. Las palabras mal escritas son solo el 3 % de las enfermedades del test.

### Votación entre encoders

Se combinan los seis modelos base de E1 (dos encoders por tres semillas). Una entidad queda si al menos cuatro de los seis la predicen igual (mayoría estricta, regla fijada antes de mirar el test).

- Enfermedad: 0,837 (IC 95 % de 0,815 a 0,857), precisión 0,862 y recall 0,813. Supera a cada uno de los seis modelos por 1,3 a 4,5 puntos, con diferencias significativas. Es el mejor resultado del estudio.
- Abreviatura: 0,957 (mejor que dos de los seis modelos).
- Medicamento: 0,831 (sin diferencias significativas).
- Con RigoBERTa (nueve modelos, cinco votos): 0,838 en enfermedad, ya sin ventaja significativa contra todos.

La ganancia sale de promediar la variación entre semillas. Combinar semillas rindió más que agrandar el modelo, y seis modelos de 125 millones de parámetros todavía corren en un computador común.

---

## Capítulo 9. Conclusiones, limitaciones y cómo defender el proyecto

### Resumen de hipótesis

| | Resultado | Evidencia |
|---|---|---|
| H1 | Apoyada | Mayor F1 en enfermedad y abreviatura; en medicamento empata con Gemini dinámico |
| H2 | Apoyada | Dinámico mejor que zero-shot en los cuatro LLM y mejor que fijo en los dos locales |
| H3 | Apoyada en enfermedad | Con ejemplos dinámicos los cuatro LLM pierden recall en enfermedades abreviadas; el encoder chileno no |
| H4 | No apoyada | Con 50 gold, 15 a 36 puntos bajo E1 |
| H5 | Apoyada en 2 de 3 | Los comerciales quedan bajo E1 en enfermedad y abreviatura; Gemini empata en medicamento |

### Conclusiones

- En derivaciones chilenas se repitió lo que reporta la literatura: el encoder ajustado gana y los ejemplos dinámicos ayudan.
- Dos sorpresas: la destilación quedó mucho más lejos de lo esperado, y un LLM comercial empató con el encoder en medicamento.
- El tamaño del modelo no fue lo que movió el resultado; la adaptación al texto local y la combinación de semillas sí.

### Recomendación para un CESFAM

- Si tiene texto anotado: un encoder base ajustado con texto local, o una votación de varios. Es lo más preciso, corre en un computador común y no saca datos del centro.
- Si no lo tiene: anotar algunos cientos de oraciones con criterio clínico antes que confiar en etiquetas de un LLM local.
- El LLM grande sirve para lo que el encoder no vio (palabras mal escritas, siglas nuevas), pero falta diseñar bien cómo combinarlos.

### Limitaciones

- Una derivación no es una ficha completa: los resultados podrían cambiar en evoluciones o planes de cuidado de CESFAM. No existe en Chile un corpus público de ese tipo.
- Contaminación posible: el encoder chileno se preentrenó con derivaciones de lista de espera sin que se publique cuáles, y los LLM comerciales pudieron ver el CWLC, público desde 2022. Sus resultados serían un techo optimista.
- Ruido de anotación (42 textos idénticos anotados distinto) y pocos medicamentos (92).
- Una sola corrida por estrategia en los LLM; Gemini en versión preliminar.
- No se hicieron E3 (ajuste fino de un LLM con LoRA) ni E5 (normalización previa de abreviaturas), por tiempo.
- La distinción hallazgo/enfermedad de la guía del CWLC penaliza a los LLM.

### Trabajo futuro

1. Un híbrido que use la confianza del encoder para decidir cuándo consultar al LLM.
2. Validar en evoluciones y planes de cuidado de CESFAM (objetivo de la tesis doctoral de Sebastián).
3. Medir robustez con texto escrito por pacientes (lenguaje coloquial, mensajería), con una lista de equivalencias que falta revisar con clínicos.

### Preguntas probables en la presentación y cómo responderlas

- ¿Por qué no usaron solo GPT o Gemini, si son los mejores modelos? Porque no son los mejores en esta tarea: quedan bajo el encoder en enfermedad y abreviatura, y obligan a sacar los datos del centro, algo que la Ley 21.719 restringe.
- ¿No es injusto comparar un modelo entrenado con 8.014 oraciones contra un LLM sin entrenar? Es justamente la pregunta práctica: qué rinde más en un CESFAM. Por eso también está E4, que simula tener poca anotación.
- ¿Cómo saben que la diferencia no es suerte? Por el bootstrap pareado y la regla de las tres semillas.
- ¿Y si el test se filtró al entrenamiento? Lo auditamos: 9,7 % de oraciones repetidas, y sin ellas el F1 cambia menos de un punto.
- ¿Por qué no afirman que el encoder chileno es mejor que el español? Gana en dos de tres semillas y en enfermedades abreviadas por 5,3 puntos; con nuestra regla estricta no lo afirmamos como robusto.
- ¿Por qué RigoBERTa no ganó, siendo más grande? Porque aquí pesa más haber visto texto chileno que el tamaño; y el modelo grande no cabe en un computador común.
- ¿Qué es lo más útil que dejan? Una comparación justa y reproducible, la evidencia de que un encoder local es suficiente y viable, y la votación entre semillas como mejora barata (0,837).

---

## Glosario rápido

- APS: Atención Primaria de Salud. CESFAM: Centro de Salud Familiar.
- NER: reconocimiento de entidades nombradas.
- Entidad anidada: entidad dentro de otra ("DM2" dentro de "DM2 descompensada").
- Token: pieza en que el tokenizador corta el texto.
- Encoder: modelo que lee la oración completa y representa cada token (BERT, RoBERTa).
- LLM: modelo de lenguaje grande generativo (Llama, Qwen, GPT, Gemini).
- Ajuste fino (fine-tuning): entrenar un modelo preentrenado con datos anotados de una tarea.
- BIO: esquema de etiquetas Begin, Inside, Outside.
- Zero-shot / few-shot: sin ejemplos / con algunos ejemplos en el prompt.
- BM25: buscador por palabras compartidas que usamos para elegir ejemplos parecidos.
- Alucinación: mención que el LLM devuelve y que no está en la oración.
- Gold: anotación humana. Silver: anotación generada por un modelo.
- Destilación: entrenar un modelo pequeño con las etiquetas de uno grande.
- F1 estricto / laxo: coincidencia exacta / coincidencia parcial.
- Bootstrap pareado: remuestreo de oraciones para saber si una diferencia es real.
- Semilla: número que fija el azar del entrenamiento.
- Early stopping: detener el entrenamiento cuando deja de mejorar en validación.
- Huella SHA-256: código que identifica un archivo; si cambia un byte, cambia la huella.
