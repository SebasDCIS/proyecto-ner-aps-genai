# Guía de estudio desde cero: reconocimiento de entidades clínicas en derivaciones de APS chilena

Esta guía explica, sin suponer conocimientos previos de inteligencia artificial, el proyecto "Evaluación comparativa de encoders ajustados y modelos de lenguaje generativos para el reconocimiento de entidades clínicas de atención primaria chilena". Cuenta qué problema aborda, qué se hizo, qué resultados salieron y qué significa cada término técnico que aparece en el manuscrito.

Conviene leerla en orden. Las primeras secciones definen los conceptos y las siguientes los usan. Al final hay preguntas frecuentes con sus respuestas y un glosario alfabético para consultar rápido.

## 1. El problema

En la atención primaria de salud (APS) chilena, casi toda la información clínica queda escrita como texto libre. Cuando un médico de un CESFAM deriva a un paciente a especialista, escribe algo como "pcte c/ DM2 desc, s/ ctrl hace 6m". Cualquier clínico entiende que el paciente tiene diabetes mellitus tipo 2 descompensada y lleva seis meses sin control. Un sistema informático no lo entiende: para él es una cadena de letras.

Ese texto tiene información útil para gestionar la lista de espera, para estudios epidemiológicos o para alertas clínicas, pero nadie puede leer a mano cientos de miles de derivaciones. La idea es que un programa encuentre automáticamente, dentro de cada oración, las enfermedades, los medicamentos y las abreviaturas.

El texto de APS es difícil para un programa por varias razones. Las oraciones son cortas y telegráficas. Hay muchas siglas locales (HTA, DM2, DLP, APS). Hay faltas de ortografía ("FUSROSEMIDA" en vez de "furosemida") y frases copiadas de plantillas. Casi todos los modelos de inteligencia artificial se evaluaron con texto en inglés o con casos clínicos publicados en revistas, que están bien redactados. No se sabía cuál funciona mejor con derivaciones chilenas reales.

Hay dos motivos prácticos para responder esa pregunta ahora. Algunos proveedores de ficha electrónica ya venden herramientas de inteligencia artificial generativa para la APS, sin publicar cuánto aciertan. Y la Ley 21.719 de protección de datos personales, que entra en vigencia en diciembre de 2026, restringe el envío de datos de salud a servicios externos. Un CESFAM necesita saber qué modelo puede correr en sus propios computadores y cuánto texto tendría que anotar para entrenarlo.

## 2. Los conceptos de partida

El procesamiento de lenguaje natural (PLN, o NLP en inglés) es el área que hace que los computadores trabajen con texto escrito por personas.

Un corpus es una colección de textos reunida para estudiarla o para entrenar modelos. Cuando los textos tienen marcas hechas por personas expertas, se habla de corpus anotado. La anotación es justamente ese trabajo: un experto lee cada oración y marca qué trozos corresponden a qué cosa.

Una entidad es un trozo de texto que nombra algo de un tipo definido. En este proyecto hay tres tipos: enfermedad, medicamento y abreviatura. En la oración "paciente en control en APS por HTA, DM y artrosis", las enfermedades son "HTA", "DM" y "artrosis", y las abreviaturas son "APS", "HTA" y "DM".

El reconocimiento de entidades nombradas (NER, por Named Entity Recognition) es la tarea de encontrar esas entidades. Un sistema de NER recibe una oración y devuelve cada entidad con tres datos: dónde empieza, dónde termina y de qué tipo es. No resume ni clasifica la oración completa. Solo marca trozos.

En el ejemplo anterior, "HTA" es a la vez enfermedad y abreviatura. Cuando una entidad queda dentro de otra o se superpone con ella, se habla de entidades anidadas. Otro ejemplo: "DM2" es una abreviatura que está dentro de la enfermedad "DM2 descompensada". Esto obliga a diseñar el sistema de modo que una misma palabra pueda tener más de una etiqueta.

## 3. Cómo lee texto un modelo

Un modelo de lenguaje no lee letras ni palabras completas. Lee tokens. Un token es una pieza de texto que el tokenizador, el programa que corta el texto, considera frecuente. Una palabra común como "furosemida" puede ser un solo token. Una palabra rara o mal escrita, como "FUSROSEMIDA", se parte en varias piezas pequeñas (subpalabras) que el modelo casi nunca vio juntas. Por eso los errores de ortografía le cuestan tanto a un modelo: la palabra deja de parecerse a la que aprendió.

Cada token se transforma en una lista de números llamada vector o embedding. Esos números representan el significado del token de una forma que el computador puede calcular. Dos tokens con significado parecido quedan con vectores parecidos. Todo lo que hace el modelo después son operaciones matemáticas sobre esos vectores.

## 4. Transformers, encoders y LLM

Casi todos los modelos de lenguaje actuales usan una arquitectura llamada transformer, presentada en 2017. Su pieza central es la atención: cada token mira a todos los demás tokens de la oración y decide cuánto le importa cada uno para entender su propio significado. Gracias a eso, "desc" se interpreta como "descompensada" cuando está al lado de "DM2", y no como otra cosa.

Los parámetros son los números internos del modelo que se ajustan durante el entrenamiento. Se cuentan en millones (M) o miles de millones (B, por billion en inglés). Un modelo de 125M tiene 125 millones de parámetros; uno de 8B, ocho mil millones. Más parámetros suele significar más capacidad, pero también más memoria y más tiempo de cálculo.

