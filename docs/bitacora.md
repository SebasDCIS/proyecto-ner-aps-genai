# Bitácora del proyecto

Registro de decisiones, avances y pendientes. Cada entrada responde tres preguntas: qué se decidió, por qué y qué queda abierto. La más reciente va primero.

---

## 2026-11-06 (tarde) · Resultados de RigoBERTa Clinical (E1 con encoder *large*)

Se entrenó en Colab con una GPU A100 (80 GB), con lote 16 sin acumulación: los mismos hiperparámetros de E1, salvo la lr de 2×10⁻⁵. Código del commit `2d5dfc9`, datos con huellas verificadas. Unos 11 minutos por entrenamiento.

| Entidad | RigoBERTa (media ± DE, 3 semillas) | E1 español clínico | E1 chileno clínico |
|---|---|---|---|
| Disease | 0,803 ± 0,004 | 0,798 | 0,815 |
| Medication | 0,780 ± 0,015 | 0,840 | 0,794 |
| Abbreviation | 0,946 ± 0,013 | 0,950 | 0,952 |

- **Lectura preliminar:** un modelo 4,5 veces más grande, preentrenado con el mayor corpus clínico en español, **no supera** al encoder base adaptado con derivaciones chilenas. Queda en Disease entre los dos encoders de E1, y bajo ambos en Medication y Abbreviation. Para este corpus pesa más el dominio local del preentrenamiento que la escala.
- Medication tiene pocas menciones en el test (92), así que su IC es ancho: [0,66–0,85] con la semilla 42.
- **Comparación pareada por semilla** (bootstrap, mismas oraciones; * = significativa):
  - Disease: RigoBERTa empata con el español clínico (+0,003 a +0,008, ninguna significativa). Contra el chileno clínico pierde en 2 de 3 semillas (−0,018* y −0,019*; la otra empata).
  - Medication: queda bajo el español clínico (−0,039 a −0,088; significativa en 1 de 3 semillas). Contra el chileno no hay diferencia significativa.
  - Abbreviation: empata salvo con la semilla 42, que pierde contra ambos (−0,018* y −0,020*).
  - Conclusión: RigoBERTa no supera de forma robusta (en las 3 semillas) a ningún encoder de E1, en ninguna entidad.
- **Un matiz:** en abreviaturas que no aparecen en train (66 menciones) RigoBERTa tiene mejor recall: 0,662, contra 0,601 del chileno y 0,606 del español. Es coherente con un preentrenamiento clínico más amplio, pero es un subgrupo chico.
- **Votación con 9 modelos** (3 semillas × 3 encoders, 5 de 9 votos): Disease 0,838 [0,818–0,860], prácticamente igual que con 6 modelos (0,837). Ya no es significativa contra todos los modelos individuales. Abbreviation 0,956, Medication 0,829. Sumar RigoBERTa no aporta: la ganancia de la votación viene de combinar semillas y los dos encoders base.

---

## 2026-11-06 · Votación entre modelos y encoder más grande

