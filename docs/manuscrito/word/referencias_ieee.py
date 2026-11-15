"""Convierte referencias.bib a texto estilo IEEE (como el formato del curso)."""
import re

ACENTOS = {r"\'a": "á", r"\'e": "é", r"\'i": "í", r"\'o": "ó", r"\'u": "ú", r"\'E": "É", r"\'A": "Á",
           r"\`a": "à", r"\`e": "è", r"\~n": "ñ", r"\&": "&"}

def limpiar(s):
    s = re.sub(r"\\url\{([^}]*)\}", r"\1", s)
    s = re.sub(r"\{\\(['`~])\{?(\w)\}?\}", lambda m: ACENTOS.get("\\" + m.group(1) + m.group(2), m.group(2)), s)
    s = re.sub(r"\\(['`~])\{?(\w)\}?", lambda m: ACENTOS.get("\\" + m.group(1) + m.group(2), m.group(2)), s)
    s = s.replace(r"\&", "&").replace("--", "–")
    return re.sub(r"[{}]", "", s).strip()

def autor(a):
    a = a.strip()
    if a.startswith("{"):
        return limpiar(a)
    if "," in a:
        ap, nom = [x.strip() for x in a.split(",", 1)]
    else:
        partes = a.split(); ap, nom = partes[-1], " ".join(partes[:-1])
    ini = " ".join(w[0] + "." for w in re.split(r"[\s]+", limpiar(nom)) if w and w[0].isalpha())
    ini = ini.replace(". -", ".-")
    return f"{ini} {limpiar(ap)}".strip()

def autores(campo):
    lista = [x for x in re.split(r"\s+and\s+", campo)]
    if lista[-1].strip() == "others":
        return autor(lista[0]) + " *et al.*"
    n = [autor(x) for x in lista]
    return n[0] if len(n) == 1 else ", ".join(n[:-1]) + " y " + n[-1]

def formatear_bib(ruta):
    txt = open(ruta, encoding="utf-8").read()
    out = {}
    for tipo, clave, cuerpo in re.findall(r"@(\w+)\{(\w+),(.*?)\n\}", txt, flags=re.S):
        f = {k.lower(): v for k, v in re.findall(r"(\w+)\s*=\s*\{(.*)\},?\s*$", cuerpo, flags=re.M)}
        partes = [autores(f["author"]) + ","]
        partes.append(f"“{limpiar(f['title'])},”")
        venue = f.get("journal") or f.get("booktitle") or f.get("howpublished") or f.get("publisher")
        if venue: partes.append(f"*{limpiar(venue)}*,")
        if f.get("volume"): partes.append(f"vol. {f['volume']},")
        if f.get("number"): partes.append(f"no. {f['number']},")
        if f.get("pages"): partes.append(f"pp. {limpiar(f['pages'])},")
        if f.get("note"): partes.append(limpiar(f["note"]) + ",")
        partes.append(f["year"] + ".")
        if f.get("doi"): partes.append(f"doi: {f['doi']}.")
        out[clave] = " ".join(partes)
    return out