Hay dos familias de transformers que importan en este proyecto.

Los encoders, como BERT y RoBERTa, leen la oración completa en ambas direcciones y producen una representación de cada token. No escriben texto nuevo. Sirven para clasificar o marcar trozos de texto, que es justo lo que pide NER.

Los modelos generativos, o decoders, escriben texto token por token, prediciendo cuál viene después. Cuando son muy grandes se les llama LLM (Large Language Models, modelos de lenguaje grandes). Llama, Qwen, GPT y Gemini son LLM. Para hacer NER con un LLM hay que pedirle por escrito que entregue la lista de entidades.

Tanto los encoders como los LLM son modelos fundacionales: modelos entrenados con enormes cantidades de texto general que después se adaptan a tareas específicas. El proyecto compara dos formas de adaptarlos.

## 5. Preentrenamiento y ajuste fino

Un encoder se construye en dos etapas.

La primera es el preentrenamiento. El modelo lee millones de oraciones sin anotar y aprende a adivinar palabras tapadas. Así aprende cómo funciona el idioma. Si el texto de preentrenamiento es clínico, también aprende el vocabulario médico.

La segunda es el ajuste fino (fine-tuning). Se toma el modelo preentrenado y se sigue entrenando con unos pocos miles de oraciones anotadas para una tarea concreta, en este caso marcar entidades. El modelo ajusta sus parámetros hasta que sus marcas se parecen a las de los anotadores.

En el proyecto se usaron tres encoders preentrenados. El primero es bsc-bio-ehr-es, un RoBERTa de 125 millones de parámetros preentrenado con texto biomédico y clínico de España; en la guía y el manuscrito se le llama "encoder español". El segundo es roberta-clinical-wl-es, el mismo modelo con un preentrenamiento adicional usando derivaciones chilenas de lista de espera; se le llama "encoder chileno". Este paso extra se conoce como preentrenamiento continuo. El tercero es RigoBERTa Clinical, un modelo de tamaño large (unos 560 millones de parámetros, 4,5 veces más que los otros dos), preentrenado con el corpus clínico abierto más grande en español.

## 6. Cómo se entrena un encoder para NER

### El etiquetado BIO

Para que un encoder marque trozos de texto, cada palabra recibe una etiqueta. B (begin) indica la primera palabra de una entidad, I (inside) las palabras siguientes de la misma entidad y O (outside) las palabras que no forman parte de ninguna. "ENFERMEDAD DE PARKINSON" queda B, I, I, y una palabra común como "paciente" queda O.

Como las entidades pueden superponerse, se entrenó un etiquetador separado para cada tipo: uno marca enfermedades, otro medicamentos y otro abreviaturas. Así "HTA" puede quedar marcada como enfermedad por un modelo y como abreviatura por otro. Trabajos anteriores con este mismo corpus mostraron que esta solución simple rinde mejor que arquitecturas diseñadas para entidades anidadas.

Como el tokenizador parte algunas palabras en subpalabras, solo la primera subpalabra de cada palabra lleva la etiqueta. El resto se ignora al calcular el error.

### Los términos del entrenamiento

Entrenar consiste en mostrarle al modelo ejemplos, medir cuánto se equivoca y corregir un poco sus parámetros. Esa medida del error se llama función de pérdida.

Un lote (batch) es el grupo de oraciones que el modelo procesa antes de cada corrección. Se usó un lote de 16 oraciones.

Una época es una pasada completa por todo el conjunto de entrenamiento. Se entrenó hasta cinco épocas.

La tasa de aprendizaje indica qué tan grande es cada corrección. Si es muy alta, el modelo salta de un lado a otro y no aprende; si es muy baja, aprende demasiado lento. Se usó 3×10⁻⁵ (0,00003) para los encoders base y 2×10⁻⁵ para RigoBERTa, porque los modelos grandes son más inestables.

El optimizador es el algoritmo que decide cómo corregir los parámetros. Se usó AdamW, el estándar para este tipo de modelos. El calentamiento (warmup) hace que la tasa de aprendizaje parta baja y suba de a poco durante el primer 10 % del entrenamiento, para no desordenar lo que el modelo ya sabía.

El early stopping (detención temprana) evita el sobreajuste, que ocurre cuando el modelo memoriza los ejemplos de entrenamiento en vez de aprender a generalizar. Después de cada época se mide el desempeño en el conjunto de validación. Si no mejora en dos épocas seguidas (paciencia 2), el entrenamiento se detiene y se conserva la mejor época.

La semilla es un número que fija el azar del entrenamiento: el orden de los ejemplos y los valores iniciales de algunas piezas del modelo. Con otra semilla, el mismo modelo con los mismos datos puede terminar con resultados algo distintos. Por eso cada encoder se entrenó tres veces, con las semillas 42, 43 y 44.

### Dónde se entrenó

Los encoders base se entrenaron en un computador Mac M5 de 24 GB de memoria, en unos 15 minutos cada uno. RigoBERTa no cupo en esa memoria. Se probó con lote 8 y acumulación de gradientes, una técnica que procesa lotes chicos y corrige los parámetros cada cierto número de lotes para simular un lote más grande con menos memoria. Aun así el computador empezó a usar el disco como memoria y cada época pasaba de dos horas. Finalmente se entrenó en una GPU A100 de 80 GB en Google Colab, con el mismo código y los mismos datos, en unos 11 minutos por modelo. Una GPU es una tarjeta gráfica que hace estos cálculos mucho más rápido que el procesador normal.