- **Votación (notebook 05, sección 7):** se formalizó la combinación por mayoría estricta, con la regla fijada antes de mirar el test (gana una entidad si la predicen al menos n//2+1 modelos). Con 6 modelos (3 semillas de cada encoder de E1) y 4 votos, Disease llega a F1 estricto 0,837 [0,815–0,857] (P 0,86, R 0,81), significativamente mejor que cada modelo por separado. En Abbreviation queda en 0,957, y en Medication en 0,832 (diferencia no significativa). Función `votacion()` en `src/analisis/errores.py`, con su prueba.
- **Encoder grande (notebook 02b):** se preparó E1 con RigoBERTa Clinical (XLM-RoBERTa *large*, ~560 M de parámetros, preentrenado con ClinText-SP). Licencia no comercial: sirve para investigación, no para un producto.
  - Cambio declarado: tasa de aprendizaje 2×10⁻⁵ (en vez de 3×10⁻⁵), por estabilidad en modelos *large*. Lo demás es igual que en E1.
  - Prueba de humo en la nube: tokenizador, alineación de etiquetas (0 oraciones desalineadas en 500), paso hacia adelante y hacia atrás, y predicción funcionan. El paso del optimizador no se probó, porque AdamW necesita unos 10 GB y la nube tiene 7 GB. Se corre en el Mac.
- **Por qué:** la votación muestra que la variabilidad entre semillas se puede aprovechar en vez de solo reportarla. El encoder grande responde si el techo de E1 sube con más escala y más preentrenamiento clínico.

**Pendiente**
- [ ] Correr el notebook 02b en el Mac (primero `rapido`, después `completo`; unas 9–10 h).
- [ ] Volver a correr el notebook 05 para sumar RigoBERTa a las tablas y a la votación.

**Actualización 06-11, mañana.** La primera corrida completa (lote 16) no terminó ni una época en 7,5 h. La causa probable es la memoria: el modelo *large* con lote 16 llena la memoria unificada del Mac y el sistema pasa a usar disco (*swap*). Cambios:
- Se agregó acumulación de gradientes (`Config.acumular`): lote 8 × 2 = lote efectivo 16, el mismo hiperparámetro de E1. Hay una diferencia menor: la pérdida se promedia por medio lote. Queda declarada.
- Se agregó un registro de velocidad dentro de la época (segundos por lote y minutos restantes).
- E1 no cambia: con `acumular=1` el código hace exactamente lo mismo.

**Actualización 06-11, 11:15.** Con lote 8 × 2 el Mac igual se frenó: 2 s por lote al comienzo, 8,6 s de promedio a los 100 lotes, más de 2 h por época. Se decidió entrenar en una GPU de Google Colab con el notebook `02c_e1_rigoberta_colab.ipynb`. Es el mismo código, clonado del repositorio, con los mismos datos (huellas verificadas) y los mismos hiperparámetros: lote 16 sin acumulación, igual que E1. Lo único que cambia es el hardware, que queda registrado en `resultados.hardware` y en la huella del entorno. Hallazgo práctico para el informe: un encoder *large* no se puede ajustar en un computador personal (Mac M5 de 24 GB). Un CESFAM necesitaría GPU o un servicio externo.

---

## 2026-11-02 · Lote manual de Gemini desde el entorno Linux del puente

Para adelantar la corrida, a las 06:18 se lanzó `scripts/correr_nube.py` desde el entorno Linux que accede a la carpeta del proyecto en el Mac (misma carpeta, misma caché, mismo código y parámetros). Se instaló `openai==3.37.0`, la misma versión del `.venv` del Mac (con 3.42 el mensaje de error 400 no traía el detalle y fallaba el reintento sin `seed`), y se usaron stubs de `torch`/`transformers` fuera del repositorio, porque el script solo importa `evaluar()` de E1. El proceso se cerró al terminar la llamada del puente: aportó 26 oraciones (494 → 520) de Gemini con ejemplos parecidos. Esas 26 respuestas tienen el campo `fecha` en UTC (las demás, en hora de Chile). La tarea diaria de las 07:00 continúa desde ahí.

---

## 2026-11-01 · Notebook 05: análisis de errores, y una idea que queda para un estudio aparte

**Qué se hizo.** Notebook 05 y `src/analisis/errores.py`. No entrena ni consulta modelos: reutiliza las predicciones guardadas (E1: 2 encoders × 3 semillas; E2 y nube: las corridas completas). Incluye tipología de errores, palabras mal escritas reales del corpus, menciones vistas vs nuevas, abreviaturas por frecuencia en train y cruce encoder × LLM con tres híbridos simples. Resultados (solo números) en `results/e5_analisis/analisis_errores.json`. Gemini con ejemplos parecidos entra cuando termine (3 de noviembre).

**Hallazgos (primera lectura):**
- Los LLM aciertan casi lo mismo que E1 en Enfermedad (GPT-5.2 con ejemplos: 854 exactas vs 895 del encoder chileno s42), pero tienen muchas más espurias (286 vs 112; Gemini sin ejemplos 636). Entre 67% y 88% de las espurias de todos los sistemas caen sobre un hallazgo (*Finding*) anotado: "dolor", "vómitos", "mordida invertida". Diferencia de criterio con la guía del corpus.
- Palabras mal escritas: heurística (diccionario de español + vocabulario de train + distancia de edición 1–2), revisada a mano. 31 enfermedades y 5 medicamentos en el test. Recall en enfermedades mal escritas: E1 ~0,52–0,56 (vs 0,82–0,84 bien escritas); Gemini 0,77 (vs 0,79). Pareado sobre las mismas 31: Gemini − encoder = +0,19 a +0,32 (IC con límite inferior en 0 o apenas sobre 0); GPT-5.2 con ejemplos +0,10 a +0,23, no significativo. Explicación: "furosemida" es 1 token, "FUSROSEMIDA" son 5 piezas.
- Abreviaturas nunca vistas en train (66): E1 0,60, GPT-5.2 con ejemplos 0,71, Gemini 0,76; frecuentes (774): E1 0,98. El encoder memoriza la jerga; los LLM grandes deducen mejor la nueva.
- Recall oráculo encoder ∪ LLM en Enfermedad: 0,90–0,92 (vs 0,84). Pero unión, rescate y rescate dirigido a palabras desconocidas empeoran el F1 (significativo en Enfermedad), porque lo que aporta el LLM viene con muchos falsos positivos. Un híbrido útil necesitaría confianza del encoder o un paso de verificación.
- Decisión: no se implementa una corrección en este proyecto, porque los errores ortográficos son el 3% de las enfermedades. Recomendación para implementación: reentrenar con aumento de datos (errores simulados), con evidencia en Moradi y Samwald 2022.

**Idea futura (fuera de este proyecto): texto escrito por pacientes.** Se discutió medir cómo rinden los modelos con lenguaje de paciente (un chatbot), lo que el CWLC no permite porque lo escriben profesionales. Quedó diseñado, pero se dejó para un estudio aparte porque cambia la pregunta del proyecto:
- Cuatro versiones de cada oración del test: C0 original, C1 vocabulario de paciente ("HTA" → "presión alta", "caries profunda" → "muela picada"), C2 ruido de chat (minúsculas, sin tildes, emojis, "xq", errores de tipeo), C3 ambas. La respuesta correcta se recalcula sola porque el cambio es por reglas; solo se reemplaza cuando la entidad completa calza con la lista.
- Lista de equivalencias en borrador: cubre 237 oraciones del test, 316 enfermedades y 32 medicamentos. Requiere revisión con criterio clínico (casos dudosos: "el azúcar", "sobrepeso", "la pastilla de la presión").
- Hipótesis: el encoder caería más que los LLM (Moradi y Samwald 2021; Singh et al. 2024; Kim et al. 2025).
- Antecedente chileno: Dunstan et al. 2024 (modelo entrenado en lista de espera aplicado a anamnesis de la ACHS; corpus disponible a solicitud). Validación externa posible con SocialDisNER (tweets en español con enfermedades).
- Lo ideal sería complementarlo con mensajes reales, con aprobación de un comité de ética.

---

## 2026-10-27 (noche) · Estado del proyecto: resumen

**F1 estricto en el test completo (990 oraciones)**

| Sistema | Disease | Medication | Abbreviation |
|---|---|---|---|
| E1 · encoder español ajustado (8.014 gold, 3 semillas) | 0,798 | 0,840 | 0,950 |
| E1 · encoder chileno ajustado | 0,815 | 0,794 | 0,952 |
| E2 · LLM local, zero-shot (llama / qwen) | 0,446 / 0,537 | 0,451 / 0,589 | 0,524 / 0,516 |
| E2 · LLM local, few-shot dinámico (llama / qwen) | 0,650 / 0,663 | 0,697 / 0,670 | 0,703 / 0,642 |
| E2 nube · GPT-5.2 zero-shot | 0,645 | 0,768 | 0,776 |
| E2 nube · GPT-5.2 few-shot dinámico | 0,727 | 0,772 | 0,887 |
| E4 · silver (qwen) + 50 gold | 0,644 | 0,610* | 0,592 |
| E4 · silver (qwen) + 100 gold | 0,650 | 0,674 | 0,634 |

\* Media de 2 semillas; la tercera colapsó (ver entrada de E4).

**Hipótesis:** H1 apoyada · H2 apoyada · H3 apoyada en Disease · H4 no apoyada · H5 apoyada con GPT-5.2 (falta Gemini).

**En curso:** Gemini 3.1 Pro en el test completo, ~250 consultas por día (tarea diaria con launchd a las 07:00; 237/990 zero-shot hechas el 27-10).

**Pendientes:** terminar Gemini · validar con el prof. Salas y confirmar la fecha de entrega · informe final (TRIPOD-LLM).

**Documentos:** guía completa y guía de estudio del grupo (Claude Docs); página del proyecto en Notion (Doctorado › Segundo semestre › Electivo IA Generativa).

---

## 2026-10-27 (tarde) · Techo de referencia: GPT-5.2 (y Gemini, en curso)

**GPT-5.2** (OpenAI, esfuerzo de razonamiento bajo; no acepta temperatura, se omitió y quedó registrado), test completo, costo total USD 4,26, ~2 s por oración:

| Entidad | GPT-5.2 zero-shot | GPT-5.2 dinámico | Mejor LLM local | E1 español / chileno |
|---|---|---|---|---|
| Disease | 0,645 | **0,727** | 0,663 | 0,798 / 0,815 |
| Medication | 0,768 | **0,772** | 0,697 | 0,840 / 0,794 |
| Abbreviation | 0,776 | **0,887** | 0,703 | 0,950 / 0,952 |

- **H5 apoyada:** el modelo grande achica la brecha (de 13–31 puntos con los LLM locales a 6–8), pero no supera a E1. Bootstrap pareado contra cada semilla de E1 español: diferencias significativas en Disease y Abbreviation en las 3 semillas; en Medication solo en 1 de 3.
- El few-shot dinámico también ayuda al modelo grande: +8 puntos en Disease y +11 en Abbreviation.
- Casi no alucina (0,4–1%) y no tuvo ningún JSON inválido.
- Sin duplicados baja ~1 punto. Posible contaminación (corpus público desde 2022): se declara.

**Gemini 3.1 Pro** (`gemini-3.1-pro-preview`): el nivel de pago inicial (Tier 1) permite 250 consultas por día por modelo. Se alcanzó tras 237 oraciones zero-shot. Decisión (revisada el mismo día): correr Gemini sobre el **test completo**, igual que GPT-5.2, para comparar las dos familias de LLM en igualdad. Toma ~8 días con la cuota diaria. `scripts/correr_nube.py` avanza las corridas desde la terminal y `scripts/instalar_tarea_diaria.sh` lo programa con launchd todos los días a las 07:00. Como `gemini-3.1-pro-preview` puede cambiar de versión en esos días, cada respuesta registra la versión que la produjo y la fecha; el JSON final resume las versiones servidas y el período. Las respuestas de GPT-5.2 (en ~1 hora) se obtuvieron antes de registrar la versión.

---

## 2026-10-27 · Resultados de E4 completo (2.000 silver, 3 entidades, 3 semillas)

Anotación con qwen2.5:7b (~3,4 h) + 63 entrenamientos (~3,3 h). Todos con al menos 300 actualizaciones; sin dev para elegir la época.

**F1 estricto en test (media de 3 semillas)**

| Entidad | N gold | Maestro (silver) | Silver + gold | Solo gold | E1 (8.014 gold) |
|---|---|---|---|---|---|
| Disease | 0 | 0,532 | 0,561 | — | 0,798 |
| Disease | 10 | 0,524 | 0,571 | 0,278 | |
| Disease | 50 | 0,586 | **0,644** | 0,489 | |
| Disease | 100 | 0,595 | **0,650** | 0,595 | |
| Medication* | 0 | 0,662 | 0,661 | — | 0,840 |
| Medication* | 10 | 0,663 | 0,587 | 0,000 | |
| Medication* | 50 | 0,660 | 0,610 | 0,465 | |
| Medication | 100 | 0,687 | **0,674** | 0,497 | |
| Abbreviation | 0 | 0,526 | 0,527 | — | 0,950 |
| Abbreviation | 10 | 0,496 | 0,555 | 0,353 | |
| Abbreviation | 50 | 0,547 | 0,592 | 0,616 | |
| Abbreviation | 100 | 0,550 | 0,634 | **0,729** | |

\* En Medication con N = 0, 10 y 50, la semilla 43 colapsó: el modelo aprendió a no marcar nada (F1 0, pérdida estancada en ~0,03). La tabla muestra la media de las semillas 42 y 44; con las 3 semillas las medias son 0,441 / 0,391 / 0,406. Es la inestabilidad de ajuste fino descrita por Dodge et al. (2020) y Mosbach et al. (2021) en clases poco frecuentes. Se reporta, no se oculta.

**Hallazgos**
- **El alumno supera al maestro en Disease y Abbreviation** (Disease N = 50: 0,644 frente a 0,586) y lo iguala en Medication.
- **El silver ayuda cuando hay poco gold:** en Disease, con 10 oraciones gold, 0,57 frente a 0,28; con 50, 0,64 frente a 0,49. La curva se aplana entre 50 y 100 (0,644 → 0,650).
- **Pero el silver puede estorbar:** en Abbreviation con 50–100 gold, entrenar solo con gold gana (0,73 frente a 0,63). El maestro tiene precisión alta (0,90) y recall bajo (0,49), porque no conoce las convenciones del corpus (APS, "+", unidades), y el alumno hereda ese sesgo.
- **H4 no se cumple en este corpus:** con 50 gold, el alumno queda 15–16 puntos bajo E1 en Disease, 23 en Medication y 36 en Abbreviation. En inglés el maestro rendía ~0,82; aquí, 0,53–0,69. El techo lo pone la calidad del maestro.
- **Resultado práctico:** con 100 oraciones gold y sin LLM al momento de usarlo, el alumno de Disease (0,65) iguala al LLM directo con few-shot dinámico (0,66), que necesitó las 8.014 oraciones de train para buscar ejemplos y corre mucho más lento.

**Pendientes**
- [ ] Techo de referencia con LLM de nube (notebook 03b)
- [ ] Informe final

---

## 2026-10-26 (noche) · E4 modo rápido con 300 actualizaciones mínimas

Solo Disease, 200 oraciones silver, 1 semilla; evaluado en el test completo (990 oraciones).

| N gold | Maestro (silver vs anotación real) | Alumno silver + gold | Solo gold |
|---|---|---|---|
| 0 | 0,53 | 0,51 | — |
| 10 | 0,49 | **0,59** | 0,31 |
| 50 | 0,57 | 0,61 | 0,51 |
| 100 | 0,57 | **0,63** | 0,61 |

- Con la corrección, todos los modelos aprenden (pérdida final < 0,01).
- **El alumno supera al maestro** desde N = 10 (0,59 vs 0,49) y con N = 100 (0,63 vs 0,57).
- **El silver aporta más cuando hay poco gold:** +28 puntos con N = 10, +10 con N = 50, +3 con N = 100.
- Referencias en Disease: E2 qwen directo 0,54 (zero-shot) y 0,66 (dinámico con todo train); E1 0,80. Con solo 200 oraciones silver, el modo completo (2.000) debería subir la curva.

---

## 2026-10-26 (tarde) · E4 modo rápido: ajuste de entrenamiento

- Maestro (qwen2.5:7b sobre 200 oraciones silver), F1 en Disease: N = 0 → 0,53 (igual que E2 zero-shot); N = 10 → 0,49; N = 50 → 0,57; N = 100 → 0,57. Con ejemplos gold las alucinaciones bajan de 27% a 4–9%. Con solo 10 oraciones, los ejemplos "más parecidos" no se parecen lo suficiente y no ayudan.
- Los encoders del modo rápido dieron F1 ≈ 0 (salvo solo gold con 100 oraciones, 0,47): con 200 oraciones y 2 épocas había apenas ~26 actualizaciones de pesos, y con 10 oraciones gold, 1 actualización por época. No era un error de código, sino falta de entrenamiento, y además hacía injusta la comparación entre condiciones.
- Corrección: `Config.pasos_min` (300 en E4). Todos los modelos reciben al menos 300 actualizaciones; si tienen pocos datos, se repiten más épocas. Los resultados de entrenamiento del modo rápido se descartan; las anotaciones silver del LLM se conservan (no dependen del entrenamiento).

---

## 2026-10-26 · Techo de referencia con LLM de nube preparado

- Notebook `03b` + `crear_llamador_api` en `e2_llm.py`: el mismo prompt, guía, ejemplos y métricas de E2, con un LLM comercial vía API (OpenAI y Gemini, este último por su endpoint compatible con OpenAI). Estrategias: zero-shot y few-shot dinámico.
- Permitido porque el CWLC es público y anonimizado; con fichas reales no sería una opción directa. Riesgo de contaminación declarado (corpus público desde 2022).
- Antes de correr, prueba 5 oraciones y proyecta el costo con los tokens reales; la corrida completa exige `CONFIRMAR_GASTO = True`. Se registran tokens, costo real y los parámetros que el modelo no acepte (p. ej. temperatura en modelos de razonamiento).
- Claves en `.env` (ignorado por git). La suscripción a ChatGPT o Gemini no incluye la API: se paga aparte.
- Modelos por defecto en la config (confirmar nombre y precio vigentes): `gpt-6.1-sol` y `gemini-3.1-pro`, ambos ~USD 2 por millón de tokens de entrada. Estimado: ~USD 5 por proveedor para las 990 oraciones con las 2 estrategias.

---

## 2026-10-26 · E4 preparado

- `src/modelos/e4_destilacion.py` + notebook `04`. Gold simulado: 0/10/50/100 oraciones de train con su anotación real, anidadas (semilla 42). Silver: 2.000 oraciones de train, disjuntas del gold, anotadas por qwen2.5:7b; con N = 0 zero-shot, con N > 0 los 5 ejemplos más parecidos buscados **solo dentro del gold** (buscar en todo train sería fuga).
- Encoder `bsc-bio-ehr-es` (sin riesgo de contaminación), 3 semillas. Sin dev para elegir la época (no existiría en el escenario simulado): se agregó `Config.seleccion = "ultima"` al entrenador de E1.
- Dos condiciones: silver + gold, y solo gold. Calidad del "maestro" medida contra la anotación real de las oraciones silver. Referencias: E1 (8.014 gold) y E2 (qwen directo en el test).
- Estimado del modo completo: ~3,4 h de anotación + ~3 h de entrenamientos.

**Pendientes**
- [ ] Correr el notebook 04 en modo rápido y luego completo

---

## 2026-10-26 · Resultados de E2 (test completo, 990 oraciones)

Corrida nocturna en el Mac: 9.900 llamadas en ~4,4 h (1,1–3,1 s por oración; la más lenta 47 s, el tope de tokens funcionó). Digests: llama3.1:8b `46e0c10c039e`, qwen2.5:7b `845dbda0ea48`.

**F1 estricto (few-shot fijo = media de 3 sets de ejemplos)**

| Entidad | Zero-shot llama / qwen | Fijo llama / qwen | Dinámico llama / qwen | E1 español / chileno |
|---|---|---|---|---|
| Disease | 0,446 / 0,537 | 0,526 / 0,560 | 0,650 / **0,663** | 0,798 / 0,815 |
| Medication | 0,451 / 0,589 | 0,393 / 0,617 | **0,697** / 0,670 | 0,840 / 0,794 |
| Abbreviation | 0,524 / 0,516 | 0,603 / 0,554 | **0,703** / 0,642 | 0,950 / 0,952 |

**Hallazgos**
- **Brecha con E1:** con la mejor estrategia, los LLM quedan 13–15 puntos bajo E1 en Disease, 14–18 en Medication y 25–31 en Abbreviation (bootstrap pareado contra cada semilla de E1: todas las diferencias significativas). En Disease la brecha está en el extremo alto de lo que reporta la literatura (3–15). La muestra de 100 oraciones la había subestimado (8–10 puntos).
- **Few-shot dinámico > fijo:** +12 puntos en Disease y +8–10 en Abbreviation (significativo); en Medication +31 en llama y no significativo en qwen. Sin duplicados baja solo ~1,5 puntos: la ventaja no viene de copiar oraciones repetidas.
- **Los LLM no generalizan mejor que E1:** recall en enfermedades nuevas 0,56–0,60 frente a 0,70–0,73 de E1. La señal contraria del modo rápido era ruido (n = 34).
- **También sufren con las abreviaturas:** recall en enfermedades abreviadas 0,65 frente a 0,72–0,76 en no abreviadas. E1 chileno no tenía esa brecha.
- **Muchos errores son de límites:** Disease con qwen dinámico 0,66 estricto frente a 0,79 laxo (13 puntos; en E1 eran 10). La precisión es el punto débil (0,57–0,62 en Disease).
- **Alucinaciones y formato:** qwen dinámico inventa el 5% de las menciones y no rompió ningún JSON; llama dinámico, el 19%. llama zero-shot inventa el 52% y dejó 22 JSON inválidos. qwen es más confiable; llama gana en Abbreviation y Medication con dinámico.
- Variación entre sets de ejemplos fijos: DE 0,02–0,05 en Disease y Medication.

**Interpretación**
Sin entrenamiento, un LLM local de 7–8B con guía y ejemplos recuperados alcanza ~80% del F1 del encoder ajustado en enfermedades y fármacos, pero no reemplaza a E1 en NER estricto. Su fortaleza no es generalizar a menciones nuevas. Esto refuerza E4: usar el LLM para pre-anotar y entrenar un encoder, en vez de usarlo directamente.

**Pendientes**
- [ ] Subir `results/e2_completo/*.json` desde el Mac
- [ ] E4: LLM como anotador + 0/10/50/100 documentos gold

---

## 2026-10-25 (noche, 2) · E2 modo rápido (100 oraciones del test, semilla 42)

- Primera corrida sin tope de generación: 4 respuestas entraron en bucle de repetición (35–70 min cada una). Se agregó `num_predict = 2048` y rescate de JSON cortado, y se repitió todo. Con tope, 1,0–3,9 s por oración.
- **Disease (n = 112), F1 estricto:** zero-shot 0,45 (llama) / 0,50 (qwen); few-shot fijo 0,54 / 0,54 (DE 0,02 entre sets de ejemplos); few-shot dinámico **0,68 / 0,70**. E1 en las mismas 100 oraciones: 0,77 (español) / 0,80 (chileno). Brecha de 8–10 puntos con la mejor estrategia, dentro de lo que reporta la literatura (3–15).
- El dinámico suma ~15 puntos sobre los ejemplos fijos. Sin duplicados baja solo ~2 puntos (0,695 → 0,676 en qwen), así que su ventaja no viene principalmente de copiar oraciones repetidas.
- **El LLM encuentra casi lo mismo que E1, pero marca de más:** recall en Disease con dinámico 0,73–0,77 (E1 0,81–0,84) y en menciones nuevas 0,68 (E1 0,70–0,73; n = 34); la diferencia está en la precisión (0,61–0,66). F1 laxo ~0,78: muchos errores son de límites.
- **Abbreviation:** los LLM quedan en 0,55–0,66 frente a 0,93 de E1. No aprenden solos las convenciones del corpus (APS, "+", unidades).
- **Alucinaciones:** llama zero-shot inventa el 54% de las menciones y produce 3 JSON inválidos; con ejemplos baja a 7–22%. qwen: 5–10% y ningún JSON inválido.
- Medication (5 menciones) y Abbreviation nuevas (3) no son interpretables en esta muestra: requieren el modo completo.
- Reproducibilidad: el few-shot dinámico de llama dio exactamente los mismos F1 en la corrida anterior y en esta (0,677 / 0,667 / 0,659).
- Tiempo estimado del modo completo: ~17 s por oración sumando las 10 corridas → ~4,6 h para las 990 oraciones.

**Pendientes**
- [ ] Correr el notebook 03 en modo completo

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
