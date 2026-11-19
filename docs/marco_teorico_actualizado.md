# Marco teórico actualizado a noviembre de 2026

Este documento resume la literatura de 2024 a 2026 que sostiene el manuscrito final, revisada en PubMed, Semantic Scholar y OpenAlex en noviembre de 2026. Sirve para entender dónde se ubica el proyecto frente al estado del arte.

## Encoders ajustados frente a LLM con prompting

La comparación base viene de Naguib, Tannier y Névéol (Findings of EMNLP 2024). Compararon 13 LLM usados con prompting y 16 modelos enmascarados ajustados en 14 corpus de NER clínico en inglés, francés y español. Los modelos ajustados ganaron en el dominio clínico en los tres idiomas. En el CWLC, con solo 100 oraciones de entrenamiento, un RoBERTa clínico superó a Llama-3-8B por 14 puntos. Chen et al. (Nature Communications 2025) mostraron lo mismo en un benchmark amplio de tareas biomédicas: en extracción de información, los modelos ajustados superan a los LLM sin ajustar.

Los trabajos de 2025 y 2026 repiten el patrón. Pan et al. (Computers, Materials & Continua 2026) compararon en español los corpus Meddocan, Meddoprof, Meddoplace y SympTEMIST: los encoders ajustados fueron los mejores en todos, y ajustar un LLM con QLoRA aportó poco por la escasez de datos por entidad. Arzideh et al. (Computers in Biology and Medicine 2025) encontraron en informes de patología y radiología que los LLM tenían alta precisión pero recall muy bajo, con F1 entre 0,18 y 0,30, contra 0,87 de los encoders. Una revisión con benchmark en portugués europeo (Elvas y Carvalho, Scientific Reports 2026) encontró que el encoder adaptado fue más preciso y entre 23 y 95 veces más rápido que Llama corrido localmente.

## El matiz: LLM ajustados

Cuando el LLM se ajusta con instrucciones, el resultado cambia. Hu et al. (JAMIA 2025, "¿estamos listos para cambiar a los LLM?") ajustaron LLaMA-2 y LLaMA-3 con 1.588 notas clínicas: superaron a BERT por cerca de 1 punto con muchos datos y por más de 7 con pocos datos o en un dataset no visto, pero corrieron hasta 28 veces más lento y con mucha más memoria. Calcina et al. (Applied Artificial Intelligence 2026) encontraron que los LLM ajustados logran mejor F1 estricto que el prompting y que BERT, aunque BERT sigue siendo mucho más rápido. Por eso la H1 del proyecto se acotó a LLM usados con prompting, y no haber probado un LLM ajustado con LoRA es una limitación.

## Elección de ejemplos y aprendizaje en contexto

Ge et al. (npj Artificial Intelligence 2026) evaluaron prompts dinámicos que recuperan los ejemplos más parecidos a cada oración en cinco corpus biomédicos: mejoraron el F1 promedio en 8,8 % con 5 ejemplos y 6,3 % con 10, y el mejor recuperador fue TF-IDF, un método por palabras como BM25. Kim et al. (Journal of Biomedical Informatics 2026) mostraron que la elección de ejemplos mueve hasta 9,4 puntos, y que con un banco de 500 ejemplos el aprendizaje en contexto con LLaMA-3.3-70B superó a RoBERTa-large ajustado. Zhang et al. (Findings of ACL 2026) mostraron que con cientos de ejemplos en el prompt (many-shot) los LLM igualan a BERT. Hu et al. (JAMIA 2024) mostraron que agregar la guía de anotación al prompt reduce la distancia con el encoder cerca de la mitad. El proyecto obtuvo +10 a +12 puntos con ejemplos dinámicos frente a fijos, en línea con esta literatura.

## Destilación con LLM anotadores

Vedula et al. (arXiv 2025) usaron GPT-4o y Gemini como maestros: el BERT destilado llegó a 0,84 en enfermedad, contra 0,89 con etiquetas humanas. Hsu y Roberts (Scientific Reports 2025) usaron un Llama-2-13B ajustado como maestro: con 50 notas anotadas quedaron cerca del sistema completo. Weng et al. (JMIR Medical Informatics 2026) encontraron, en detección de negaciones, que las etiquetas humanas siempre ganan, aunque por 2 a 4 puntos. Estos trabajos usan maestros fuertes. El maestro del proyecto fue un Qwen 2.5 de 7B sin ajustar, con F1 entre 0,50 y 0,69, y eso explica en parte por qué la destilación quedó entre 15 y 36 puntos bajo el encoder.

## Por qué los LLM no siguen la guía del corpus

Zhao y Goto (arXiv 2025) describen que los LLM no aprenden las convenciones implícitas de cada corpus biomédico y siguen con dificultad su guía de anotación. Kim, Kim y Aizawa (ACL 2026) proponen refinar la guía de forma iterativa con ejemplos corregidos para alinear al LLM. Hsu et al. (JAMIA 2026) proponen que el propio LLM sintetice la guía. En el proyecto, entre el 67 % y el 93 % de las predicciones espurias de enfermedad cayeron sobre hallazgos anotados, porque la guía del CWLC separa hallazgo (signo o síntoma) de enfermedad y los LLM no respetaron esa separación.

## Ensambles y votación

En el shared task MultiClinNER 2026, que incluyó español entre siete idiomas, el sistema BIT.UA (Jonker y Matos) obtuvo el primer lugar en cinco idiomas con un ensamble de semillas de un mismo XLM-RoBERTa large. Otros trabajos de 2026 encontraron que un ensamble homogéneo, de varias semillas de un mismo encoder, rinde más que combinar arquitecturas distintas. El proyecto llegó a la misma conclusión: la votación de seis encoders base subió enfermedad a 0,837, y agregar RigoBERTa no ayudó.

## El CWLC y el texto clínico chileno

El Chilean Waiting List Corpus (Báez et al. 2020 y 2022) sigue siendo el único corpus público chileno de derivaciones anotadas. Se usa como benchmark de NER anidado: lo emplean, por ejemplo, el modelo Bean (BMC Bioinformatics 2025) y un trabajo de 2026 sobre NER anidado en física de plasmas para probar generalización. Rojas, Bravo-Marquez y Dunstan (COLING 2022) mostraron que en este corpus un etiquetador por tipo de entidad rinde mejor que arquitecturas especiales para entidades anidadas. En la búsqueda hecha en noviembre de 2026 no aparecieron trabajos que evaluaran LLM generativos sobre el CWLC completo, que es el vacío que cubre este proyecto.

En recursos en español, RigoBERTa Clinical y el corpus ClinText-SP (García Subies et al. 2025) son los recursos abiertos más grandes para texto clínico en español. Para notas de atención primaria no estandarizadas en Cataluña, Estupiñán-Ojeda et al. (JAMIA Open 2025) mostraron que el ajuste eficiente con QLoRA queda a 0,8 puntos del ajuste completo usando un tercio menos de memoria, un argumento a favor de desplegar modelos en el propio centro.

## Contexto regulatorio

La Ley 21.719 de protección de datos personales de Chile entra en vigencia en diciembre de 2026 y restringe el envío de datos de salud a servicios externos. Esto pesa a favor de modelos que corren en los computadores del centro, como los encoders base o los LLM locales.