## 7. Cómo se usa un LLM para NER

### El prompt

A un LLM no se le entrena en este proyecto. Se le entrega una instrucción escrita, el prompt, y se le pide que responda. Usar un modelo así, solo con instrucciones, se llama prompting.

El prompt del proyecto tiene tres partes. La primera describe la tarea: el modelo es un anotador clínico que recibirá una oración de una derivación de APS chilena. La segunda es una guía de anotación con las reglas del corpus, redactada mirando solo el conjunto de entrenamiento: por ejemplo, incluir los diagnósticos CIE-10 completos, marcar los fármacos sin la dosis y marcar "+" como abreviatura cuando reemplaza a "y". La tercera es un esquema JSON que obliga al modelo a responder con una lista ordenada de pares {tipo, texto}. JSON es un formato de texto estructurado que un programa puede leer sin ambigüedad. Si el modelo entrega algo que no respeta ese formato, se cuenta como JSON inválido.

La temperatura controla cuánto azar usa el LLM al elegir cada palabra. Con temperatura 0, el modelo elige siempre la opción más probable y responde casi igual cada vez. Se usó temperatura 0 en los modelos que lo permitían.

### Del texto a posiciones

El LLM devuelve textos ("HTA"), no posiciones. Un programa busca cada texto dentro de la oración y lo convierte en su posición de inicio y fin. Si el texto devuelto no aparece en la oración, se descarta y se cuenta como alucinación. Una alucinación es una respuesta que el modelo inventa. Este paso se probó con respuestas perfectas y pierde menos de 0,5 puntos de F1, así que no explica las diferencias entre modelos.

### Tres estrategias de prompting

En zero-shot el prompt lleva solo la tarea y la guía, sin ejemplos.

En few-shot fijo el prompt incluye cinco oraciones de ejemplo ya anotadas, elegidas al azar del entrenamiento y siempre las mismas. Se probaron tres sets distintos de cinco ejemplos y se reporta el promedio.

En few-shot dinámico, para cada oración que hay que anotar, un buscador elige las cinco oraciones de entrenamiento más parecidas y las pone como ejemplos. El buscador es BM25, un método clásico que mide cuántas palabras comparten dos textos, dando más peso a las palabras poco frecuentes. Recuperar ejemplos parecidos para mejorar la respuesta de un LLM es una forma de RAG (generación aumentada por recuperación).

### Los LLM usados

Los LLM locales corren dentro del propio computador y no envían datos fuera. Se usaron Llama 3.1 de 8B y Qwen 2.5 de 7B, a través de Ollama, un programa para correr LLM en un computador personal. Estaban cuantizados: sus parámetros se guardan con menos precisión numérica para que ocupen menos memoria, a cambio de una pequeña pérdida de calidad.

Los LLM comerciales corren en servidores de las empresas y se usan a través de una API, que es la forma en que un programa le envía consultas a otro servicio por internet. Se usaron GPT-5.2 (OpenAI) y Gemini 3.1 Pro (Google), con el mismo prompt, la misma guía y los mismos ejemplos. Funcionan como techo de referencia: muestran cuánto rinde un modelo de los más grandes disponibles. Se corrieron en zero-shot y few-shot dinámico. Gemini tiene un límite de 250 consultas diarias, así que el conjunto de prueba se corrió durante varios días. Enviar el texto a una API fue aceptable porque el corpus es público y está desidentificado; con fichas reales de pacientes no lo sería.

## 8. Destilación: un LLM como anotador

Anotar a mano es caro. La destilación propone otra vía: un modelo grande (el maestro) etiqueta mucho texto y un modelo pequeño (el alumno) aprende de esas etiquetas.

A las anotaciones hechas por personas se les llama gold (oro), porque son la referencia. A las generadas por un modelo se les llama silver (plata), porque son más baratas pero menos confiables.

En el experimento de destilación, Qwen 2.5 7B etiquetó 2.000 oraciones de entrenamiento (silver). Luego se tomó un número pequeño N de oraciones gold: 0, 10, 50 o 100. El encoder español se entrenó con las silver más esas N gold, y se comparó con el mismo encoder entrenado solo con las N gold. Esto simula un centro de salud con mucho texto y casi nada anotado. Como ese centro no tendría un conjunto de validación, se usó la última época de entrenamiento, con un mínimo de 300 correcciones de los parámetros.

## 9. Votación entre modelos

Un ensamble combina las predicciones de varios modelos. En este proyecto se usó votación por mayoría estricta entre los seis encoders base (dos encoders por tres semillas). Una entidad se acepta si al menos cuatro de los seis la marcan con el mismo inicio, fin y tipo. La regla se fijó antes de mirar los resultados del conjunto de prueba, para no elegirla a conveniencia. También se probó con nueve modelos, sumando las tres semillas de RigoBERTa, con cinco votos como mínimo.

La votación funciona porque cada semilla se equivoca en lugares algo distintos. Al exigir acuerdo, se eliminan errores aislados.

## 10. Cómo se mide el desempeño

### Particiones del corpus

El corpus se divide en tres conjuntos que nunca se mezclan. El de entrenamiento sirve para que los modelos aprendan y para sacar los ejemplos de los prompts. El de validación sirve para decidir cuándo detener el entrenamiento. El de prueba (test) se usa una sola vez, al final, para reportar los resultados; con él no se ajusta nada.

### Precisión, recall y F1

