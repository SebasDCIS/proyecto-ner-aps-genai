"""Contenido del manuscrito en el formato Word del curso.

Marcas: *cursiva*, **negrita**, ^superíndice^, `monoespaciado`, [@clave] cita.
"""
from pathlib import Path

FIG = Path(__file__).resolve().parent.parent / "figuras"
COL = 3.3   # ancho de una columna, en pulgadas
PAG = 6.9   # ancho de página útil


def construir(d):
    d.titulo("Evaluación comparativa de encoders ajustados y modelos de lenguaje generativos "
             "para el reconocimiento de entidades clínicas de atención primaria chilena")
    d.autores([("Sebastián Inostroza Hurtado", "1"), ("Maite Bahamondes", "1"), ("Ruth Vergara", "1")])
    d.afiliacion("1", "Doctorado en Ciencias e Ingeniería para la Salud, Universidad de Valparaíso, "
                 "Valparaíso, Chile. Autor de correspondencia: sebastian.inostroza@postgrado.uv.cl")

    d.etiqueta_y_texto("resumen", "RESUMEN",
        "En la atención primaria de salud (APS) chilena, la mayor parte de la información clínica queda "
        "en texto libre, escrito con abreviaturas locales y estilo telegráfico. Para extraer de ese texto "
        "enfermedades, medicamentos y abreviaturas se usan modelos de reconocimiento de entidades "
        "nombradas (NER), pero la evidencia sobre cuál funciona mejor viene de casos clínicos publicados "
        "o de notas en inglés, no de derivaciones chilenas. En este trabajo comparamos, con un mismo "
        "protocolo, tres encoders ajustados, dos modelos de lenguaje generativos (LLM) locales de 7 y 8B "
        "parámetros y dos comerciales (GPT-5.2 y Gemini 3.1 Pro) con distintas formas de armar el prompt, y un "
        "encoder entrenado con etiquetas generadas por un LLM. Usamos las 990 oraciones de prueba del "
        "Chilean Waiting List Corpus, tres semillas por modelo entrenable y *bootstrap* pareado. El encoder "
        "adaptado a derivaciones chilenas obtuvo el mayor F1 estricto en enfermedad (0,815) y los encoders "
        "llegaron a 0,95 en abreviatura. Elegir los ejemplos del prompt por similitud mejoró a todos los "
        "LLM; con ellos, Gemini empató con el encoder en medicamento (0,844), pero los LLM locales quedaron "
        "entre 13 y 25 puntos abajo. La destilación con 50 oraciones anotadas quedó entre 15 y 36 puntos "
        "bajo el encoder, y la votación entre seis encoders subió enfermedad a 0,837. Para un centro que no "
        "puede enviar datos fuera, un encoder base ajustado con texto local sigue siendo la opción más precisa.")
    d.etiqueta_y_texto("claves", "PALABRAS CLAVES",
        "Reconocimiento de entidades nombradas, texto clínico en español, modelos de lenguaje generativos, "
        "ajuste fino, atención primaria de salud.", cierra_seccion=True)

    # ------------------------------------------------------------------ I
    d.h1("I", "Introducción")
    d.parrafo("En la APS chilena, el médico que deriva a un paciente escribe frases como “pcte c/ DM2 desc, "
              "s/ ctrl hace 6m”. Cualquier clínico entiende que el paciente tiene diabetes tipo 2 "
              "descompensada y lleva seis meses sin control, pero un sistema administrativo no lo entiende. "
              "Para convertir esa nota en datos, el primer paso es reconocer entidades nombradas (NER, por sus siglas en "
              "inglés): ubicar en la oración qué palabras son una enfermedad, un fármaco o una abreviatura.",
              sangria=False)
    d.parrafo("Los resultados publicados apuntan en una misma dirección. En NER clínico en español, un "
              "encoder del tipo BERT o RoBERTa ajustado con datos anotados supera por 3 a 15 puntos de F1 "
              "a un LLM generativo usado solo con instrucciones (*prompting*) [@naguib2024,chen2025]. Si el "
              "prompt incluye la guía de anotación, esa distancia se reduce cerca de la mitad [@hu2024]. Si "
              "los ejemplos del prompt se eligen por similitud con la oración de entrada (*few-shot* "
              "dinámico, una forma de recuperación aumentada), el LLM gana entre 5 y 9 puntos frente a "
              "ejemplos fijos [@ge2026]. Cuando hay poca anotación, otra opción es que un LLM etiquete el "
              "texto y que un encoder pequeño aprenda de esas etiquetas (destilación).")
    d.parrafo("Esa evidencia sale casi siempre de casos clínicos publicados en revistas o de notas en "
              "inglés. Una derivación de APS tiene oraciones cortas, siglas locales, faltas de ortografía y "
              "plantillas repetidas. En Chile, el único corpus público de este tipo es el Chilean Waiting "
              "List Corpus (CWLC) [@baez2020,baez2022]. Con él se han publicado encoders y arquitecturas "
              "para entidades anidadas [@rojas2022coling,rojas2022louhi,rojas2022flair], y una comparación "
              "con solo 100 oraciones de entrenamiento en la que un RoBERTa clínico superó a Llama-3-8B por "
              "14 puntos [@naguib2024]. No encontramos trabajos que comparen con el CWLC completo, y con un "
              "mismo protocolo, encoders ajustados, LLM locales, LLM comerciales y destilación.")
    d.parrafo("El problema también es práctico. Algunos proveedores de ficha electrónica ya ofrecen "
              "herramientas de IA generativa en la APS chilena, sin métricas públicas. A eso se suma la Ley "
              "21.719 de protección de datos personales, que entra en vigencia en diciembre de 2026 y restringe el "
              "envío de datos de salud a servicios externos [@ley21719]. Un CESFAM necesita saber qué "
              "modelo funciona en sus propios equipos y cuánto texto tendría que anotar.")
    d.parrafo("Este trabajo es una evaluación comparativa. Su objetivo general es comparar el desempeño de "
              "encoders ajustados y de modelos de lenguaje generativos en el reconocimiento de enfermedades, "
              "medicamentos y abreviaturas en derivaciones reales del CWLC, con un mismo protocolo de "
              "evaluación. Los objetivos específicos son cuatro:")
    d.lista(["Ajustar tres encoders preentrenados para reconocer las tres entidades y medir su desempeño.",
             "Medir el desempeño de cuatro LLM generativos, dos locales y dos comerciales, con tres formas de "
             "armar el prompt: sin ejemplos, con ejemplos fijos y con ejemplos elegidos por similitud.",
             "Estimar cuánto se acerca al encoder entrenado con todo el corpus un encoder entrenado con "
             "etiquetas generadas por un LLM y pocas oraciones anotadas a mano.",
             "Describir los errores de cada tipo de modelo y medir si combinar sus predicciones por "
             "votación mejora el resultado."])
    d.parrafo("Antes de correr cada experimento fijamos cinco hipótesis, tomadas de la literatura:")
    d.lista(["**H1.** Un encoder ajustado obtiene un F1 estricto mayor que el de los LLM generativos.",
             "**H2.** Elegir los ejemplos del prompt por similitud con la oración mejora el F1 de los LLM "
             "frente a no darles ejemplos (*zero-shot*) y frente a darles siempre los mismos (*few-shot* fijo).",
             "**H3.** La diferencia de F1 entre el encoder y los LLM es mayor en las entidades escritas como "
             "abreviatura que en las escritas completas.",
             "**H4.** Un encoder entrenado con etiquetas generadas por un LLM y 50 oraciones anotadas a mano "
             "queda a pocos puntos de F1 del encoder entrenado con todo el corpus anotado.",
             "**H5.** Un LLM comercial grande reduce la diferencia de F1 con el encoder, pero no llega a "
             "igualarlo."], numerada=False)
    d.parrafo("Comparamos dieciséis sistemas sobre el mismo conjunto de prueba, con tres semillas por "
              "modelo entrenable y pruebas pareadas. Es también la primera evaluación NER en el CWLC del "
              "encoder adaptado a derivaciones chilenas (`roberta-clinical-wl-es`) y de RigoBERTa Clinical. "
              "El análisis de errores separa los errores de límite, las entidades espurias, las palabras mal "
              "escritas y las abreviaturas nunca vistas. El código, los prompts y los resultados de cada "
              "corrida están en un repositorio público.")
    d.parrafo("El resto del artículo se organiza así. La Sección II describe el corpus y los métodos. La Sección III define "
              "las métricas, presenta el estudio descriptivo de los datos y los resultados de cada "
              "experimento, y cierra con la discusión de las hipótesis y las limitaciones. La Sección IV "
              "resume las conclusiones y el trabajo futuro.")

    # ------------------------------------------------------------------ II
    d.h1("II", "Materiales y métodos")
    d.parrafo("Organizamos el trabajo según las etapas del proceso KDD. La selección y el preprocesamiento "
              "del corpus se describen en la Subsección A. La transformación del texto en etiquetas, los "
              "modelos y su entrenamiento, en la Subsección B. La evaluación, en la Sección III. La Fig. 1 resume "
              "las cinco etapas.", sangria=False)
    d.fig_inline(FIG / "fig_metodologia.png", 1,
                 "Etapas del estudio, ordenadas según el proceso KDD.", 3.0)
    d.h2("A", "Materiales")
    d.parrafo("Usamos la versión 4 del CWLC (Zenodo 5591011), en los archivos CoNLL que publicaron Báez et "
              "al. [@baez2022]. El corpus contiene derivaciones desidentificadas de la lista de espera no GES, "
              "escritas y anotadas por médicos y dentistas, con siete tipos de entidad, y tiene licencia "
              "CC BY-NC-SA 4.0. Mantuvimos la partición oficial en oraciones (Tabla I) para que los "
              "resultados se puedan comparar con los de Báez et al.", sangria=False)
    d.parrafo("De los siete tipos usamos tres. Enfermedad y medicamento tienen valor clínico directo, y "
              "abreviatura es lo más propio del texto de APS. Las entidades pueden ir una dentro de otra: "
              "“DM2” es una abreviatura dentro de la enfermedad “DM2 descompensada”. Como los datos son "
              "públicos y están desidentificados, pudimos enviar el conjunto de prueba a las API comerciales. "
              "Con fichas reales eso no sería aceptable.")
    d.cap_tabla("I", "Partición del CWLC y entidades usadas")
    d.tabla(["", "Entrenamiento", "Validación", "Prueba"],
            [["Oraciones", "8.014", "890", "990"],
             ["Palabras", "149.574", "16.754", "18.436"],
             ["Enfermedad", "8.860", "981", "1.071"],
             ["Medicamento", "823", "95", "92"],
             ["Abreviatura", "8.402", "942", "993"]],
            [1300, 1200, 1000, 900])

    d.h2("B", "Métodos")
    d.parrafo("La Tabla II resume los experimentos. Todos predicen las mismas 990 oraciones y se evalúan "
              "con el mismo código. Para los encoders, el texto se transforma en etiquetas BIO por palabra; "
              "para los LLM, la salida es una lista de pares {tipo, texto} que un programa convierte en "
              "posiciones de carácter. Así los dos tipos de modelo se comparan sobre la misma "
              "representación.", sangria=False)

    def tabla_diseno():
        d.cap_tabla("II", "Experimentos. Los modelos entrenables se repitieron con las semillas 42, 43 y 44")
        d.tabla(["Experimento", "Modelos", "Estrategia", "Datos que usa"],
                [["E1 · encoder ajustado", "`bsc-bio-ehr-es` (RoBERTa clínico español, 125M) [@carrino2022]; "
                  "`roberta-clinical-wl-es` (el mismo, con preentrenamiento continuo en derivaciones "
                  "chilenas); RigoBERTa Clinical (XLM-RoBERTa *large*, 560M) [@subies2025]",
                  "Un etiquetador BIO por tipo de entidad; *early stopping* con F1 en validación",
                  "8.014 oraciones anotadas"],
                 ["E2 · LLM local", "Llama 3.1 8B [@llama3] y Qwen 2.5 7B [@qwen25], cuantizados, vía Ollama",
                  "*Zero-shot*, *few-shot* fijo (k = 5, tres sets) y *few-shot* dinámico (k = 5, BM25)",
                  "Guía de anotación; ejemplos solo de entrenamiento"],
                 ["E2 nube · techo comercial", "GPT-5.2 [@openai2025] y Gemini 3.1 Pro [@gemini2026] vía API",
                  "*Zero-shot* y *few-shot* dinámico, con el mismo prompt de E2", "Igual que E2"],
                 ["E4 · destilación", "Maestro: Qwen 2.5 7B. Alumno: `bsc-bio-ehr-es`",
                  "El maestro etiqueta 2.000 oraciones (*silver*); el alumno se entrena con *silver* + 0, 10, "
                  "50 o 100 oraciones *gold*", "Hasta 100 oraciones anotadas"],
                 ["Votación", "Seis modelos de E1 (dos encoders base × tres semillas)",
                  "Mayoría estricta, fijada antes de mirar el test", "Las predicciones de E1"]],
                [1500, 3900, 2900, 1700], alin=["left"] * 4, sep_filas=(2, 3, 4, 5))
    d.ancho_completo(tabla_diseno)

    d.parrafo("Para conservar las entidades anidadas entrenamos un etiquetador BIO por tipo de entidad. En "
              "el CWLC, esta arquitectura simple rinde mejor que las diseñadas para entidades anidadas "
              "[@rojas2022coling]. El tokenizador divide cada palabra en subpalabras y solo la primera lleva "
              "etiqueta. Usamos AdamW con tasa de aprendizaje 3×10^−5^, lote de 16, hasta cinco épocas, "
              "calentamiento lineal del 10 % y *early stopping* con paciencia 2 según el F1 estricto en "
              "validación. Para RigoBERTa Clinical bajamos la tasa a 2×10^−5^, el rango habitual en modelos "
              "*large*. Los encoders base se entrenaron en un Mac M5 de 24 GB, en unos 15 minutos cada uno. "
              "RigoBERTa no cupo en esa memoria: con lote 16, y también con lote 8 y acumulación de "
              "gradientes, el sistema empezó a usar el disco y cada época pasaba de dos horas. Lo entrenamos "
              "entonces en una GPU A100 de Google Colab, con el mismo código, los mismos datos (verificados "
              "por huella) y lote 16; cada modelo tardó unos 11 minutos.",
              cabeza="1) E1, encoders ajustados:")
    d.parrafo("El prompt tiene la tarea, una guía de anotación que redactamos solo con el conjunto de "
              "entrenamiento y un esquema JSON que obliga al modelo a responder con pares {tipo, texto}. "
              "Usamos temperatura 0 y semilla fija. Si un texto devuelto no está en la oración, lo "
              "descartamos y lo contamos como alucinación. Al probarlo con respuestas perfectas, este paso "
              "pierde menos de 0,5 puntos de F1. En el *few-shot* fijo usamos tres sets de cinco ejemplos al "
              "azar y reportamos la media. En el dinámico, BM25 [@robertson2009] busca las cinco oraciones "
              "de entrenamiento más parecidas a cada oración de prueba. En el 8,3 % del test, el ejemplo "
              "recuperado es la misma oración repetida en entrenamiento; el análisis sin duplicados controla "
              "esa fuga. Los LLM comerciales recibieron el mismo prompt, la misma guía y los mismos ejemplos. "
              "GPT-5.2 corrió con esfuerzo de razonamiento bajo y sin temperatura, porque la API no acepta "
              "ese parámetro. Gemini 3.1 Pro (`gemini-3.1-pro-preview`) corrió durante varios días por su "
              "límite de 250 consultas diarias, y sin semilla, que no acepta. Guardamos la versión servida "
              "en cada respuesta que la informó.", cabeza="2) E2, LLM con prompting:")
    d.parrafo("Este experimento simula un centro con mucho texto y poca anotación. Qwen 2.5 7B, el LLM "
              "local más confiable en E2, etiquetó 2.000 oraciones de entrenamiento. Con N = 0 trabajó en "
              "*zero-shot*; con N > 0 recibió los cinco ejemplos más parecidos, buscados solo entre las N "
              "oraciones *gold*. Después entrenamos el encoder español con esas etiquetas *silver* más las "
              "N oraciones *gold*, y lo comparamos con el mismo encoder entrenado solo con las N oraciones "
              "*gold*. Un centro así no tendría conjunto de validación, por lo que usamos la última época y "
              "un mínimo de 300 actualizaciones de pesos.", cabeza="3) E4, LLM como anotador:")
    d.parrafo("Combinamos las predicciones de los seis modelos base de E1. Una entidad queda si al menos "
              "cuatro de los seis la predicen con el mismo inicio, fin y tipo. Fijamos esta regla antes de "
              "mirar el test. Al terminar RigoBERTa repetimos la votación con nueve modelos y cinco votos.",
              cabeza="4) Votación entre encoders:")
    d.parrafo("Cada resultado guarda la huella SHA-256 de los archivos del corpus, de la configuración, "
              "del código (commit de git) y de las predicciones, junto con la revisión exacta de cada "
              "modelo en Hugging Face o su *digest* en Ollama. Cada notebook revisa la huella de los datos "
              "antes de entrenar, y las comparaciones pareadas se regeneran desde las predicciones guardadas. "
              "El reporte sigue la guía TRIPOD-LLM [@gallifant2025].", cabeza="5) Reproducibilidad:")

    # ------------------------------------------------------------------ III
    d.h1("III", "Resultados y discusión")
    d.h2("A", "Métricas de desempeño")
    d.parrafo("Para cada sistema y tipo de entidad calculamos la precisión P (la fracción de entidades "
              "predichas que son correctas), el recall R (la fracción de entidades del *gold* que el sistema "
              "encontró) y su media armónica, F1 = 2PR/(P + R). La métrica principal es el F1 estricto, que "
              "cuenta una predicción como correcta solo si coinciden el inicio, el fin y el tipo. El F1 laxo "
              "acepta cualquier superposición con el tipo correcto; la diferencia entre ambos estima cuántos "
              "errores son de límite.", sangria=False)
    d.parrafo("Los intervalos de confianza del 95 % salen de 1.000 remuestreos *bootstrap* por oración "
              "[@efron1993]. Para comparar dos sistemas usamos *bootstrap* pareado sobre las mismas "
              "oraciones [@bergkirkpatrick2012]. La semilla aleatoria cambia el resultado del ajuste fino "
              "[@dodge2020,mosbach2021], así que repetimos cada modelo entrenable con tres semillas y solo "
              "afirmamos que un encoder supera a otro si la comparación pareada es significativa en las "
              "tres. Los LLM, con temperatura 0, tienen una corrida por estrategia, que comparamos contra "
              "cada semilla del encoder.")
    d.parrafo("También medimos el recall en cuatro subgrupos: menciones vistas o nuevas respecto del "
              "entrenamiento, enfermedades con y sin abreviatura (H3), palabras mal escritas y abreviaturas "
              "según su frecuencia. Las palabras mal escritas las detectamos con un diccionario, el "
              "vocabulario de entrenamiento y una distancia de edición de 1 o 2, y revisamos la lista a "
              "mano: quedaron 31 enfermedades y 5 medicamentos del test. En los LLM registramos también la "
              "tasa de alucinación, los JSON inválidos, el tiempo por oración y el costo.")

    d.h2("B", "Estudio descriptivo de los datos")
    d.parrafo("Las derivaciones son textos cortos con una cola larga (Fig. 2a). La mediana es de 15 "
              "palabras por oración y el 90 % tiene 37 o menos, aunque hay oraciones de hasta 234 palabras, "
              "que juntan en una sola línea el diagnóstico, el fundamento clínico y el examen físico. Las tres particiones tienen la misma "
              "forma: en entrenamiento, el 60 % de las oraciones contiene al menos una enfermedad, el 51 % "
              "una abreviatura y solo el 6 % un medicamento. Un 24 % no tiene ninguna de las tres entidades.",
              sangria=False)
    d.fig_inline(FIG / "fig_eda_cwlc.png", 2,
                 "Estudio descriptivo del conjunto de entrenamiento. (a) Distribución del largo de las "
                 "oraciones. (b) Abreviaturas más frecuentes; “aps” por sí sola suma 1.430 menciones.", COL)
    d.parrafo("Los tres tipos de entidad se comportan distinto. Una enfermedad tiene una mediana de tres "
              "palabras y solo el 28 % ocupa una palabra, porque suele incluir calificativos (“diabetes "
              "mellitus no insulinodependiente”). Medicamentos y abreviaturas casi siempre ocupan una "
              "palabra (89 % y 97 %). Por eso esperábamos los errores de límite sobre todo en enfermedad. "
              "Las abreviaturas se concentran mucho: hay 1.113 distintas en entrenamiento, pero las 15 más "
              "frecuentes reúnen el 43 % de las menciones (Fig. 2b). En el test, el 11,1 % de las "
              "enfermedades (119) se superpone con una abreviatura anotada; con ese subgrupo medimos H3, "
              "aunque los intervalos quedan anchos.")
    d.parrafo("También revisamos el corpus en busca de fugas entre particiones. De las oraciones del test, "
              "96 (9,7 %) también están en entrenamiento. Casi todas son plantillas, como “se deriva para "
              "evaluación y manejo”, o descripciones de la CIE-10, y contienen el 2,7 % de las entidades del "
              "test; por eso reportamos las métricas también sin esas oraciones. Del test, el 61 % de las "
              "enfermedades, el 62 % de los medicamentos y el 93 % de las abreviaturas ya aparecen escritas "
              "igual en entrenamiento. Por último, encontramos 42 textos idénticos con anotaciones distintas. "
              "Ese ruido de etiquetas pone un techo al F1 de cualquier modelo. En medicamento, con solo 92 "
              "menciones en el test, los intervalos de confianza serán anchos.")

    d.h2("C", "Estudios de simulación: comparación global")
    d.parrafo("La Fig. 3 y la Tabla III muestran el F1 estricto de todos los sistemas. Los encoders "
              "ajustados tuvieron los valores más altos en enfermedad y abreviatura: el chileno llegó a "
              "0,815 en enfermedad, y los tres encoders quedaron entre 0,946 y 0,952 en abreviatura. En "
              "medicamento empataron el encoder español (0,840) y Gemini 3.1 Pro con ejemplos dinámicos "
              "(0,844). Sin las oraciones repetidas, el F1 de los encoders bajó menos de un punto (0,009 "
              "como máximo), así que la fuga no explica estos valores.", sangria=False)

    def fig_global():
        d.fig_inline(FIG / "fig_comparacion_f1.png", 3,
                     "F1 estricto con IC 95 % en las 990 oraciones de prueba. Para los encoders se muestra la "
                     "media de tres semillas y el promedio de sus intervalos. La línea punteada marca el mejor "
                     "encoder individual. La votación combina seis encoders base con mayoría estricta.", PAG)
    d.ancho_completo(fig_global)

    d.cap_tabla("III", "F1 estricto en el test (media ± DE de 3 semillas para E1). En negrita, el mayor "
                "valor de cada columna entre los sistemas individuales")
    d.tabla(["Sistema", "Enfermedad", "Medicamento", "Abreviatura"],
            [["E1 español", "0,798 ± 0,006", "0,840 ± 0,012", "0,950 ± 0,004"],
             ["E1 chileno", "**0,815** ± 0,010", "0,794 ± 0,046", "**0,952** ± 0,002"],
             ["E1 RigoBERTa", "0,803 ± 0,004", "0,780 ± 0,015", "0,946 ± 0,013"],
             ["Llama 8B zero-shot", "0,446", "0,451", "0,524"],
             ["Llama 8B fijo", "0,526", "0,393", "0,603"],
             ["Llama 8B dinámico", "0,650", "0,697", "0,703"],
             ["Qwen 7B zero-shot", "0,537", "0,589", "0,516"],
             ["Qwen 7B fijo", "0,560", "0,617", "0,554"],
             ["Qwen 7B dinámico", "0,663", "0,670", "0,642"],
             ["GPT-5.2 zero-shot", "0,645", "0,768", "0,776"],
             ["GPT-5.2 dinámico", "0,727", "0,772", "0,887"],
             ["Gemini 3.1 zero-shot", "0,618", "0,765", "0,888"],
             ["Gemini 3.1 dinámico", "0,717", "**0,844**", "0,901"],
             ["E4 *silver* + 50 *gold*", "0,644", "0,406^†^", "0,592"],
             ["E4 *silver* + 100 *gold*", "0,650", "0,674", "0,634"],
             ["Votación (6 encoders)", "0,837", "0,831", "0,957"]],
            [1500, 1050, 1150, 1050], sep_filas=(4, 10, 14, 16),
            notas=["^†^Una de las tres semillas colapsó y no marcó ninguna entidad (Sección III-F)."])

    d.parrafo("Estos encoders superan a los del piloto del CWLC, que usó una versión más chica del corpus y "
              "obtuvo 0,77 en enfermedad, 0,75 en medicamento y 0,92 en abreviatura [@baez2020]. El mejor "
              "resultado publicado con el CWLC, 83,16 de micro-F1 sobre siete tipos de entidad "
              "[@rojas2022louhi], usa otra partición y otras entidades, por lo que no se puede comparar directo.")
    d.parrafo("En enfermedad, el encoder chileno superó al español por 2,6 y 2,4 puntos en dos semillas, con "
              "diferencias significativas, y por 0,2 en la tercera. Con la regla de las tres semillas no "
              "podemos afirmar que sea mejor, aunque la tendencia va siempre en la misma dirección. En "
              "medicamento rindió más el español; ahí el chileno tuvo una corrida inestable (0,741 con la "
              "semilla 42), y con 92 menciones los intervalos llegan a ±7 puntos.")

    d.h2("D", "Estudios de simulación: estrategias de prompting (E2)")
    d.parrafo("Sin ejemplos, los LLM locales quedaron lejos, entre 0,45 y 0,59 de F1 estricto. Llama 3.1 8B "
              "en *zero-shot* inventó el 52,5 % de las menciones que devolvió y entregó 22 JSON inválidos. Los "
              "ejemplos dinámicos mejoraron a los cuatro LLM en las tres entidades (Fig. 4), lo que apoya H2. "
              "Frente a los ejemplos fijos, el *few-shot* dinámico sumó 12,4 puntos en enfermedad y 10,0 en "
              "abreviatura con Llama, y 10,3 y 8,8 con Qwen, todos significativos. Es lo que reporta la "
              "literatura (5 a 9 puntos) o un poco más [@ge2026]. Sin las oraciones repetidas, la ventaja en "
              "enfermedad casi no cambió (12,4 puntos en Llama y 9,8 en Qwen), así que no viene de copiar "
              "oraciones idénticas.", sangria=False)

    def fig_estr():
        d.fig_inline(FIG / "fig_estrategias_llm.png", 4,
                     "F1 estricto de cada LLM según la estrategia de prompting. Para el *few-shot* fijo se "
                     "muestra la media de tres sets de ejemplos; a los LLM comerciales no se les aplicó esa "
                     "estrategia. La línea azul marca el mejor encoder de E1 en cada entidad.", PAG)
    d.ancho_completo(fig_estr)

    d.parrafo("Con su mejor estrategia, el mejor LLM local quedó entre 13,5 y 15,2 puntos bajo los encoders "
              "en enfermedad, 14,3 bajo el encoder español en medicamento y cerca de 25 en abreviatura, con "
              "diferencias significativas contra cada semilla de E1. El problema fue la precisión: Qwen con "
              "ejemplos dinámicos encontró el 71 % de las enfermedades, pero solo el 62 % de lo que marcó "
              "era correcto. Su F1 laxo en enfermedad (0,793) quedó 13 puntos sobre el estricto, contra 10 "
              "en los encoders.")
    d.parrafo("Los LLM comerciales redujeron la diferencia, pero solo la cerraron en una entidad. GPT-5.2 "
              "con ejemplos dinámicos llegó a 0,727 en enfermedad y 0,887 en abreviatura, y casi no inventó "
              "menciones (0,4 %). Gemini 3.1 Pro llegó a 0,717 y 0,901, y empató con el encoder en "
              "medicamento (0,844 contra 0,840, sin diferencia significativa). Contra E1, Gemini quedó entre "
              "7 y 11 puntos abajo en enfermedad y entre 4 y 5 en abreviatura, con diferencias "
              "significativas en las tres semillas. Su recall en enfermedad (0,839) igualó al del encoder "
              "chileno, pero su precisión fue de 0,626. Correr las 990 oraciones con ambas estrategias costó "
              "4,26 dólares con GPT-5.2 y 4,46 con Gemini (Tabla IV).")
    d.cap_tabla("IV", "Confiabilidad y costo de los LLM con *few-shot* dinámico")
    d.tabla(["Modelo", "Alucin.", "JSON inv.", "s/oración", "USD"],
            [["Llama 3.1 8B (local)", "19,4 %", "3", "2,1", "0"],
             ["Qwen 2.5 7B (local)", "5,2 %", "0", "1,6", "0"],
             ["GPT-5.2 (API)", "0,4 %", "0", "2,0", "2,52"],
             ["Gemini 3.1 Pro (API)", "14,2 %", "3", "4,2", "2,54"]],
            [1650, 700, 700, 800, 600],
            notas=["Alucin.: menciones devueltas que no aparecen en la oración. USD: costo de las 990 "
                   "oraciones. Tiempos locales en un Mac M5 de 24 GB."])

    d.h2("E", "Estudios de simulación: abreviaturas y escala del encoder")
    d.parrafo("Los LLM reconocieron peor las enfermedades escritas con abreviatura. Con ejemplos dinámicos, el "
              "recall en enfermedades con y sin abreviatura fue 0,655 y 0,764 en Llama, 0,647 y 0,723 en "
              "Qwen, 0,748 y 0,804 en GPT-5.2, y 0,824 y 0,841 en Gemini. El encoder chileno no tuvo esa "
              "brecha (0,843 y 0,835); el español sí, aunque más chica (0,790 y 0,816). H3 se cumple en "
              "enfermedad, y es el resultado que más apoya la adaptación al texto local: en enfermedades "
              "abreviadas, el encoder chileno superó al español por 5,3 puntos (n = 119). En la entidad "
              "abreviatura, los LLM locales no aprendieron por sí solos las convenciones del corpus, como "
              "anotar “APS” o “+” como abreviaturas, y quedaron 25 a 31 puntos abajo; los comerciales las "
              "tomaron mejor de los ejemplos y quedaron a 5 o 6 puntos.", sangria=False)
    d.parrafo("RigoBERTa Clinical tiene 4,5 veces más parámetros que los encoders base y se preentrenó con "
              "el corpus clínico abierto más grande en español [@subies2025]. Aun así, no los superó en "
              "ninguna entidad: en enfermedad empató con el español y perdió contra el chileno en dos de tres "
              "semillas, y en medicamento quedó bajo el español en las tres. Solo en las 66 abreviaturas que "
              "nunca aparecen en entrenamiento tuvo un recall mayor (0,662, contra 0,601 y 0,606), aunque el "
              "subgrupo es chico. En este corpus importó más que el modelo hubiera visto derivaciones "
              "chilenas que su tamaño, y entrenar el modelo *large* exigió una GPU de 80 GB.")

    d.h2("F", "Estudios de simulación: destilación con un LLM anotador (E4)")
    d.parrafo("La Fig. 5 muestra la curva de E4. En enfermedad y abreviatura, el alumno superó a su maestro: "
              "con 50 oraciones *gold*, el encoder entrenado con las etiquetas de Qwen llegó a 0,644 en "
              "enfermedad, y esas mismas etiquetas tenían 0,586. Las etiquetas *silver* ayudaron cuando había "
              "poco *gold*: con 10 oraciones anotadas, el alumno llegó a 0,571 en enfermedad, y el modelo "
              "entrenado solo con esas 10 oraciones, a 0,278. Entre 50 y 100 oraciones la curva se aplanó "
              "(de 0,644 a 0,650).", sangria=False)

    def fig_e4():
        d.fig_inline(FIG / "fig_destilacion_e4.png", 5,
                     "Destilación (E4): F1 estricto medio de tres semillas según las oraciones *gold* "
                     "disponibles. El maestro es Qwen 2.5 7B; su F1 se mide contra el *gold* de las 2.000 "
                     "oraciones que etiquetó. En medicamento, con N = 0, 10 y 50, una semilla del alumno "
                     "colapsó y no marcó ninguna entidad; la media incluye esa semilla.", PAG)
    d.ancho_completo(fig_e4)

    d.parrafo("H4 no se cumplió. Con 50 oraciones *gold*, el alumno quedó entre 15 y 17 puntos bajo E1 en "
              "enfermedad, 23 en medicamento (con las dos semillas que no colapsaron) y 36 en abreviatura. "
              "En abreviatura, las etiquetas *silver* incluso empeoraron el resultado: con 100 oraciones, "
              "entrenar solo con *gold* dio 0,729, y agregar *silver* lo bajó a 0,634. El maestro tuvo ahí "
              "precisión alta (0,90) y recall bajo (0,49), porque no conocía las convenciones del corpus, y "
              "el alumno heredó ese sesgo. En medicamento, una semilla colapsó con F1 0, la inestabilidad "
              "del ajuste fino en clases poco frecuentes que describen Dodge et al. y Mosbach et al. "
              "[@dodge2020,mosbach2021]. E4 deja, eso sí, un dato útil: con 100 oraciones anotadas, el "
              "alumno llegó en enfermedad a 0,650, casi lo mismo que el LLM local con ejemplos dinámicos "
              "(0,663), que en cambio necesita las 8.014 oraciones de entrenamiento para buscar ejemplos.")

    d.h2("G", "Estudios de simulación: análisis de errores y votación")
    d.parrafo("Con ejemplos dinámicos, los LLM comerciales acertaron casi tantas enfermedades exactas como el "
              "encoder: 899 Gemini y 854 GPT-5.2, contra 895 del encoder chileno (Fig. 6). La diferencia de "
              "F1 estuvo en las predicciones espurias: 112 del encoder chileno, 286 de GPT-5.2, 406 de Gemini "
              "con ejemplos y 636 sin ellos. Según el sistema, entre el 67 % y el 93 % de las espurias se "
              "superpuso con un hallazgo anotado, como “dolor”, “vómitos” o “mordida invertida”. La guía del "
              "CWLC separa el hallazgo (un signo o síntoma) de la enfermedad, y los LLM no siguieron esa "
              "separación aunque la guía estaba en el prompt. Parte del error de los LLM es un desacuerdo de "
              "criterio con la anotación.", sangria=False)
    d.fig_inline(FIG / "fig_tipologia_errores.png", 6,
                 "Tipología de las predicciones de enfermedad en el test (semilla 42 para E1). “Espuria sobre "
                 "un hallazgo”: predicción que no coincide con ninguna enfermedad del *gold* y que se "
                 "superpone con un hallazgo anotado.", COL)
    d.parrafo("En dos subgrupos, los LLM comerciales fueron mejores (Fig. 7). En las 31 enfermedades mal "
              "escritas, el recall de los encoders bajó de 0,82 o 0,84 a entre 0,52 y 0,56, mientras Gemini "
              "sin ejemplos se mantuvo en 0,77; la diferencia fue significativa en tres de las seis "
              "comparaciones pareadas. La tokenización ayuda a entenderlo: para el encoder, “furosemida” es "
              "una sola pieza, y “FUSROSEMIDA” son cinco que nunca vio juntas [@moradi2021]. En las 66 "
              "abreviaturas nunca vistas, los encoders base llegaron a 0,60 y los LLM comerciales a entre "
              "0,71 y 0,76, mientras que en las 774 abreviaturas frecuentes los encoders llegaron a entre "
              "0,97 y 0,99. El encoder reconoce casi siempre la jerga que vio en entrenamiento; la que no "
              "vio, los LLM grandes la deducen mejor.")
    d.fig_inline(FIG / "fig_subgrupos_recall.png", 7,
                 "Recall estricto por subgrupo. Encoders: media de tres semillas. Las palabras mal escritas "
                 "se detectaron con diccionario y distancia de edición y se revisaron a mano.", COL)
    d.parrafo("Como cada tipo de modelo acierta en casos distintos, probamos combinarlos. Juntando las "
              "enfermedades que encuentra el encoder con las de un LLM, el recall llega a entre 0,87 y 0,92, "
              "contra 0,81 a 0,84 del encoder solo. Pero las tres combinaciones simples que probamos (la "
              "unión, agregar solo las predicciones del LLM que no chocan con las del encoder, y agregar "
              "solo las que caen en palabras que el encoder nunca vio) empeoraron el F1 en enfermedad, "
              "porque cada acierto del LLM llega con varios falsos positivos.")
    d.parrafo("Combinar semillas rindió más que agrandar el modelo. La votación de los seis encoders base "
              "llegó a 0,837 en enfermedad (IC 95 % de 0,815 a 0,857), con precisión de 0,862 y recall de "
              "0,813, y superó a cada uno de los seis modelos por 1,3 a 4,5 puntos, con diferencias "
              "significativas. Es el mejor resultado del estudio en esa entidad. En abreviatura llegó a "
              "0,957 y en medicamento a 0,831, sin diferencias significativas. Con nueve modelos (sumando "
              "RigoBERTa), enfermedad quedó en 0,838 y ya no fue mejor que todos los modelos individuales.")

    d.h2("H", "Discusión: hipótesis y limitaciones")
    d.parrafo("La Tabla V resume las hipótesis. En las derivaciones chilenas se repitió lo que reporta la "
              "literatura: el encoder ajustado gana y los ejemplos dinámicos ayudan. Hubo dos sorpresas. La "
              "destilación quedó mucho más lejos del encoder de lo esperado, y un LLM comercial empató con el "
              "encoder en medicamento.", sangria=False)
    d.cap_tabla("V", "Resultado de las hipótesis")
    d.tabla(["", "Resultado", "Evidencia"],
            [["H1", "Apoyada", "Mayor F1 en enfermedad y abreviatura; en medicamento, empate con Gemini dinámico"],
             ["H2", "Apoyada", "Dinámico > *zero-shot* en los cuatro LLM y > fijo en los dos locales"],
             ["H3", "Apoyada en enfermedad", "Los cuatro LLM tienen menor recall en enfermedades "
              "abreviadas; el encoder chileno no tiene esa brecha"],
             ["H4", "No apoyada", "Con 50 *gold*, 15 a 36 puntos bajo E1"],
             ["H5", "Apoyada en 2 de 3", "Los LLM comerciales quedan bajo E1 en enfermedad y abreviatura; "
              "Gemini empata en medicamento"]],
            [450, 1100, 3100], alin=["left", "left", "left"])
    d.parrafo("El estudio tiene limitaciones. Una derivación es un texto corto, escrito para justificar una "
              "interconsulta, y los resultados podrían cambiar en las evoluciones o los planes de cuidado de "
              "una ficha de CESFAM. Hoy no existe en Chile un corpus público de ese tipo. Hay riesgo de "
              "contaminación: el encoder chileno se preentrenó con derivaciones de la lista de espera, sin "
              "que se publique cuáles, y los LLM comerciales pudieron ver el CWLC, público desde 2022. Si eso "
              "pasó, sus resultados son un techo optimista.")
    d.parrafo("Corrimos los LLM una vez por estrategia. Con temperatura 0 la variación debería ser baja, "
              "pero no la medimos, y Gemini estaba en versión preliminar. Por tiempo, no evaluamos el ajuste "
              "fino de un LLM con LoRA ni la normalización previa de abreviaturas. Por último, la distinción "
              "entre hallazgo y enfermedad de la guía del CWLC penaliza a los LLM, y con otra guía esa parte "
              "del resultado podría cambiar.")

    # ------------------------------------------------------------------ IV
    d.h1("IV", "Conclusiones")
    d.parrafo("Con derivaciones reales de APS chilena, un encoder ajustado con datos anotados reconoció "
              "enfermedades, medicamentos y abreviaturas mejor que un LLM generativo con prompting, como "
              "reporta la literatura internacional. El encoder adaptado a derivaciones chilenas tuvo el mejor "
              "F1 individual en enfermedad (0,815), y la votación de seis encoders base subió esa cifra a "
              "0,837. Un encoder 4,5 veces más grande no mejoró el resultado. Los ejemplos recuperados por "
              "similitud mejoraron a todos los LLM, pero los locales de 7 y 8B siguieron entre 13 y 25 puntos "
              "abajo, y la destilación con 50 oraciones anotadas quedó lejos del encoder.", sangria=False)
    d.parrafo("Los LLM comerciales reconocieron mejor que el encoder las palabras mal escritas y las "
              "abreviaturas que nunca aparecieron en entrenamiento. A cambio, marcaron muchos hallazgos como "
              "enfermedades, y para usarlos hay que enviar el texto a un servicio externo.")
    d.parrafo("Si un CESFAM tiene texto anotado, la opción más precisa es un encoder base ajustado con "
              "texto local, o una votación de varios: corre en un computador común y no saca datos del "
              "centro. Si no lo tiene, le conviene anotar algunos cientos de "
              "oraciones con criterio clínico antes que confiar en etiquetas generadas por un LLM local.")
    d.parrafo("Quedan tres líneas de trabajo futuro: un sistema híbrido que use la confianza del encoder para "
              "decidir cuándo consultar al LLM; la validación en evoluciones y planes de cuidado de CESFAM, "
              "que es el objetivo de la tesis doctoral del primer autor, y el texto escrito por pacientes, "
              "con lenguaje coloquial y ruido de mensajería.")

    d.h1(None, "Disponibilidad de código y datos")
    d.parrafo("El código, los prompts, las configuraciones y los resultados están en "
              "https://github.com/SebasDCIS/proyecto-ner-aps-genai. El CWLC está disponible en Zenodo "
              "(registro 5591011) bajo licencia CC BY-NC-SA 4.0. Usamos herramientas de IA como apoyo en la "
              "programación y en la edición del texto.", sangria=False)
