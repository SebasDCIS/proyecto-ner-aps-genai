"""Construye el manuscrito en el formato Word entregado por el profesor.

Uso: python construir_docx.py <plantilla.docx> <salida.docx>
El contenido está en contenido.py; las citas se numeran por orden de aparición.
"""
import copy, re, sys
from pathlib import Path
import docx
from docx.shared import Inches, Pt
from docx.oxml.ns import qn
from docx.oxml import OxmlElement

AQUI = Path(__file__).resolve().parent
sys.path.insert(0, str(AQUI))
import contenido as C
from referencias_ieee import formatear_bib

plantilla, salida = sys.argv[1], sys.argv[2]
doc = docx.Document(plantilla)
P = doc.paragraphs
proto = {k: copy.deepcopy(P[i]._p) for k, i in dict(titulo=0, autores=1, afil=2, resumen=5, claves=6,
         h1=7, cuerpo=8, h2=12, fig=37, figcap=38, tabnum=45, tabtit=46, ref=53).items()}
body = doc.element.body
sect_final = copy.deepcopy(body.sectPr)
for el in list(body):
    if el.tag != qn("w:sectPr"):
        body.remove(el)

# ---------------------------------------------------------------- citas
orden = []
def citas(txt):
    def rep(m):
        nums = []
        for k in [x.strip() for x in m.group(1).split(",")]:
            if k not in orden:
                orden.append(k)
            nums.append(orden.index(k) + 1)
        return ", ".join(f"[{n}]" for n in nums)
    return re.sub(r"\[@([^\]]+)\]", rep, txt)

# ---------------------------------------------------------------- utilidades XML
def base_rpr(p):
    r = p.find(qn("w:r"))
    rp = r.find(qn("w:rPr")) if r is not None else None
    return copy.deepcopy(rp) if rp is not None else OxmlElement("w:rPr")

def nuevo_p(clave):
    p = copy.deepcopy(proto[clave])
    rpr = base_rpr(p)
    for ch in list(p):
        if ch.tag != qn("w:pPr"):
            p.remove(ch)
    return p, rpr

def set_flag(rpr, tag, on=True):
    el = rpr.find(qn(tag))
    if on and el is None:
        rpr.append(OxmlElement(tag))
    if not on and el is not None:
        rpr.remove(el)

def run(p, texto, rpr, b=None, i=None, sup=False, sub=False, mono=False, color=None):
    r = OxmlElement("w:r"); rp = copy.deepcopy(rpr)
    if b is not None: set_flag(rp, "w:b", b)
    if i is not None: set_flag(rp, "w:i", i)
    if sup or sub:
        va = OxmlElement("w:vertAlign"); va.set(qn("w:val"), "superscript" if sup else "subscript"); rp.append(va)
    if mono:
        f = rp.find(qn("w:rFonts"))
        if f is None:
            f = OxmlElement("w:rFonts"); rp.insert(0, f)
        for a in ("w:ascii", "w:hAnsi", "w:cs", "w:eastAsia"): f.set(qn(a), "Courier New")
        for t in ("w:sz", "w:szCs"):
            e = rp.find(qn(t))
            if e is not None: e.set(qn("w:val"), str(int(e.get(qn("w:val"))) - 2))
    if color:
        c = rp.find(qn("w:color"))
        if c is None: c = OxmlElement("w:color"); rp.append(c)
        c.set(qn("w:val"), color)
    r.append(rp)
    t = OxmlElement("w:t"); t.set(qn("xml:space"), "preserve"); t.text = texto; r.append(t)
    p.append(r)

TOK = re.compile(r"(\*\*.+?\*\*|\*.+?\*|\^.+?\^|~.+?~|`.+?`)")
def rico(p, texto, rpr, **kw):
    for seg in TOK.split(citas(texto)):
        if not seg: continue
        if seg.startswith("**"): run(p, seg[2:-2], rpr, **{**kw, "b": True})
        elif seg.startswith("*"): run(p, seg[1:-1], rpr, i=True, **kw)
        elif seg.startswith("^"): run(p, seg[1:-1], rpr, sup=True, **kw)
        elif seg.startswith("~"): run(p, seg[1:-1], rpr, sub=True, **kw)
        elif seg.startswith("`"): run(p, seg[1:-1], rpr, mono=True, **kw)
        else: run(p, seg, rpr, **kw)

def add(p):
    body.insert(len(body) - 1, p)
    return p

def ppr(p):
    return p.find(qn("w:pPr"))