La precisión responde: de todo lo que marcó el modelo, ¿qué fracción era correcta? Un modelo que marca de más tiene precisión baja.

El recall (o sensibilidad) responde: de todo lo que había que marcar, ¿qué fracción encontró? Un modelo que se le pasan entidades tiene recall bajo.

El F1 es la media armónica de ambas, F1 = 2 × precisión × recall / (precisión + recall). Va de 0 a 1. Si una de las dos es baja, el F1 baja, así que obliga a ser bueno en ambas. Cuando se dice que un modelo quedó "15 puntos abajo", se habla de 0,15 de F1.

El F1 estricto, la métrica principal, cuenta una predicción como correcta solo si coinciden exactamente el inicio, el fin y el tipo. Si la anotación es "caries profunda" y el modelo marca "caries", es un error. El F1 laxo acepta cualquier superposición con el tipo correcto, así que "caries" contaría como acierto. La diferencia entre ambos indica cuántos errores son de límite, es decir, entidades encontradas pero cortadas de más o de menos.

### Intervalos de confianza y bootstrap

Un resultado medido en 990 oraciones podría cambiar si se usaran otras 990. El bootstrap estima esa variación: toma muchas muestras al azar de las mismas oraciones, con reposición (una oración puede salir más de una vez), y recalcula el F1 en cada muestra. Con 1.000 repeticiones se obtiene un intervalo de confianza del 95 % (IC 95 %): el rango donde probablemente está el valor real.

Para comparar dos sistemas se usa bootstrap pareado. En cada repetición se usan las mismas oraciones para los dos sistemas y se calcula la diferencia. Si el intervalo de esa diferencia no incluye el cero, la diferencia es significativa, o sea, difícil de explicar por azar.

### La regla de las tres semillas

Como el ajuste fino cambia con la semilla, un encoder podría ganar a otro solo por suerte. Por eso se exigió una regla estricta: un encoder supera a otro solo si la comparación pareada es significativa en las tres semillas. Los LLM, con temperatura 0, tienen una sola corrida por estrategia, que se comparó contra cada una de las tres semillas del encoder. Los resultados de los encoders se reportan como media ± desviación estándar (DE) de las tres semillas.

### Subgrupos

Fuera del F1 general, se midió el recall en grupos específicos de entidades: las ya vistas en entrenamiento frente a las nuevas, las enfermedades escritas con y sin abreviatura, las palabras mal escritas (31 enfermedades y 5 medicamentos del test, detectadas con un diccionario y una distancia de edición, y revisadas a mano) y las abreviaturas según su frecuencia. La distancia de edición cuenta cuántas letras hay que cambiar para pasar de una palabra a otra.

En los LLM también se registró la tasa de alucinación, los JSON inválidos, el tiempo por oración y el costo en dólares.

### Fugas y ruido

Una fuga de datos ocurre cuando información del conjunto de prueba se cuela en el entrenamiento, lo que infla los resultados. El ruido de etiquetas ocurre cuando los anotadores marcaron de forma distinta textos iguales; pone un techo al F1 que cualquier modelo puede alcanzar, porque ni siquiera la referencia es consistente.

### Reproducibilidad

Cada resultado guarda una huella SHA-256 de los archivos del corpus, de la configuración, del código y de las predicciones. Una huella es un código que identifica un archivo: si cambia un solo carácter, cambia la huella. Así se puede comprobar que dos corridas usaron exactamente los mismos datos. El reporte sigue la guía TRIPOD-LLM, una lista de lo que debe informar un estudio que evalúa LLM en salud.

## 11. El corpus: Chilean Waiting List Corpus

El Chilean Waiting List Corpus (CWLC) es el único corpus público chileno de este tipo. Lo publicaron Báez y colaboradores, con una versión piloto en 2020 y la versión completa en 2022. Reúne derivaciones desidentificadas de la lista de espera no GES (las patologías que no tienen garantía de oportunidad), escritas y anotadas por médicos y dentistas. Desidentificado significa que se quitaron los datos que permitirían reconocer al paciente. Tiene siete tipos de entidad: enfermedad, medicamento, abreviatura, hallazgo, parte del cuerpo, procedimiento y familiar. Su licencia, CC BY-NC-SA 4.0, permite usarlo sin fines comerciales.

Se usó la versión 4 con la partición oficial. El conjunto de entrenamiento tiene 8.014 oraciones (149.574 palabras), con 8.860 enfermedades, 823 medicamentos y 8.402 abreviaturas. El de validación tiene 890 oraciones. El de prueba tiene 990 oraciones, con 1.071 enfermedades, 92 medicamentos y 993 abreviaturas. Medicamento tiene tan pocas menciones en el test que sus intervalos de confianza llegan a más o menos 7 puntos; cualquier conclusión sobre esa entidad es más débil.

Se eligieron tres de los siete tipos. Enfermedad y medicamento tienen valor clínico directo, y abreviatura es lo más propio del texto de APS.

### Estudio descriptivo

Antes de entrenar se describió el corpus. Las oraciones son cortas pero con algunas muy largas: la mediana es de 15 palabras, el 90 % tiene 37 o menos, y la más larga llega a 234, porque junta en una línea el diagnóstico, el fundamento clínico y el examen físico. En entrenamiento, el 60 % de las oraciones tiene al menos una enfermedad, el 51 % una abreviatura y solo el 6 % un medicamento. Un 24 % no tiene ninguna de las tres.

