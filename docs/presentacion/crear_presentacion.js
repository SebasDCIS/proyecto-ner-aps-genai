// Presentación final (15–20 min). Uso: node docs/presentacion/crear_presentacion.js
const path = require("path");
const pptxgen = require("pptxgenjs");
const React = require("react");
const ReactDOMServer = require("react-dom/server");
const sharp = require("sharp");
const fa = require("react-icons/fa");
const { applyTheme } = require("/root/.claude/skills/synced/37277f79-f1a3-4c4d-996d-36e3dcb3faa2_cc06b6d8-d097-483d-a8c4-52c8a78934af/pptx/scripts/apply_theme.js");

const DIR = __dirname;
const SALIDA = path.join(DIR, "Presentacion_NER_APS_final.pptx");

const THEME = {
  name: "NER APS",
  headFontFace: "Calibri",
  bodyFontFace: "Calibri",
  colors: {
    dk1: "1A1A1A", lt1: "FFFFFF", dk2: "14284B", lt2: "EEF2F8",
    accent1: "2A78D6", accent2: "1BAF7A", accent3: "EB6834", accent4: "6250D6",
    accent5: "D64545", accent6: "8A94A6", hlink: "2A78D6", folHlink: "6250D6",
  },
};
const HEX = { navy: "14284B", azul: "2A78D6", aqua: "1BAF7A", naranja: "EB6834", violeta: "6250D6", rojo: "D64545", gris: "8A94A6", tinte: "EEF2F8", texto: "1A1A1A", texto2: "4A5568" };

async function icono(Comp, color, size = 256) {
  const svg = ReactDOMServer.renderToStaticMarkup(React.createElement(Comp, { color: "#" + color, size: String(size) }));
  const buf = await sharp(Buffer.from(svg)).png().toBuffer();
  return "image/png;base64," + buf.toString("base64");
}

