# Bitácora del proyecto

Registro de decisiones, avances y pendientes. Cada entrada responde tres preguntas: qué se decidió, por qué y qué queda abierto. La más reciente va primero.

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
- [ ] Fijar la versión del CWLC y los splits (ver `docs/verificacion_arranque.md`)
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