Una enfermedad tiene una mediana de tres palabras, porque suele incluir calificativos ("diabetes mellitus no insulinodependiente"). Medicamentos y abreviaturas casi siempre son una sola palabra. Por eso los errores de límite se esperan sobre todo en enfermedad. Hay 1.113 abreviaturas distintas, pero las 15 más frecuentes reúnen el 43 % de las menciones; "aps" sola aparece 1.430 veces.

En el test, 119 enfermedades (11,1 %) se superponen con una abreviatura. Con ese grupo se evaluó si los modelos tienen más problemas con las enfermedades abreviadas. Del test, el 61 % de las enfermedades, el 62 % de los medicamentos y el 93 % de las abreviaturas ya aparecen escritas igual en entrenamiento.

### Auditoría

También se buscaron fugas. Hay 96 oraciones del test (9,7 %) que también están en entrenamiento. Casi todas son plantillas, como "se deriva para evaluación y manejo", o descripciones de la CIE-10, y contienen el 2,7 % de las entidades del test. Por eso todos los resultados se calcularon también sin esas oraciones. Se encontraron 42 textos idénticos con anotaciones distintas, que son ruido de etiquetas.

## 12. Pregunta, objetivos e hipótesis

La pregunta del proyecto es qué modelos, y usados de qué forma, reconocen mejor enfermedades, medicamentos y abreviaturas en derivaciones de APS chilena. Es una evaluación comparativa: no propone un método nuevo, sino que mide con un mismo protocolo qué funciona mejor con este texto y contrasta ese orden con el que reporta la literatura.

El objetivo general es comparar el desempeño de encoders ajustados y de modelos de lenguaje generativos en esa tarea, sobre derivaciones reales del CWLC y con un mismo protocolo de evaluación.

Los objetivos específicos son cuatro. Primero, ajustar tres encoders preentrenados para reconocer las tres entidades y medir su desempeño. Segundo, medir cuatro LLM generativos, dos locales y dos comerciales, con distintas formas de armar el prompt. Tercero, estimar cuánto se acerca al encoder completo un encoder entrenado con etiquetas de un LLM y pocas oraciones anotadas a mano. Cuarto, describir los errores de cada tipo de modelo y medir si combinarlos por votación mejora el resultado.

Las hipótesis se fijaron antes de correr cada experimento, a partir de la literatura. H1: un encoder ajustado obtiene un F1 estricto mayor que el de los LLM generativos usados con prompting. H2: elegir los ejemplos del prompt por similitud mejora el F1 de los LLM frente a no darles ejemplos y frente a darles siempre los mismos. H3: la diferencia de F1 entre el encoder y los LLM es mayor en las entidades escritas como abreviatura. H4: un encoder entrenado con etiquetas de un LLM y 50 oraciones anotadas queda a pocos puntos del encoder entrenado con todo el corpus. H5: un LLM comercial grande reduce la diferencia con el encoder, pero no llega a igualarlo.

Fijar las hipótesis antes de ver los datos importa porque impide acomodarlas después a lo que salió.

## 13. Qué se hizo, paso a paso

El trabajo siguió las etapas del proceso KDD (Knowledge Discovery in Databases), un esquema clásico para proyectos de análisis de datos.

En la selección se eligió el CWLC versión 4, con su partición oficial, y las tres entidades.

En el preprocesamiento se auditó el corpus en busca de fugas y duplicados, y se registraron las huellas de los archivos.

En la transformación se convirtió el texto al formato que necesita cada modelo: etiquetas BIO por palabra para los encoders, y un prompt con guía y salida JSON para los LLM.

En el modelado se corrieron los experimentos. E1 entrenó los tres encoders con tres semillas cada uno. E2 probó los dos LLM locales con las tres estrategias de prompting. E2 nube probó los dos LLM comerciales con zero-shot y few-shot dinámico. E4 hizo la destilación con Qwen como maestro. Al final se probó la votación entre encoders. Los nombres E3 y E5 correspondían a experimentos planificados que no se hicieron por tiempo: el ajuste fino de un LLM con LoRA (una técnica que ajusta solo una pequeña parte de los parámetros) y la normalización previa de abreviaturas.

En la evaluación se calcularon el F1 estricto y laxo con sus intervalos, las comparaciones pareadas, la regla de las tres semillas y el recall por subgrupo. Todos los sistemas predijeron las mismas 990 oraciones y se evaluaron con el mismo código. En total se compararon dieciséis sistemas.

## 14. Resultados

### Los encoders ganan en enfermedad y abreviatura

En enfermedad, el encoder chileno obtuvo 0,815 de F1 estricto (media de tres semillas), el español 0,798 y RigoBERTa 0,803. En abreviatura los tres quedaron entre 0,946 y 0,952. En medicamento el español llegó a 0,840, el chileno a 0,794 y RigoBERTa a 0,780. Sin las oraciones repetidas entre test y entrenamiento, el F1 de los encoders bajó menos de un punto, así que la fuga no explica estos valores.

El encoder chileno superó al español en enfermedad por 2,6 y 2,4 puntos en dos semillas, de forma significativa, y por 0,2 en la tercera. Con la regla de las tres semillas no se puede afirmar que sea mejor, aunque la tendencia va siempre a su favor.

Estos valores superan a los del piloto del CWLC (0,77 en enfermedad, 0,75 en medicamento y 0,92 en abreviatura).

### Los LLM locales quedan lejos, pero los ejemplos dinámicos ayudan