def set_ind(p, left=0, hanging=0, first=0):
    pp = ppr(p); ind = pp.find(qn("w:ind"))
    if ind is None:
        ind = OxmlElement("w:ind"); pp.append(ind)
    ind.set(qn("w:left"), str(left))
    if hanging: ind.set(qn("w:hanging"), str(hanging))
    if first: ind.set(qn("w:firstLine"), str(first))

def set_spacing(p, before=None, after=None):
    pp = ppr(p); sp = pp.find(qn("w:spacing"))
    if sp is None:
        sp = OxmlElement("w:spacing"); pp.insert(1, sp)
    if before is not None: sp.set(qn("w:before"), str(before))
    if after is not None: sp.set(qn("w:after"), str(after))

def set_jc(p, val):
    pp = ppr(p); jc = pp.find(qn("w:jc"))
    if jc is None:
        jc = OxmlElement("w:jc"); pp.append(jc)
    jc.set(qn("w:val"), val)

def quitar_sect(p):
    s = ppr(p).find(qn("w:sectPr"))
    if s is not None: ppr(p).remove(s)

# ---------------------------------------------------------------- bloques
def titulo(t):
    p, r = nuevo_p("titulo"); rico(p, t, r); add(p)

def autores(lista):
    p, r = nuevo_p("autores")
    for k, (n, s) in enumerate(lista):
        sep = "" if k == 0 else (" y " if k == len(lista) - 1 else ", ")
        if sep: run(p, sep, r)
        run(p, n, r); run(p, s, r, sup=True)
    add(p)

def afiliacion(s, t):
    p, r = nuevo_p("afil"); run(p, s, r, sup=True); rico(p, t, r); add(p)

def etiqueta_y_texto(clave, etq, texto, cierra_seccion=False):
    p, r = nuevo_p(clave)
    runs = proto[clave].findall(qn("w:r"))
    r_etq = copy.deepcopy(runs[0].find(qn("w:rPr"))); r_txt = copy.deepcopy(runs[-1].find(qn("w:rPr")))
    run(p, etq, r_etq); rico(p, " " + texto, r_txt)
    if not cierra_seccion: quitar_sect(p)
    add(p)

def h1(num, t):
    p, r = nuevo_p("h1"); run(p, (f"{num}. " if num else "") + t.upper(), r)
    set_spacing(p, before=200, after=60); add(p)

def h2(letra, t):
    p, r = nuevo_p("h2"); run(p, f"{letra}. {t}", r); set_spacing(p, before=160, after=40); add(p)

def parrafo(t, sangria=True, cabeza=None):
    p, r = nuevo_p("cuerpo")
    if sangria: set_ind(p, first=200)
    if cabeza: run(p, cabeza + " ", r, i=True)
    rico(p, t, r); add(p)

def lista(items, numerada=True):
    for k, t in enumerate(items, 1):
        p, r = nuevo_p("cuerpo"); set_ind(p, left=300, hanging=300)
        if numerada: run(p, f"{k})\t", r)
        rico(p, t, r); add(p)

def fig_inline(ruta, num, cap, ancho):
    p, r = nuevo_p("fig"); set_jc(p, "center"); ppr(p).insert(0, OxmlElement("w:keepNext")); add(p)
    para = docx.text.paragraph.Paragraph(p, doc._body)
    para.add_run().add_picture(str(ruta), width=Inches(ancho))
    c, _ = nuevo_p("figcap")
    runs = proto["figcap"].findall(qn("w:r"))
    run(c, f"FIGURA {num}.", copy.deepcopy(runs[0].find(qn("w:rPr"))))
    rt = copy.deepcopy(runs[-1].find(qn("w:rPr"))); set_flag(rt, "w:b", False)
    rico(c, "  " + cap, rt); set_spacing(c, before=60, after=160); set_jc(c, "both"); add(c)

def cap_tabla(num, t):
    p, r = nuevo_p("tabnum"); run(p, f"TABLA {num}", r); set_spacing(p, before=160)
    ppr(p).insert(0, OxmlElement("w:keepNext")); add(p)
    p, r = nuevo_p("tabtit"); rico(p, t, r); set_spacing(p, after=60)
    ppr(p).insert(0, OxmlElement("w:keepNext")); add(p)

def borde(tc_or_tbl, lados, sz):
    pr = tc_or_tbl
    b = OxmlElement("w:tcBorders")
    for lado in ["top", "left", "bottom", "right"]:
        e = OxmlElement(f"w:{lado}")
        if lado in lados:
            e.set(qn("w:val"), "single"); e.set(qn("w:sz"), str(sz)); e.set(qn("w:color"), "000000")
        else:
            e.set(qn("w:val"), "nil")
        b.append(e)
    pr.append(b)