(async () => {
  const pres = new pptxgen();
  pres.layout = "LAYOUT_16x9"; // 10 x 5.625
  pres.author = "Sebastián Inostroza, Maite Bahamondes, Ruth Vergara";
  pres.title = "Evaluación comparativa de encoders ajustados y modelos de lenguaje generativos para el reconocimiento de entidades clínicas de atención primaria chilena";
  pres.theme = { headFontFace: THEME.headFontFace, bodyFontFace: THEME.bodyFontFace };
  const C = pres.SchemeColor;

  // ------------------------------------------------------------------ layouts
  pres.defineSlideMaster({
    title: "PORTADA", background: { color: HEX.navy },
    objects: [
      { placeholder: { options: { name: "title", type: "title", x: 0.6, y: 1.35, w: 8.8, h: 1.6, fontSize: 30, bold: true, color: C.background1, valign: "top", align: "left" }, text: "" } },
      { placeholder: { options: { name: "body", type: "body", x: 0.6, y: 3.05, w: 8.8, h: 1.0, fontSize: 15, color: "C9D3E6", valign: "top", align: "left" }, text: "" } },
    ],
  });
  pres.defineSlideMaster({
    title: "CONTENIDO", background: { color: "FFFFFF" },
    margin: [0.5, 0.5, 0.5, 0.5],
    objects: [
      { placeholder: { options: { name: "title", type: "title", x: 0.5, y: 0.3, w: 9.0, h: 0.6, fontSize: 26, bold: true, color: C.text2, valign: "top", align: "left", margin: 0 }, text: "" } },
      { placeholder: { options: { name: "body", type: "body", x: 0.5, y: 0.88, w: 9.0, h: 0.35, fontSize: 13, italic: true, color: C.accent6, valign: "top", align: "left", margin: 0 }, text: "" } },
      { text: { text: "NER clínico en derivaciones de APS chilena · IA Generativa y Modelos Fundacionales · UV 2026", options: { x: 0.5, y: 5.25, w: 7.5, h: 0.25, fontSize: 9, color: HEX.gris, margin: 0 } } },
    ],
    slideNumber: { x: 9.1, y: 5.25, w: 0.4, h: 0.25, fontSize: 9, color: HEX.gris, align: "right" },
  });
  pres.defineSlideMaster({
    title: "CIERRE", background: { color: HEX.navy },
    objects: [
      { placeholder: { options: { name: "title", type: "title", x: 0.6, y: 0.45, w: 8.8, h: 0.7, fontSize: 28, bold: true, color: C.background1, valign: "top", align: "left", margin: 0 }, text: "" } },
    ],
    slideNumber: { x: 9.1, y: 5.25, w: 0.4, h: 0.25, fontSize: 9, color: "C9D3E6", align: "right" },
  });

  const ic = {
    texto: await icono(fa.FaFileMedical, HEX.navy), escudo: await icono(fa.FaShieldAlt, HEX.navy), libro: await icono(fa.FaBookOpen, HEX.navy),
    lupa: await icono(fa.FaSearch, HEX.navy), robot: await icono(fa.FaRobot, HEX.navy), nube: await icono(fa.FaCloud, HEX.navy),
    escuela: await icono(fa.FaChalkboardTeacher, HEX.navy), votos: await icono(fa.FaVoteYea, HEX.navy), check: await icono(fa.FaCheckCircle, HEX.aqua),
    x: await icono(fa.FaTimesCircle, HEX.rojo), medio: await icono(fa.FaAdjust, HEX.naranja), alerta: await icono(fa.FaExclamationTriangle, HEX.naranja),
    pc: await icono(fa.FaLaptopMedical, "FFFFFF"), datos: await icono(fa.FaDatabase, "FFFFFF"), hibrido: await icono(fa.FaProjectDiagram, "FFFFFF"),
  };
  const ejesGraf = (extra = {}) => Object.assign({
    catAxisLabelColor: HEX.texto2, valAxisLabelColor: HEX.texto2, catAxisLabelFontFace: "+mn-lt", valAxisLabelFontFace: "+mn-lt",
    catAxisLabelFontSize: 11, valAxisLabelFontSize: 10, valGridLine: { color: "E2E6EE", size: 0.5 }, catGridLine: { style: "none" },
    legendFontFace: "+mn-lt", legendFontSize: 10, legendColor: HEX.texto2, dataLabelFontFace: "+mn-lt", dataLabelFontSize: 9, dataLabelColor: HEX.texto2,
    titleFontFace: "+mn-lt",
  }, extra);
  const tarjeta = (s, x, y, w, h, nombre) => s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x, y, w, h, rectRadius: 0.08, fill: { color: C.background2 }, line: { type: "none" }, objectName: nombre });

  // ------------------------------------------------------------------ 1 portada
  pres.addSection({ title: "Introducción" });
  let s = pres.addSlide({ masterName: "PORTADA", sectionTitle: "Introducción" });
  s.addImage({ path: path.join(DIR, "recursos/logo_uv_blanco.png"), x: 0.6, y: 0.45, w: 1.6, h: 0.75, objectName: "Logo UV" });
  s.addImage({ path: path.join(DIR, "recursos/logo_dcis_blanco.png"), x: 8.3, y: 0.35, w: 1.1, h: 0.77, objectName: "Logo DCIS" });
  s.addText("Evaluación comparativa de encoders ajustados y modelos de lenguaje generativos", { placeholder: "title" });
  s.addText([
    { text: "para el reconocimiento de entidades clínicas de atención primaria chilena", options: { breakLine: true } },
    { text: " ", options: { breakLine: true, fontSize: 8 } },
    { text: "Sebastián Inostroza · Maite Bahamondes · Ruth Vergara", options: { fontSize: 13, color: "FFFFFF", bold: true } },
  ], { placeholder: "body" });
  s.addText("Inteligencia Artificial Generativa y Modelos Fundacionales · prof. Rodrigo Salas · Doctorado en Ciencias e Ingeniería para la Salud", { x: 0.6, y: 4.75, w: 8.8, h: 0.35, fontSize: 11, color: "C9D3E6", isTextBox: true, margin: 0 });
  s.addNotes("Buenos días. Les vamos a presentar una evaluación comparativa. Con un mismo protocolo probamos encoders ajustados y modelos de lenguaje generativos sobre derivaciones reales de la atención primaria chilena, para saber cuál reconoce mejor enfermedades, medicamentos y abreviaturas en nuestro texto, y si ese orden coincide con lo que reporta la literatura.");

  // ------------------------------------------------------------------ 2 problema
  s = pres.addSlide({ masterName: "CONTENIDO", sectionTitle: "Introducción" });
  s.addText("La información clínica de APS está en texto libre", { placeholder: "title" });
  s.addText("Así escribe un médico cuando deriva a un paciente", { placeholder: "body" });
  tarjeta(s, 0.5, 1.45, 5.3, 2.05, "Ejemplo de derivación");
  s.addText([
    { text: "pcte c/ ", options: { color: HEX.texto } },
    { text: "DM2 desc", options: { color: "FFFFFF", highlight: "2A78D6", bold: true } },
    { text: " , s/ ctrl hace 6m. En tto con ", options: { color: HEX.texto } },
    { text: "metformina", options: { color: "FFFFFF", highlight: "1BAF7A", bold: true } },
  ], { x: 0.75, y: 1.65, w: 4.9, h: 0.9, fontSize: 18, fontFace: "Courier New", isTextBox: true, margin: 0, valign: "top" });
  s.addText([
    { text: "Enfermedad", options: { color: HEX.azul, bold: true } }, { text: "   " },
    { text: "Medicamento", options: { color: HEX.aqua, bold: true } }, { text: "   " },
    { text: "Abreviaturas: pcte, c/, DM2, s/, ctrl, tto", options: { color: HEX.naranja, bold: true } },
  ], { x: 0.75, y: 2.65, w: 4.9, h: 0.6, fontSize: 12, isTextBox: true, margin: 0 });
  const filas2 = [
    [ic.texto, "Reconocer entidades (NER)", "Ubicar qué palabras son una enfermedad, un fármaco o una abreviatura. Es el primer paso para convertir la nota en datos."],
    [ic.escudo, "Ley 21.719 (dic. 2026)", "Restringe enviar datos de salud a servicios externos. Un CESFAM necesita modelos que corran en sus propios equipos."],
  ];
  filas2.forEach(([img, tit, txt], i) => {
    const y = 1.45 + i * 1.2;
    s.addImage({ data: img, x: 6.15, y: y + 0.05, w: 0.42, h: 0.42, objectName: "Icono " + tit });
    s.addText(tit, { x: 6.7, y, w: 2.8, h: 0.35, fontSize: 14, bold: true, color: C.text2, isTextBox: true, margin: 0 });
    s.addText(txt, { x: 6.7, y: y + 0.36, w: 2.8, h: 0.8, fontSize: 11.5, color: HEX.texto2, isTextBox: true, margin: 0, valign: "top" });
  });
  s.addText("Proveedores de ficha electrónica ya ofrecen IA generativa en APS, sin métricas públicas.", { x: 0.5, y: 3.85, w: 9.0, h: 0.4, fontSize: 13, italic: true, color: HEX.rojo, isTextBox: true, margin: 0 });
  s.addNotes("La nota dice que el paciente tiene diabetes tipo 2 descompensada y lleva seis meses sin control. Un médico la entiende; un sistema administrativo, no. Reconocer entidades es ubicar en la oración qué palabras son enfermedad, medicamento o abreviatura. La Ley 21.719 restringe sacar datos de salud del centro, y ya hay proveedores vendiendo IA generativa en APS sin publicar cómo rinde.");

  // ------------------------------------------------------------------ 3 literatura
  s = pres.addSlide({ masterName: "CONTENIDO", sectionTitle: "Introducción" });
  s.addText("Lo que dice la literatura", { placeholder: "title" });
  s.addText("Evidencia de casos clínicos publicados y de notas en inglés", { placeholder: "body" });
  const stats3 = [["3–15", "puntos de F1", "gana el encoder ajustado a un LLM con prompting, en español"], ["+5–9", "puntos", "suma elegir los ejemplos del prompt por similitud (few-shot dinámico)"], ["0", "estudios", "comparan estas estrategias con el corpus chileno completo"]];
  stats3.forEach(([n, u, t], i) => {
    const x = 0.5 + i * 3.05;
    tarjeta(s, x, 1.5, 2.85, 2.45, "Dato " + n);
    s.addText(n, { x: x + 0.25, y: 1.65, w: 2.4, h: 0.9, fontSize: 44, bold: true, color: i === 2 ? HEX.rojo : C.text2, isTextBox: true, margin: 0 });
    s.addText(u, { x: x + 0.25, y: 2.5, w: 2.4, h: 0.3, fontSize: 13, bold: true, color: HEX.texto2, isTextBox: true, margin: 0 });
    s.addText(t, { x: x + 0.25, y: 2.85, w: 2.4, h: 0.95, fontSize: 12, color: HEX.texto2, isTextBox: true, margin: 0, valign: "top" });
  });
  s.addText("Las derivaciones de APS son distintas: oraciones cortas, siglas locales, faltas de ortografía y plantillas repetidas.", { x: 0.5, y: 4.25, w: 9.0, h: 0.5, fontSize: 13, color: HEX.texto, isTextBox: true, margin: 0 });
  s.addNotes("La literatura da una receta clara. En español, el encoder ajustado le gana a un LLM con prompting entre 3 y 15 puntos de F1 (Naguib 2024). Elegir los ejemplos por similitud suma 5 a 9 puntos (Ge 2026). El problema es de dónde sale esa evidencia: casos clínicos publicados en revistas o notas en inglés. Nadie lo había probado con el corpus chileno completo bajo un mismo protocolo.");

  // ------------------------------------------------------------------ 4 hipótesis
  s = pres.addSlide({ masterName: "CONTENIDO", sectionTitle: "Introducción" });
  s.addText("Objetivo e hipótesis", { placeholder: "title" });
  s.addText("Comparar encoders ajustados y LLM generativos en el reconocimiento de enfermedades, medicamentos y abreviaturas en derivaciones de APS chilena", { placeholder: "body" });
  const hip = [["H1", "Un encoder ajustado obtiene mayor F1 que los LLM generativos"], ["H2", "Elegir los ejemplos por similitud mejora el F1 de los LLM"], ["H3", "La diferencia encoder–LLM es mayor en las abreviaturas"], ["H4", "LLM anotador + 50 oraciones anotadas queda cerca del encoder completo"], ["H5", "Un LLM comercial reduce la diferencia, pero no iguala al encoder"]];
  hip.forEach(([h, t], i) => {
    const y = 1.45 + i * 0.68;
    s.addShape(pres.shapes.OVAL, { x: 0.6, y, w: 0.52, h: 0.52, fill: { color: C.text2 }, line: { type: "none" }, objectName: "Círculo " + h });
    s.addText(h, { x: 0.6, y, w: 0.52, h: 0.52, fontSize: 13, bold: true, color: "FFFFFF", align: "center", valign: "middle", isTextBox: true, margin: 0 });
    s.addText(t, { x: 1.3, y, w: 8.1, h: 0.52, fontSize: 15, color: HEX.texto, valign: "middle", isTextBox: true, margin: 0 });
  });
  s.addNotes("El objetivo es comparar los dos tipos de modelo en las tres entidades, con el mismo test y el mismo protocolo. Para eso tenemos cuatro objetivos específicos: ajustar tres encoders, medir cuatro LLM con tres formas de armar el prompt, ver cuánto se acerca un encoder entrenado con etiquetas de un LLM y poca anotación, y analizar errores y votación. Las hipótesis las fijamos antes de correr cada experimento. Las cuatro primeras salen de la literatura; la quinta la agregamos al sumar los modelos comerciales. Al final volvemos a esta lista.");

  // ------------------------------------------------------------------ 5 corpus
  pres.addSection({ title: "Métodos" });
  s = pres.addSlide({ masterName: "CONTENIDO", sectionTitle: "Métodos" });
  s.addText("Chilean Waiting List Corpus", { placeholder: "title" });
  s.addText("Derivaciones reales de APS, desidentificadas, escritas y anotadas por médicos y dentistas (Báez et al., 2022)", { placeholder: "body" });
  [["8.014", "oraciones de entrenamiento"], ["890", "de validación"], ["990", "de prueba"]].forEach(([n, t], i) => {
    s.addText(n, { x: 0.5, y: 1.45 + i * 0.95, w: 2.2, h: 0.6, fontSize: 36, bold: true, color: C.text2, isTextBox: true, margin: 0 });
    s.addText(t, { x: 0.5, y: 2.0 + i * 0.95, w: 2.6, h: 0.3, fontSize: 12, color: HEX.texto2, isTextBox: true, margin: 0 });
  });
  s.addChart(pres.charts.BAR, [{ name: "Menciones en el test", labels: ["Enfermedad", "Abreviatura", "Medicamento"], values: [1071, 993, 92] }], ejesGraf({
    x: 3.3, y: 1.35, w: 3.4, h: 3.2, barDir: "bar", chartColors: [HEX.navy], showValue: true, dataLabelPosition: "outEnd", showLegend: false,
    showTitle: true, title: "Menciones en las 990 oraciones de prueba", titleFontSize: 11, titleColor: HEX.texto2, valAxisHidden: true, valGridLine: { style: "none" }, objectName: "Gráfico menciones test",
  }));
  tarjeta(s, 6.95, 1.45, 2.55, 3.05, "Auditoría");
  s.addImage({ data: ic.lupa, x: 7.15, y: 1.6, w: 0.34, h: 0.34, objectName: "Icono auditoría" });
  s.addText("Auditoría antes de entrenar", { x: 7.6, y: 1.6, w: 1.85, h: 0.4, fontSize: 12.5, bold: true, color: C.text2, isTextBox: true, margin: 0 });
  s.addText([
    { text: "9,7 % de las oraciones del test está también en entrenamiento (plantillas).", options: { bullet: true, breakLine: true } },
    { text: "42 textos idénticos con anotación distinta.", options: { bullet: true, breakLine: true } },
    { text: "Reportamos todo también sin duplicados.", options: { bullet: true } },
  ], { x: 7.15, y: 2.1, w: 2.25, h: 2.3, fontSize: 11.5, color: HEX.texto2, isTextBox: true, margin: 0, paraSpaceAfter: 6, valign: "top" });
  s.addNotes("Usamos el Chilean Waiting List Corpus, versión 4, con la partición oficial: 8.014 oraciones para entrenar, 890 para validar y 990 para la prueba final. Trabajamos con tres entidades: enfermedad, medicamento y abreviatura. Ojo con medicamento: solo 92 menciones en la prueba, así que sus intervalos son anchos. Antes de entrenar auditamos fugas: casi un 10 % de las oraciones del test se repite en entrenamiento, sobre todo plantillas. Por eso reportamos todo también sin esas oraciones.");

  // ------------------------------------------------------------------ 6 diseño
  s = pres.addSlide({ masterName: "CONTENIDO", sectionTitle: "Métodos" });
  s.addText("Cuatro estrategias sobre el mismo test", { placeholder: "title" });
  s.addText("Mismas 990 oraciones, mismas funciones de evaluación, 3 semillas por modelo entrenable", { placeholder: "body" });
  const exps = [
    [ic.libro, "E1 · Encoder ajustado", "RoBERTa clínico español, el mismo adaptado a derivaciones chilenas, y RigoBERTa Clinical (large). Un etiquetador por entidad.", HEX.azul],
    [ic.robot, "E2 · LLM local", "Llama 3.1 8B y Qwen 2.5 7B en el Mac: zero-shot, 5 ejemplos fijos y 5 ejemplos dinámicos (BM25).", HEX.naranja],
    [ic.nube, "E2 nube · Techo comercial", "GPT-5.2 y Gemini 3.1 Pro con el mismo prompt. Solo porque el corpus es público.", HEX.aqua],
    [ic.escuela, "E4 · LLM como anotador", "Qwen etiqueta 2.000 oraciones; un encoder aprende de esas etiquetas + 0, 10, 50 o 100 oraciones gold.", HEX.violeta],
  ];
  exps.forEach(([img, tit, txt, col], i) => {
    const x = 0.5 + (i % 2) * 4.6, y = 1.45 + Math.floor(i / 2) * 1.75;
    tarjeta(s, x, y, 4.4, 1.55, "Tarjeta " + tit);
    s.addShape(pres.shapes.OVAL, { x: x + 0.2, y: y + 0.22, w: 0.6, h: 0.6, fill: { color: "FFFFFF" }, line: { color: col, width: 2 }, objectName: "Círculo " + tit });
    s.addImage({ data: img, x: x + 0.34, y: y + 0.36, w: 0.32, h: 0.32, objectName: "Icono " + tit });
    s.addText(tit, { x: x + 0.95, y: y + 0.18, w: 3.3, h: 0.35, fontSize: 14, bold: true, color: C.text2, isTextBox: true, margin: 0 });
    s.addText(txt, { x: x + 0.95, y: y + 0.55, w: 3.3, h: 0.9, fontSize: 11.5, color: HEX.texto2, isTextBox: true, margin: 0, valign: "top" });
  });
  s.addNotes("Estos son los experimentos. E1 es la línea base: encoders tipo BERT ajustados con las 8.014 oraciones, incluido uno adaptado a texto chileno y uno grande. E2 son LLM locales que corren en un Mac, con tres formas de armar el prompt. E2 nube es el techo comercial, que solo usamos porque el corpus es público. E4 simula un centro sin anotación: el LLM etiqueta y un encoder aprende de esas etiquetas. También combinamos los encoders por votación.");

  // ------------------------------------------------------------------ 7 evaluación
  s = pres.addSlide({ masterName: "CONTENIDO", sectionTitle: "Métodos" });
  s.addText("Cómo medimos", { placeholder: "title" });
  s.addText("Una predicción cuenta solo si el inicio, el fin y el tipo coinciden con la anotación", { placeholder: "body" });
  tarjeta(s, 0.5, 1.45, 4.4, 2.9, "Estricto vs laxo");
  s.addText("Gold:", { x: 0.75, y: 1.65, w: 1.0, h: 0.35, fontSize: 12, bold: true, color: HEX.texto2, isTextBox: true, margin: 0 });
  s.addText([{ text: "caries", options: { highlight: "2A78D6", color: "FFFFFF", bold: true } }, { text: " ", options: { highlight: "2A78D6" } }, { text: "profunda", options: { highlight: "2A78D6", color: "FFFFFF", bold: true } }, { text: " pieza 36" }], { x: 1.6, y: 1.62, w: 3.2, h: 0.4, fontSize: 15, fontFace: "Courier New", isTextBox: true, margin: 0 });
  s.addText("Modelo:", { x: 0.75, y: 2.15, w: 1.0, h: 0.35, fontSize: 12, bold: true, color: HEX.texto2, isTextBox: true, margin: 0 });
  s.addText([{ text: "caries", options: { highlight: "EB6834", color: "FFFFFF", bold: true } }, { text: " profunda pieza 36" }], { x: 1.6, y: 2.12, w: 3.2, h: 0.4, fontSize: 15, fontFace: "Courier New", isTextBox: true, margin: 0 });
  s.addImage({ data: ic.x, x: 0.75, y: 2.8, w: 0.3, h: 0.3, objectName: "Icono estricto" });
  s.addText("F1 estricto: error (límite más corto)", { x: 1.15, y: 2.78, w: 3.6, h: 0.35, fontSize: 12.5, color: HEX.texto, isTextBox: true, margin: 0 });
  s.addImage({ data: ic.check, x: 0.75, y: 3.3, w: 0.3, h: 0.3, objectName: "Icono laxo" });
  s.addText("F1 laxo: acierto (se superponen)", { x: 1.15, y: 3.28, w: 3.6, h: 0.35, fontSize: 12.5, color: HEX.texto, isTextBox: true, margin: 0 });
  s.addText([
    { text: "IC 95 % con bootstrap por oración y comparación pareada entre sistemas.", options: { bullet: true, breakLine: true } },
    { text: "3 semillas por modelo entrenable. Solo afirmamos que un encoder gana si se repite en las 3.", options: { bullet: true, breakLine: true } },
    { text: "Subgrupos: abreviadas, mal escritas, menciones nunca vistas.", options: { bullet: true, breakLine: true } },
    { text: "En los LLM: alucinaciones, JSON inválidos, tiempo y costo.", options: { bullet: true } },
  ], { x: 5.2, y: 1.5, w: 4.3, h: 2.9, fontSize: 13, color: HEX.texto, isTextBox: true, margin: 0, paraSpaceAfter: 10, valign: "top" });
  s.addNotes("La métrica principal es el F1 estricto: la predicción tiene que calzar exacto en inicio, fin y tipo. El laxo acepta superposición, y la diferencia entre ambos nos dice cuántos errores son de límite. La semilla aleatoria cambia el resultado del ajuste fino, así que repetimos cada encoder tres veces y solo afirmamos una diferencia si aparece en las tres.");

  // ------------------------------------------------------------------ 8 resultado global
  pres.addSection({ title: "Resultados" });
  s = pres.addSlide({ masterName: "CONTENIDO", sectionTitle: "Resultados" });
  s.addText("El encoder ajustado sigue ganando", { placeholder: "title" });
  s.addText("F1 estricto en las 990 oraciones de prueba (encoders: media de 3 semillas)", { placeholder: "body" });
  s.addChart(pres.charts.BAR, [
    { name: "E1 chileno", labels: ["Enfermedad", "Medicamento", "Abreviatura"], values: [0.815, 0.794, 0.952] },
    { name: "E1 español", labels: ["Enfermedad", "Medicamento", "Abreviatura"], values: [0.798, 0.840, 0.950] },
    { name: "Gemini 3.1 Pro dinámico", labels: ["Enfermedad", "Medicamento", "Abreviatura"], values: [0.717, 0.844, 0.901] },
    { name: "GPT-5.2 dinámico", labels: ["Enfermedad", "Medicamento", "Abreviatura"], values: [0.727, 0.772, 0.887] },
    { name: "Qwen 7B dinámico", labels: ["Enfermedad", "Medicamento", "Abreviatura"], values: [0.663, 0.670, 0.642] },
    { name: "Llama 8B dinámico", labels: ["Enfermedad", "Medicamento", "Abreviatura"], values: [0.650, 0.697, 0.703] },
  ], ejesGraf({
    x: 0.4, y: 1.3, w: 6.3, h: 3.85, barDir: "col", barGapWidthPct: 60, chartColors: ["14284B", "2A78D6", "1BAF7A", "0F7F57", "EB6834", "B8471C"],
    showLegend: true, legendPos: "b", valAxisMinVal: 0.5, valAxisMaxVal: 1.0, valAxisMajorUnit: 0.1, valAxisLabelFormatCode: "0.0", showValue: false, objectName: "Gráfico F1 global",
  }));
  tarjeta(s, 6.95, 1.45, 2.55, 3.4, "Lectura global");
  s.addText([
    { text: "0,815", options: { fontSize: 30, bold: true, color: HEX.navy, breakLine: true } },
    { text: "encoder chileno en enfermedad", options: { fontSize: 11.5, color: HEX.texto2, breakLine: true } },
    { text: " ", options: { fontSize: 8, breakLine: true } },
    { text: "13–25 pts", options: { fontSize: 24, bold: true, color: HEX.naranja, breakLine: true } },
    { text: "bajo E1 queda el mejor LLM local", options: { fontSize: 11.5, color: HEX.texto2, breakLine: true } },
    { text: " ", options: { fontSize: 8, breakLine: true } },
    { text: "0,844", options: { fontSize: 24, bold: true, color: HEX.aqua, breakLine: true } },
    { text: "Gemini empata con E1 en medicamento", options: { fontSize: 11.5, color: HEX.texto2 } },
  ], { x: 7.15, y: 1.6, w: 2.2, h: 3.15, isTextBox: true, margin: 0, valign: "top" });
  s.addNotes("Este es el resultado central. Los encoders ganan en enfermedad y abreviatura: el chileno llega a 0,815 en enfermedad y los encoders a 0,95 en abreviatura. El mejor LLM local queda entre 13 y 25 puntos abajo, con diferencias significativas contra cada semilla. Los comerciales se acercan, y Gemini con ejemplos dinámicos empata en medicamento: 0,844 contra 0,840, sin diferencia significativa. Sin las oraciones duplicadas, el F1 del encoder baja menos de un punto.");

  // ------------------------------------------------------------------ 9 estrategias
  s = pres.addSlide({ masterName: "CONTENIDO", sectionTitle: "Resultados" });
  s.addText("Los ejemplos parecidos ayudan a todos los LLM", { placeholder: "title" });
  s.addText("F1 estricto en enfermedad según cómo se arma el prompt", { placeholder: "body" });
  s.addChart(pres.charts.BAR, [
    { name: "Zero-shot", labels: ["Llama 8B", "Qwen 7B", "GPT-5.2", "Gemini 3.1"], values: [0.446, 0.537, 0.645, 0.618] },
    { name: "5 ejemplos fijos", labels: ["Llama 8B", "Qwen 7B", "GPT-5.2", "Gemini 3.1"], values: [0.526, 0.560, 0, 0] },
    { name: "5 ejemplos dinámicos", labels: ["Llama 8B", "Qwen 7B", "GPT-5.2", "Gemini 3.1"], values: [0.650, 0.663, 0.727, 0.717] },
  ], ejesGraf({
    x: 0.4, y: 1.3, w: 5.8, h: 3.85, barDir: "col", barGapWidthPct: 70, chartColors: ["B9C3D3", "8A94A6", "14284B"], showLegend: true, legendPos: "b",
    valAxisMinVal: 0, valAxisMaxVal: 0.9, valAxisMajorUnit: 0.1, valAxisLabelFormatCode: "0.0", showValue: true, dataLabelPosition: "outEnd", dataLabelFormatCode: "0.00;;", objectName: "Gráfico estrategias",
  }));
  tarjeta(s, 6.5, 1.45, 3.0, 3.4, "Lectura estrategias");
  s.addText([
    { text: "+10 a +12 pts", options: { fontSize: 24, bold: true, color: HEX.navy, breakLine: true } },
    { text: "del dinámico sobre los ejemplos fijos en los LLM locales (significativo)", options: { fontSize: 11.5, color: HEX.texto2, breakLine: true } },
    { text: " ", options: { fontSize: 8, breakLine: true } },
    { text: "52 %", options: { fontSize: 24, bold: true, color: HEX.rojo, breakLine: true } },
    { text: "de lo que devolvió Llama sin ejemplos era inventado; Qwen dinámico 5 %, GPT-5.2 0,4 %", options: { fontSize: 11.5, color: HEX.texto2, breakLine: true } },
    { text: " ", options: { fontSize: 8, breakLine: true } },
    { text: "~4 USD", options: { fontSize: 24, bold: true, color: HEX.aqua, breakLine: true } },
    { text: "costó cada modelo comercial para todo el test", options: { fontSize: 11.5, color: HEX.texto2 } },
  ], { x: 6.7, y: 1.6, w: 2.65, h: 3.15, isTextBox: true, margin: 0, valign: "top" });
  s.addNotes("H2 se cumple. Pasar de ejemplos fijos a ejemplos parecidos suma 10 a 12 puntos en enfermedad, y la ventaja casi no cambia al quitar las oraciones duplicadas, así que no es copia. Los LLM locales sin ejemplos son poco confiables: Llama inventó la mitad de lo que devolvió. Los comerciales no los corrimos con ejemplos fijos. Cada uno costó cerca de 4 dólares para todo el test, con ambas estrategias.");

  // ------------------------------------------------------------------ 10 abreviaturas y escala
  s = pres.addSlide({ masterName: "CONTENIDO", sectionTitle: "Resultados" });
  s.addText("Abreviaturas y tamaño del modelo", { placeholder: "title" });
  s.addText("Recall en enfermedades con abreviatura (n = 119) y sin ella; LLM con ejemplos dinámicos", { placeholder: "body" });
  s.addChart(pres.charts.BAR, [
    { name: "Con abreviatura", labels: ["E1 chileno", "E1 español", "Gemini din.", "GPT-5.2 din.", "Qwen din.", "Llama din."], values: [0.843, 0.790, 0.824, 0.748, 0.647, 0.655] },
    { name: "Sin abreviatura", labels: ["E1 chileno", "E1 español", "Gemini din.", "GPT-5.2 din.", "Qwen din.", "Llama din."], values: [0.835, 0.816, 0.841, 0.804, 0.723, 0.764] },
  ], ejesGraf({
    x: 0.4, y: 1.3, w: 5.6, h: 3.85, barDir: "col", barGapWidthPct: 60, chartColors: ["EB6834", "B9C3D3"], showLegend: true, legendPos: "b",
    valAxisMinVal: 0.5, valAxisMaxVal: 0.9, valAxisMajorUnit: 0.1, valAxisLabelFormatCode: "0.0", catAxisLabelFontSize: 10, objectName: "Gráfico abreviadas",
  }));
  tarjeta(s, 6.3, 1.45, 3.2, 1.55, "H3");
  s.addText([{ text: "H3 se cumple en enfermedad", options: { bold: true, color: HEX.navy, breakLine: true, fontSize: 13.5 } }, { text: "Con ejemplos dinámicos, los 4 LLM pierden recall con abreviaturas. El encoder chileno no tiene esa brecha.", options: { color: HEX.texto2, fontSize: 11.5 } }], { x: 6.5, y: 1.58, w: 2.85, h: 1.35, isTextBox: true, margin: 0, valign: "top" });
  tarjeta(s, 6.3, 3.2, 3.2, 1.65, "Escala");
  s.addText([{ text: "4,5× más grande, no mejor", options: { bold: true, color: HEX.navy, breakLine: true, fontSize: 13.5 } }, { text: "RigoBERTa Clinical (560M): 0,803 en enfermedad. No supera a los encoders base y no cupo en el Mac: se entrenó en una GPU A100.", options: { color: HEX.texto2, fontSize: 11.5 } }], { x: 6.5, y: 3.33, w: 2.85, h: 1.45, isTextBox: true, margin: 0, valign: "top" });
  s.addNotes("Con las abreviaturas, los cuatro LLM reconocen peor las enfermedades abreviadas, como DM2 o HTA. El encoder chileno no muestra esa diferencia, y en abreviadas le gana al español por 5 puntos. Es la señal más clara a favor de adaptar el modelo al texto local. También probamos si un modelo más grande sube el techo. RigoBERTa Clinical tiene 4,5 veces más parámetros y no ganó en ninguna entidad. Tampoco se pudo entrenar en el Mac del proyecto: necesitó una GPU de 80 GB.");

  // ------------------------------------------------------------------ 11 E4
  s = pres.addSlide({ masterName: "CONTENIDO", sectionTitle: "Resultados" });
  s.addText("El LLM como anotador no reemplaza la anotación", { placeholder: "title" });
  s.addText("E4 en enfermedad: F1 estricto según las oraciones gold disponibles (media de 3 semillas)", { placeholder: "body" });
  s.addChart(pres.charts.LINE, [
    { name: "Alumno: silver + gold", labels: ["0", "10", "50", "100"], values: [0.561, 0.571, 0.644, 0.650] },
    { name: "Solo gold", labels: ["0", "10", "50", "100"], values: [null, 0.278, 0.489, 0.595] },
    { name: "Maestro (Qwen 7B)", labels: ["0", "10", "50", "100"], values: [0.532, 0.524, 0.586, 0.595] },
    { name: "E1 con 8.014 oraciones", labels: ["0", "10", "50", "100"], values: [0.798, 0.798, 0.798, 0.798] },
  ], ejesGraf({
    x: 0.4, y: 1.3, w: 5.8, h: 3.85, chartColors: ["1BAF7A", "EB6834", "8A94A6", "2A78D6"], lineSize: 2, lineDataSymbolSize: 7, showLegend: true, legendPos: "b",
    valAxisMinVal: 0, valAxisMaxVal: 1.0, valAxisMajorUnit: 0.2, valAxisLabelFormatCode: "0.0", showCatAxisTitle: true, catAxisTitle: "Oraciones gold", catAxisTitleColor: HEX.texto2, catAxisTitleFontSize: 10, objectName: "Gráfico E4",
  }));
  tarjeta(s, 6.5, 1.45, 3.0, 3.4, "Lectura E4");
  s.addText([
    { text: "H4 no se cumple", options: { fontSize: 15, bold: true, color: HEX.rojo, breakLine: true } },
    { text: "Con 50 gold, el alumno queda 15 a 36 puntos bajo E1 según la entidad.", options: { fontSize: 11.5, color: HEX.texto2, breakLine: true } },
    { text: " ", options: { fontSize: 8, breakLine: true } },
    { text: "El alumno supera al maestro", options: { fontSize: 13.5, bold: true, color: HEX.navy, breakLine: true } },
    { text: "0,644 contra 0,586 con 50 gold. El techo lo pone la calidad del LLM anotador.", options: { fontSize: 11.5, color: HEX.texto2, breakLine: true } },
    { text: " ", options: { fontSize: 8, breakLine: true } },
    { text: "Con 100 gold iguala al LLM directo", options: { fontSize: 13.5, bold: true, color: HEX.navy, breakLine: true } },
    { text: "0,650 contra 0,663, sin necesitar el LLM al usarlo.", options: { fontSize: 11.5, color: HEX.texto2 } },
  ], { x: 6.7, y: 1.6, w: 2.65, h: 3.15, isTextBox: true, margin: 0, valign: "top" });
  s.addNotes("E4 simula un centro con poca anotación. Qwen etiqueta 2.000 oraciones y un encoder aprende de esas etiquetas. Con pocas oraciones gold, las etiquetas del LLM ayudan mucho: con 10 oraciones, 0,57 contra 0,28. Y el alumno termina mejor que su maestro. Pero la hipótesis no se cumple: con 50 oraciones gold quedamos 15 a 36 puntos bajo el encoder completo. El maestro local es débil, y eso pone el techo. En abreviatura, las etiquetas del LLM incluso estorban.");

  // ------------------------------------------------------------------ 12 errores
  s = pres.addSlide({ masterName: "CONTENIDO", sectionTitle: "Resultados" });
  s.addText("Los LLM aciertan lo mismo, pero marcan de más", { placeholder: "title" });
  s.addText("Predicciones de enfermedad en el test (E1: semilla 42)", { placeholder: "body" });
  const sis = ["E1 chileno", "GPT-5.2 din.", "Gemini din.", "Qwen din.", "Llama din."];
  s.addChart(pres.charts.BAR, [
    { name: "Correctas", labels: sis, values: [895, 854, 899, 765, 805] },
    { name: "Error de límite", labels: sis, values: [113, 138, 131, 161, 142] },
    { name: "Espurias sobre un hallazgo", labels: sis, values: [84, 245, 373, 227, 333] },
    { name: "Otras espurias", labels: sis, values: [28, 41, 33, 84, 125] },
  ], ejesGraf({
    x: 0.4, y: 1.3, w: 6.0, h: 3.85, barDir: "bar", barGrouping: "stacked", barGapWidthPct: 50, chartColors: ["2A78D6", "B9C3D3", "EB6834", "F3A684"],
    showLegend: true, legendPos: "b", valAxisLabelFormatCode: "#,##0", catAxisOrientation: "maxMin", objectName: "Gráfico tipología",
  }));
  tarjeta(s, 6.7, 1.45, 2.8, 3.4, "Lectura errores");
  s.addText([
    { text: "899 vs 895", options: { fontSize: 24, bold: true, color: HEX.navy, breakLine: true } },
    { text: "enfermedades exactas: Gemini dinámico y encoder chileno", options: { fontSize: 11.5, color: HEX.texto2, breakLine: true } },
    { text: " ", options: { fontSize: 8, breakLine: true } },
    { text: "406 vs 112", options: { fontSize: 24, bold: true, color: HEX.naranja, breakLine: true } },
    { text: "espurias. La mayoría cae sobre un hallazgo anotado: “dolor”, “vómitos”, “mordida invertida”", options: { fontSize: 11.5, color: HEX.texto2 } },
  ], { x: 6.9, y: 1.6, w: 2.45, h: 3.15, isTextBox: true, margin: 0, valign: "top" });
  s.addNotes("Gemini con ejemplos encuentra 899 enfermedades exactas y el encoder chileno 895: aciertan lo mismo. La diferencia está en lo que marcan de más: 406 espurias contra 112. Y la mayoría cae sobre hallazgos, como dolor o vómitos, que la guía del corpus anota como hallazgo y no como enfermedad. Parte del error del LLM es un desacuerdo de criterio con la anotación.");

  // ------------------------------------------------------------------ 13 dónde gana el LLM
  s = pres.addSlide({ masterName: "CONTENIDO", sectionTitle: "Resultados" });
  s.addText("Donde el LLM grande sí gana", { placeholder: "title" });
  s.addText("Recall estricto por subgrupo", { placeholder: "body" });
  s.addChart(pres.charts.BAR, [
    { name: "E1 chileno", labels: ["Enfermedad bien escrita", "Enfermedad mal escrita (31)", "Abreviatura nunca vista (66)"], values: [0.844, 0.559, 0.601] },
    { name: "GPT-5.2 dinámico", labels: ["Enfermedad bien escrita", "Enfermedad mal escrita (31)", "Abreviatura nunca vista (66)"], values: [0.801, 0.677, 0.712] },
    { name: "Gemini zero-shot", labels: ["Enfermedad bien escrita", "Enfermedad mal escrita (31)", "Abreviatura nunca vista (66)"], values: [0.788, 0.774, 0.758] },
  ], ejesGraf({
    x: 0.4, y: 1.3, w: 5.8, h: 3.85, barDir: "col", barGapWidthPct: 60, chartColors: ["2A78D6", "0F7F57", "1BAF7A"], showLegend: true, legendPos: "b",
    valAxisMinVal: 0, valAxisMaxVal: 1.0, valAxisMajorUnit: 0.2, valAxisLabelFormatCode: "0.0", showValue: true, dataLabelPosition: "outEnd", dataLabelFormatCode: "0.00", catAxisLabelFontSize: 10, objectName: "Gráfico subgrupos",
  }));
  tarjeta(s, 6.5, 1.45, 3.0, 3.4, "Lectura subgrupos");
  s.addText([
    { text: "FUSROSEMIDA", options: { fontSize: 18, bold: true, color: HEX.navy, fontFace: "Courier New", breakLine: true } },
    { text: "son 5 piezas para el encoder; “furosemida”, 1. El encoder reconoce la jerga que vio y le cuesta la que no vio.", options: { fontSize: 11.5, color: HEX.texto2, breakLine: true } },
    { text: " ", options: { fontSize: 8, breakLine: true } },
    { text: "¿Híbrido?", options: { fontSize: 15, bold: true, color: HEX.naranja, breakLine: true } },
    { text: "Juntos llegarían a recall 0,92, pero las tres combinaciones simples que probamos empeoraron el F1: cada acierto del LLM trae varios falsos positivos.", options: { fontSize: 11.5, color: HEX.texto2 } },
  ], { x: 6.7, y: 1.6, w: 2.65, h: 3.15, isTextBox: true, margin: 0, valign: "top" });
  s.addNotes("Los LLM comerciales sí ganan en dos casos. En palabras mal escritas, el encoder cae de 0,84 a 0,56 y Gemini casi no cae. La razón está en la tokenización: furosemida es una pieza para el encoder, y con un error de tipeo se parte en cinco que nunca vio juntas. En abreviaturas nunca vistas pasa lo mismo. Pensamos en un híbrido: juntos encontrarían el 92 % de las enfermedades. Pero las combinaciones simples empeoraron el F1, porque el LLM trae demasiados falsos positivos. Las palabras mal escritas son solo el 3 % del test.");

  // ------------------------------------------------------------------ 14 votación
  s = pres.addSlide({ masterName: "CONTENIDO", sectionTitle: "Resultados" });
  s.addText("Combinar semillas rinde más que agrandar el modelo", { placeholder: "title" });
  s.addText("Votación por mayoría estricta entre 6 encoders base (2 modelos × 3 semillas), regla fijada antes de mirar el test", { placeholder: "body" });
  s.addText("0,837", { x: 0.5, y: 1.55, w: 4.0, h: 1.3, fontSize: 72, bold: true, color: HEX.violeta, isTextBox: true, margin: 0 });
  s.addText("F1 estricto en enfermedad, IC 95 % de 0,815 a 0,857. Mejor que cada uno de los 6 modelos por 1,3 a 4,5 puntos, significativo contra todos.", { x: 0.5, y: 2.9, w: 4.0, h: 1.2, fontSize: 13, color: HEX.texto2, isTextBox: true, margin: 0, valign: "top" });
  s.addChart(pres.charts.BAR, [{ name: "Enfermedad", labels: ["E1 español", "RigoBERTa", "E1 chileno", "Votación 6", "Votación 9"], values: [0.798, 0.803, 0.815, 0.837, 0.838] }], ejesGraf({
    x: 4.8, y: 1.35, w: 4.7, h: 3.4, barDir: "bar", chartColors: ["B9C3D3", "B9C3D3", "2A78D6", "6250D6", "6250D6"], invertedColors: ["B9C3D3"],
    showLegend: false, showValue: true, dataLabelPosition: "outEnd", dataLabelFormatCode: "0.000", valAxisMinVal: 0.7, valAxisMaxVal: 0.86, valAxisHidden: true, valGridLine: { style: "none" }, catAxisOrientation: "maxMin", objectName: "Gráfico votación",
  }));
  s.addText("Sumar RigoBERTa (votación 9) no agrega nada. Seis modelos de 125M siguen cabiendo en un computador común.", { x: 0.5, y: 4.3, w: 4.0, h: 0.75, fontSize: 12, italic: true, color: HEX.texto, isTextBox: true, margin: 0 });
  s.addNotes("La mejor cifra del estudio salió de votar entre encoders. La variación entre semillas, que normalmente solo se reporta, se puede aprovechar: votamos entre seis encoders y una entidad queda si al menos cuatro la predicen. Enfermedad sube a 0,837, significativamente mejor que cada modelo solo. Fijamos la regla antes de mirar el test. Agregar el modelo grande no sumó nada.");

  // ------------------------------------------------------------------ 15 hipótesis
  pres.addSection({ title: "Cierre" });
  s = pres.addSlide({ masterName: "CONTENIDO", sectionTitle: "Cierre" });
  s.addText("¿Qué se cumplió?", { placeholder: "title" });
  s.addText("Lo que reporta la literatura se mantuvo en derivaciones chilenas, con dos sorpresas", { placeholder: "body" });
  const res = [
    [ic.check, "H1", "El encoder gana en enfermedad y abreviatura", "Apoyada"],
    [ic.check, "H2", "Ejemplos dinámicos mejoran a los 4 LLM", "Apoyada"],
    [ic.medio, "H3", "Brecha con abreviaturas en enfermedad", "Apoyada en enfermedad"],
    [ic.x, "H4", "Destilación con 50 gold: 15–36 puntos bajo E1", "No apoyada"],
    [ic.medio, "H5", "Gemini empata con E1 en medicamento", "Apoyada en 2 de 3"],
  ];
  res.forEach(([img, h, t, r], i) => {
    const y = 1.45 + i * 0.68;
    tarjeta(s, 0.5, y, 9.0, 0.56, "Fila " + h);
    s.addImage({ data: img, x: 0.68, y: y + 0.12, w: 0.32, h: 0.32, objectName: "Icono " + h });
    s.addText(h, { x: 1.15, y, w: 0.6, h: 0.56, fontSize: 15, bold: true, color: C.text2, valign: "middle", isTextBox: true, margin: 0 });
    s.addText(t, { x: 1.8, y, w: 5.2, h: 0.56, fontSize: 13.5, color: HEX.texto, valign: "middle", isTextBox: true, margin: 0 });
    s.addText(r, { x: 7.0, y, w: 2.35, h: 0.56, fontSize: 13, bold: true, color: r === "No apoyada" ? HEX.rojo : r === "Apoyada" ? "0F7F57" : HEX.naranja, valign: "middle", align: "right", isTextBox: true, margin: 0 });
  });
  s.addNotes("Volvemos a las hipótesis. H1 y H2 se cumplen: el encoder gana y los ejemplos dinámicos ayudan, igual que en la literatura. H3 se cumple en enfermedad. H4 no se cumple: la destilación quedó mucho más lejos que en los trabajos en inglés. H5 se cumple en dos de tres entidades, porque Gemini alcanzó al encoder en medicamento.");

  // ------------------------------------------------------------------ 16 limitaciones
  s = pres.addSlide({ masterName: "CONTENIDO", sectionTitle: "Cierre" });
  s.addText("Limitaciones", { placeholder: "title" });
  s.addText("Lo que este estudio no puede afirmar", { placeholder: "body" });
  const lim = [
    ["Derivaciones, no fichas", "Textos cortos para pedir una interconsulta. Las evoluciones y planes de cuidado de CESFAM pueden comportarse distinto."],
    ["Posible contaminación", "El encoder chileno y los LLM comerciales pudieron ver el corpus, público desde 2022. Sus cifras serían un techo optimista."],
    ["Pocos medicamentos", "92 menciones en el test: intervalos de ±7 puntos. Hay ruido de anotación (42 textos idénticos anotados distinto)."],
    ["Lo que no alcanzamos", "Ajuste fino de un LLM con LoRA y normalización previa de abreviaturas. Una corrida por estrategia en los LLM."],
  ];
  lim.forEach(([t, d], i) => {
    const x = 0.5 + (i % 2) * 4.6, y = 1.45 + Math.floor(i / 2) * 1.75;
    tarjeta(s, x, y, 4.4, 1.55, "Limitación " + t);
    s.addImage({ data: ic.alerta, x: x + 0.22, y: y + 0.22, w: 0.32, h: 0.32, objectName: "Icono " + t });
    s.addText(t, { x: x + 0.7, y: y + 0.18, w: 3.55, h: 0.4, fontSize: 14, bold: true, color: C.text2, isTextBox: true, margin: 0 });
    s.addText(d, { x: x + 0.7, y: y + 0.6, w: 3.55, h: 0.85, fontSize: 11.5, color: HEX.texto2, isTextBox: true, margin: 0, valign: "top" });
  });
  s.addNotes("Las limitaciones. Las derivaciones no son fichas completas de CESFAM. Hay riesgo de contaminación: el encoder chileno se preentrenó con derivaciones sin que se sepa cuáles, y los LLM comerciales pudieron ver el corpus. Medicamento tiene pocas menciones. Y quedaron fuera el ajuste fino de un LLM con LoRA y la normalización de abreviaturas.");

  // ------------------------------------------------------------------ 17 conclusión
  s = pres.addSlide({ masterName: "CIERRE", sectionTitle: "Cierre" });
  s.addText("Qué le recomendaríamos a un CESFAM", { placeholder: "title" });
  const recs = [
    [ic.pc, "Un encoder base ajustado con texto local", "Es lo más preciso, corre en un computador común y no saca datos del centro. Con votación de varios, 0,837 en enfermedad."],
    [ic.datos, "Anotar algunos cientos de oraciones", "Rinde más que confiar en etiquetas de un LLM local. El tamaño del modelo no fue la variable que movió el resultado."],
    [ic.hibrido, "El LLM grande, para lo que el encoder no vio", "Palabras mal escritas y siglas nuevas. Un híbrido con la confianza del encoder queda como trabajo futuro."],
  ];
  recs.forEach(([img, t, d], i) => {
    const x = 0.6 + i * 3.0;
    s.addShape(pres.shapes.OVAL, { x, y: 1.5, w: 0.75, h: 0.75, fill: { color: HEX.azul }, line: { type: "none" }, objectName: "Círculo rec " + (i + 1) });
    s.addImage({ data: img, x: x + 0.19, y: 1.69, w: 0.37, h: 0.37, objectName: "Icono rec " + (i + 1) });
    s.addText(t, { x, y: 2.45, w: 2.7, h: 0.75, fontSize: 15, bold: true, color: "FFFFFF", isTextBox: true, margin: 0, valign: "top" });
    s.addText(d, { x, y: 3.2, w: 2.7, h: 1.3, fontSize: 12, color: "C9D3E6", isTextBox: true, margin: 0, valign: "top" });
  });
  s.addText("Código, prompts y resultados: github.com/SebasDCIS/proyecto-ner-aps-genai", { x: 0.6, y: 4.75, w: 8.4, h: 0.35, fontSize: 11, color: "C9D3E6", isTextBox: true, margin: 0, hyperlink: { url: "https://github.com/SebasDCIS/proyecto-ner-aps-genai" } });
  s.addNotes("Para cerrar, lo que le recomendaríamos a un CESFAM. Si tiene texto anotado, un encoder base ajustado con datos locales es lo más preciso y corre en sus propios equipos, sin sacar datos. Si no tiene, conviene anotar algunos cientos de oraciones con criterio clínico antes que confiar en un LLM local como anotador. Y el LLM grande sirve para lo que el encoder no vio, pero falta diseñar bien cómo combinarlos. Todo el código y los resultados están en el repositorio. Gracias.");

  await pres.writeFile({ fileName: SALIDA });
  await applyTheme(SALIDA, THEME);
  console.log("ok", SALIDA);
})();