Sin ejemplos, los LLM locales quedaron entre 0,45 y 0,59. Llama en zero-shot inventó el 52,5 % de lo que devolvió y entregó 22 JSON inválidos.

Los ejemplos dinámicos mejoraron a los cuatro LLM en las tres entidades. Frente a los ejemplos fijos, sumaron 12,4 puntos en enfermedad y 10,0 en abreviatura con Llama, y 10,3 y 8,8 con Qwen, todos significativos. La literatura reportaba mejoras de 5 a 9 puntos, así que se repitió o un poco más. H2 se cumple.

Aun así, con su mejor estrategia, el mejor LLM local quedó entre 13,5 y 15,2 puntos bajo los encoders en enfermedad, 14,3 bajo el encoder español en medicamento y unos 25 en abreviatura. Su problema fue la precisión: Qwen con ejemplos dinámicos encontró el 71 % de las enfermedades, pero solo el 62 % de lo que marcó era correcto. Qwen fue más confiable que Llama: con ejemplos dinámicos inventó el 5,2 % de sus respuestas, contra 19,4 % de Llama.

### Los LLM comerciales se acercan, y Gemini empata en medicamento

GPT-5.2 con ejemplos dinámicos llegó a 0,727 en enfermedad, 0,772 en medicamento y 0,887 en abreviatura, y casi no inventó menciones (0,4 %). Gemini 3.1 Pro con ejemplos dinámicos llegó a 0,717, 0,844 y 0,901. En medicamento empató con el encoder español (0,844 contra 0,840, sin diferencia significativa). En enfermedad quedó entre 7 y 11 puntos bajo los encoders y en abreviatura entre 4 y 5, con diferencias significativas. Gemini encontró tantas enfermedades como el encoder chileno (recall 0,839), pero con precisión de 0,626. Correr las 990 oraciones con ambas estrategias costó 4,26 dólares con GPT-5.2 y 4,46 con Gemini. H5 se cumple en dos de tres entidades.

### Las abreviaturas confunden a los LLM

Con ejemplos dinámicos, todos los LLM reconocieron peor las enfermedades escritas con abreviatura que las escritas completas. El recall fue 0,655 contra 0,764 en Llama, 0,647 contra 0,723 en Qwen, 0,748 contra 0,804 en GPT-5.2 y 0,824 contra 0,841 en Gemini. El encoder chileno no tuvo esa brecha (0,843 y 0,835); el español sí, aunque menor (0,790 y 0,816). En enfermedades abreviadas, el chileno superó al español por 5,3 puntos. H3 se cumple en enfermedad, y es el resultado que más apoya adaptar el modelo al texto local.

En la entidad abreviatura, los LLM locales quedaron 25 a 31 puntos abajo, porque no aprendieron por sí solos las convenciones del corpus, como marcar "APS" o "+" como abreviaturas.

### Un encoder más grande no ayudó

RigoBERTa, 4,5 veces más grande, no superó a los encoders base en ninguna entidad. En enfermedad empató con el español y perdió contra el chileno en dos de tres semillas. En medicamento quedó bajo el español en las tres. Solo en las 66 abreviaturas que nunca aparecen en entrenamiento tuvo un recall mayor (0,662 contra 0,601 y 0,606), pero el grupo es chico. En este corpus importó más que el modelo hubiera visto derivaciones chilenas que su tamaño, y el modelo grande no cupo en el computador del proyecto.

### La destilación quedó lejos

En enfermedad, el alumno superó a su maestro: con 50 oraciones gold llegó a 0,644, mientras las etiquetas de Qwen tenían 0,586. Las silver ayudaron cuando había muy poco gold: con 10 oraciones, el alumno llegó a 0,571 y el modelo entrenado solo con esas 10, a 0,278. Entre 50 y 100 oraciones la mejora fue mínima (de 0,644 a 0,650).

Pero H4 no se cumple. Con 50 oraciones gold, el alumno quedó entre 15 y 17 puntos bajo los encoders completos en enfermedad, 23 en medicamento y 36 en abreviatura. En abreviatura las silver incluso empeoraron el resultado: con 100 oraciones, entrenar solo con gold dio 0,729, y agregar silver lo bajó a 0,634. El maestro marcaba pocas abreviaturas pero casi siempre bien (precisión 0,90, recall 0,49), y el alumno heredó ese sesgo. En medicamento, una semilla colapsó y no marcó ninguna entidad, algo que pasa en el ajuste fino de clases poco frecuentes.

Un dato útil: con 100 oraciones anotadas, el alumno llegó en enfermedad a 0,650, casi lo mismo que el LLM local con ejemplos dinámicos (0,663), que necesita las 8.014 oraciones de entrenamiento para buscar ejemplos.

### Qué tipo de errores comete cada modelo

Cada predicción de enfermedad se clasificó como correcta, con límite más largo, con límite más corto, espuria (marcó algo que no es enfermedad) u omitida. Con ejemplos dinámicos, los LLM comerciales acertaron casi tantas enfermedades exactas como el encoder: 899 Gemini y 854 GPT-5.2, contra 895 del encoder chileno. La diferencia estuvo en las espurias: 112 del encoder chileno, 286 de GPT-5.2, 406 de Gemini con ejemplos y 636 sin ellos.