def tabla(enc, filas, anchos, notas=(), alin=None, sep_filas=()):
    t = doc.add_table(rows=1 + len(filas), cols=len(enc))
    tbl = t._tbl; body.remove(tbl); body.insert(len(body) - 1, tbl)
    tp = tbl.tblPr
    jc = OxmlElement("w:jc"); jc.set(qn("w:val"), "center"); tp.append(jc)
    lay = OxmlElement("w:tblLayout"); lay.set(qn("w:type"), "fixed"); tp.append(lay)
    alin = alin or (["left"] + ["center"] * (len(enc) - 1))
    grid = tbl.find(qn("w:tblGrid"))
    for gc, w in zip(grid.findall(qn("w:gridCol")), anchos):
        gc.set(qn("w:w"), str(w))
    tw = tp.find(qn("w:tblW"))
    if tw is None:
        tw = OxmlElement("w:tblW"); tp.append(tw)
    tw.set(qn("w:w"), str(sum(anchos))); tw.set(qn("w:type"), "dxa")
    for ri, fila in enumerate([enc] + filas):
        for ci, txt in enumerate(fila):
            cell = t.rows[ri].cells[ci]; cell.width = Inches(anchos[ci] / 1440)
            tcpr = cell._tc.get_or_add_tcPr()
            lados = []
            if ri == 0: lados = ["top", "bottom"]
            if ri == len(filas): lados.append("bottom")
            if ri in sep_filas: lados.append("top")
            if lados: borde(tcpr, lados, 6)
            p = cell.paragraphs[0]._p
            pp = OxmlElement("w:pPr"); j = OxmlElement("w:jc"); j.set(qn("w:val"), alin[ci]); pp.append(j)
            sp = OxmlElement("w:spacing"); sp.set(qn("w:before"), "10"); sp.set(qn("w:after"), "10"); pp.insert(0, sp)
            if ri < len(filas): pp.insert(0, OxmlElement("w:keepNext"))
            p.insert(0, pp)
            rp = OxmlElement("w:rPr")
            for tag in ("w:sz", "w:szCs"):
                e = OxmlElement(tag); e.set(qn("w:val"), "15"); rp.append(e)
            if ri == 0: set_flag(rp, "w:b", True)
            rico(p, txt, rp)
    for n in notas:
        p, r = nuevo_p("cuerpo")
        for tag in ("w:sz", "w:szCs"):
            e = r.find(qn(tag)); e.set(qn("w:val"), "14")
        rico(p, n, r); set_spacing(p, before=20); add(p)
    p, _ = nuevo_p("cuerpo"); set_spacing(p, after=80); add(p)

def corte(columnas):
    """Termina la sección actual; la que termina tiene `columnas` (1 o 2)."""
    p, r = nuevo_p("cuerpo")
    s = copy.deepcopy(sect_final)
    for ch in list(s):
        if ch.tag in (qn("w:headerReference"), qn("w:footerReference")):
            s.remove(ch)
    if columnas == 1:
        cols = s.find(qn("w:cols"))
        for ch in list(cols): cols.remove(ch)
        cols.attrib.clear(); cols.set(qn("w:space"), "720")
    ppr(p).append(s)
    rp = ppr(p).find(qn("w:rPr"))
    for tag in ("w:sz", "w:szCs"):
        e = rp.find(qn(tag))
        if e is not None: e.set(qn("w:val"), "2")
    add(p)

def ancho_completo(fn):
    corte(2); fn(); corte(1)

def referencias():
    h1(None, "Referencias")
    bib = formatear_bib(AQUI.parent / "referencias.bib")
    for k in orden:
        p, r = nuevo_p("ref"); rico(p, bib[k], r); add(p)

# número de página real en el pie (la plantilla trae un "1" fijo)
for rel in doc.part.rels.values():
    if rel.reltype.endswith("/footer"):
        ftr = rel.target_part.element
        for t in ftr.iter(qn("w:t")):
            if t.text == "1":
                r = t.getparent(); r.remove(t)
                for tipo, txt in (("begin", None), (None, " PAGE "), ("end", None)):
                    if tipo:
                        f = OxmlElement("w:fldChar"); f.set(qn("w:fldCharType"), tipo); r.append(f)
                    else:
                        it = OxmlElement("w:instrText"); it.set(qn("xml:space"), "preserve"); it.text = txt; r.append(it)
                break

C.construir(sys.modules[__name__])
referencias()
doc.save(salida)
faltan = set(re.findall(r"@(\w+)", open(AQUI.parent / "referencias.bib").read())) - set(orden)
print("citas:", len(orden), "| no citadas:", sorted(faltan))