Entre el 67 % y el 93 % de esas espurias, según el sistema, cayó sobre un hallazgo anotado, como "dolor", "vómitos" o "mordida invertida". La guía del CWLC separa el hallazgo (un signo o síntoma) de la enfermedad, y los LLM no siguieron esa separación aunque estaba en el prompt. Parte del error de los LLM es, entonces, un desacuerdo de criterio con la anotación.

En dos grupos los LLM comerciales fueron mejores. En las 31 enfermedades mal escritas, el recall de los encoders bajó a entre 0,52 y 0,56, mientras Gemini sin ejemplos se mantuvo en 0,77. En las 66 abreviaturas nunca vistas, los encoders base llegaron a 0,60 y los LLM comerciales a entre 0,71 y 0,76. En las 774 abreviaturas frecuentes, en cambio, los encoders llegaron a entre 0,97 y 0,99. El encoder reconoce casi siempre la jerga que vio en entrenamiento; la que no vio, los LLM grandes la deducen mejor.

Se probó combinar encoder y LLM. Juntando las enfermedades que encuentra cada uno, el recall sube a entre 0,87 y 0,92. Pero las tres combinaciones simples que se probaron empeoraron el F1, porque cada acierto del LLM llega con varios falsos positivos. Un sistema híbrido útil queda como trabajo futuro.

### La votación dio el mejor resultado

La votación de los seis encoders base llegó a 0,837 en enfermedad (IC 95 % de 0,815 a 0,857), con precisión de 0,862 y recall de 0,813. Superó a cada uno de los seis modelos por 1,3 a 4,5 puntos, con diferencias significativas. Es el mejor resultado del estudio en esa entidad. En abreviatura llegó a 0,957 y en medicamento a 0,831. Con nueve modelos (sumando RigoBERTa) enfermedad quedó en 0,838, sin ventaja adicional. Combinar semillas rindió más que agrandar el modelo, y seis modelos de 125 millones de parámetros todavía corren en un computador común.

### Resumen de las hipótesis

H1 se apoya: los encoders tienen el mayor F1 en enfermedad y abreviatura, y en medicamento empatan con Gemini. H2 se apoya: los ejemplos dinámicos mejoran a todos los LLM. H3 se apoya en enfermedad. H4 no se apoya: la destilación queda 15 a 36 puntos abajo. H5 se apoya en dos de tres entidades.

## 15. Qué significan los resultados

En derivaciones chilenas se repitió lo que reporta la literatura internacional: el encoder ajustado gana y los ejemplos dinámicos ayudan a los LLM. Hubo dos sorpresas. La destilación quedó mucho más lejos de lo esperado, y un LLM comercial empató con el encoder en medicamento.

Para un CESFAM que tiene texto anotado, la opción más precisa es un encoder base ajustado con texto local, o una votación de varios. Corre en un computador común y no saca datos del centro. Si no tiene texto anotado, le conviene anotar algunos cientos de oraciones con criterio clínico antes que confiar en etiquetas generadas por un LLM local. Los LLM grandes sirven para lo que el encoder no vio, como palabras mal escritas y siglas nuevas, pero todavía falta diseñar bien cómo combinarlos.

### Limitaciones

Una derivación es un texto corto escrito para justificar una interconsulta. Los resultados podrían cambiar con evoluciones o planes de cuidado de una ficha completa, y en Chile no existe un corpus público de ese tipo.

Hay riesgo de contaminación: el encoder chileno se preentrenó con derivaciones de lista de espera sin que se publique cuáles, y los LLM comerciales pudieron haber visto el CWLC, público desde 2022. Si eso pasó, sus resultados son un techo optimista.

No se probó el ajuste fino de un LLM. Estudios de 2025 y 2026 muestran que un LLM ajustado con instrucciones puede igualar o superar al encoder, así que las conclusiones valen para LLM usados con prompting. Los LLM se corrieron una vez por estrategia y Gemini estaba en versión preliminar. Medicamento tiene pocas menciones en el test, y el corpus tiene ruido de anotación. La distinción entre hallazgo y enfermedad de la guía del CWLC penaliza a los LLM; con otra guía, esa parte del resultado podría cambiar.

### Trabajo futuro

Quedan tres líneas. La primera es un sistema híbrido que use la confianza del encoder para decidir cuándo consultar al LLM. La segunda es validar los modelos en evoluciones y planes de cuidado de CESFAM, objetivo de una tesis doctoral en curso. La tercera es medir qué pasa con texto escrito por pacientes, con lenguaje coloquial y ruido de mensajería.

## 16. Preguntas frecuentes

¿Por qué no usar directamente GPT o Gemini, si son los modelos más grandes? Porque en esta tarea no fueron los mejores: quedaron bajo el encoder en enfermedad y abreviatura. Y obligan a enviar los datos del centro a un servicio externo, algo que la Ley 21.719 restringe.

¿No es injusto comparar un modelo entrenado con 8.014 oraciones contra un LLM que no se entrenó? Esa es justamente la pregunta práctica: qué rinde más para un CESFAM. Para el caso de poca anotación existe el experimento de destilación.

¿Cómo se sabe que una diferencia no es suerte? Por el bootstrap pareado y por la regla de las tres semillas, que exige que la diferencia sea significativa con cada una.

¿Y si el test se filtró al entrenamiento? Se auditó: el 9,7 % de las oraciones del test estaba repetido, y sin ellas el F1 cambió menos de un punto.

¿Por qué no se afirma que el encoder chileno es mejor que el español? Porque ganó en dos de tres semillas, no en las tres. Donde sí ganó fue en las enfermedades abreviadas, por 5,3 puntos.

¿Por qué RigoBERTa no ganó, si es más grande? Porque en este corpus pesó más haber visto texto chileno que el tamaño. Y el modelo grande no cabe en un computador común.

¿Por qué los LLM tienen tantos falsos positivos? Porque marcan como enfermedad muchos signos y síntomas que la guía del corpus clasifica como hallazgo.

¿Qué aporta el proyecto? Una comparación justa y reproducible de dieciséis sistemas en texto chileno real, la evidencia de que un encoder local basta y es viable, y la votación entre semillas como una mejora barata que llevó enfermedad a 0,837.

## 17. Glosario

Abreviatura: forma acortada de una palabra o sigla (HTA, DM2, APS). En este proyecto también es un tipo de entidad.

Ajuste fino (fine-tuning): seguir entrenando un modelo preentrenado con datos anotados de una tarea específica.

Alucinación: respuesta que un LLM inventa; aquí, una mención que no aparece en la oración.

API: forma en que un programa envía consultas a un servicio externo por internet.

APS: atención primaria de salud. CESFAM: centro de salud familiar.

Atención (mecanismo de): parte del transformer en que cada token pondera a los demás para interpretar su significado.

BIO: esquema de etiquetas por palabra: B (inicio de entidad), I (dentro de la entidad), O (fuera).

BM25: buscador que mide cuántas palabras comparten dos textos; se usó para elegir ejemplos parecidos.

Bootstrap: remuestreo al azar de los datos para estimar cuánto varía un resultado. Pareado: cuando se aplica a dos sistemas con las mismas muestras para comparar su diferencia.

Corpus: colección de textos; anotado, si tiene marcas hechas por expertos.

Cuantización: guardar los parámetros de un modelo con menos precisión para que ocupe menos memoria.

CWLC: Chilean Waiting List Corpus, corpus de derivaciones chilenas usado en el proyecto.

Destilación: entrenar un modelo pequeño (alumno) con etiquetas generadas por uno grande (maestro).

Early stopping: detener el entrenamiento cuando el desempeño en validación deja de mejorar.

Embedding: vector de números asociado a un token, que codifica su significado.

Encoder: modelo que lee la oración completa y produce un vector para cada token; sirve para clasificar o marcar texto (BERT, RoBERTa).

Ensamble o votación: combinación de las predicciones de varios modelos.

Entidad: trozo de texto que nombra algo de un tipo definido. Anidada: entidad dentro de otra o superpuesta con ella.

Época: una pasada completa por el conjunto de entrenamiento.

F1: media armónica de precisión y recall. Estricto: exige coincidencia exacta de inicio, fin y tipo. Laxo: acepta superposición.

Few-shot: prompt con algunos ejemplos resueltos. Fijo: siempre los mismos. Dinámico: elegidos por similitud con cada oración.

Fuga de datos: cuando información del test se cuela en el entrenamiento.

Gold y silver: anotación humana y anotación generada por un modelo.

GPU: procesador especializado que acelera los cálculos de entrenamiento.

Hallazgo: en la guía del CWLC, un signo o síntoma, distinto de una enfermedad.

Huella SHA-256: código que identifica un archivo; cambia si cambia un solo carácter.

Intervalo de confianza del 95 %: rango donde probablemente está el valor real de una medida.

JSON: formato de texto estructurado que un programa puede leer sin ambigüedad.

KDD: Knowledge Discovery in Databases, esquema de etapas para proyectos de análisis de datos (selección, preprocesamiento, transformación, modelado y evaluación).

LLM: modelo de lenguaje grande generativo (Llama, Qwen, GPT, Gemini).

Lote (batch): grupo de ejemplos que el modelo procesa antes de cada corrección.

Modelo fundacional: modelo entrenado con grandes cantidades de datos generales que luego se adapta a tareas específicas.

NER: reconocimiento de entidades nombradas.

Parámetros: números internos del modelo que se ajustan al entrenar; se cuentan en millones (M) o miles de millones (B).

Partición: división del corpus en entrenamiento, validación y prueba.

PLN (NLP): procesamiento de lenguaje natural.

Precisión: fracción de lo marcado por el modelo que es correcto.

Preentrenamiento: primera etapa de entrenamiento con texto sin anotar. Continuo: preentrenamiento adicional con texto de un dominio específico.

Prompt: instrucción escrita que recibe un LLM. Prompting: usar un LLM solo con instrucciones, sin entrenarlo.

RAG: generación aumentada por recuperación; dar al LLM información o ejemplos buscados para cada consulta.

Recall (sensibilidad): fracción de lo que había que marcar que el modelo encontró.

Ruido de etiquetas: anotaciones inconsistentes en el corpus.

Semilla: número que fija el azar del entrenamiento.

Significativa (diferencia): diferencia difícil de explicar por azar; en el bootstrap, cuando su intervalo no incluye el cero.

Sobreajuste: cuando un modelo memoriza el entrenamiento y no generaliza.

Tasa de aprendizaje: tamaño de cada corrección de los parámetros durante el entrenamiento.

Temperatura: cuánto azar usa un LLM al generar; con 0 responde casi siempre igual.

Token: pieza en que el tokenizador corta el texto. Subpalabra: pedazo de una palabra que el tokenizador separa.

Transformer: arquitectura de red neuronal basada en atención, base de los encoders y los LLM actuales.

Zero-shot: prompt sin ejemplos.
