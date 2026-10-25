"""Lectura del Chilean Waiting List Corpus (CWLC) en formato CoNLL.

Fuente: archivos CoNLL publicados por PLN@CMM junto al paper de Báez et al. (2022),
un archivo por tipo de entidad y split (p. ej. Disease/Disease_train.conll).
Cada tipo viene en su propio archivo porque las entidades pueden anidarse
("cáncer de [mama]"): un token puede ser parte de una Enfermedad y de una Parte del
cuerpo a la vez. Aquí juntamos los 7 archivos de un split en una sola estructura.

Representación que usa todo el proyecto:
- Oracion: id, lista de tokens, texto (tokens unidos por un espacio).
- Entidad: (id_oracion, inicio, fin, tipo) con posiciones de carácter [inicio, fin)
  sobre ese texto. Es el mismo formato que espera src/evaluacion/metricas.py.
"""
from __future__ import annotations

from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path

TIPOS = ["Abbreviation", "Body_Part", "Disease", "Family_Member", "Finding", "Medication", "Procedure"]
SPLITS = ["train", "dev", "test"]


@dataclass
class Oracion:
    id: str
    tokens: list[str]
    entidades: list[tuple[str, int, int, str]] = field(default_factory=list)

    @property
    def texto(self) -> str:
        return " ".join(self.tokens)

    def offsets(self) -> list[tuple[int, int]]:
        """Posición [inicio, fin) de cada token dentro de `texto`."""
        pos, salida = 0, []
        for t in self.tokens:
            salida.append((pos, pos + len(t)))
            pos += len(t) + 1
        return salida

    def mencion(self, ent: tuple[str, int, int, str]) -> str:
        return self.texto[ent[1]:ent[2]]


def leer_conll(ruta: Path) -> list[tuple[list[str], list[str]]]:
    """Lee un CoNLL de dos columnas (token etiqueta). Devuelve [(tokens, etiquetas), ...]."""
    oraciones, toks, tags = [], [], []
    for linea in ruta.read_text(encoding="utf-8").splitlines():
        if not linea.strip():
            if toks:
                oraciones.append((toks, tags))
                toks, tags = [], []
            continue
        partes = linea.rsplit(" ", 1)
        if len(partes) != 2:
            partes = linea.split()
            partes = [" ".join(partes[:-1]), partes[-1]]
        toks.append(partes[0])
        tags.append(partes[1])
    if toks:
        oraciones.append((toks, tags))
    return oraciones


def bio_a_spans(etiquetas: list[str]) -> list[tuple[int, int, str]]:
    """Convierte etiquetas BIO en spans de tokens [inicio, fin) con su tipo."""
    spans, inicio, tipo = [], None, None
    for i, et in enumerate(etiquetas + ["O"]):
        if et.startswith("B-") or et == "O" or (et.startswith("I-") and et[2:] != tipo):
            if inicio is not None:
                spans.append((inicio, i, tipo))
                inicio, tipo = None, None
            if et.startswith("B-") or et.startswith("I-"):  # I- huérfano se trata como inicio
                inicio, tipo = i, et[2:]
    return spans


def cargar_split(carpeta: Path, split: str, tipos: list[str] | None = None) -> list[Oracion]:
    """Une los archivos de cada tipo de entidad de un split en una lista de oraciones."""
    tipos = tipos or TIPOS
    oraciones: list[Oracion] | None = None
    for tipo in tipos:
        datos = leer_conll(carpeta / tipo / f"{tipo}_{split}.conll")
        if oraciones is None:
            oraciones = [Oracion(f"{split}-{i:05d}", toks) for i, (toks, _) in enumerate(datos)]
        if len(datos) != len(oraciones):
            raise ValueError(f"{tipo}/{split}: {len(datos)} oraciones, se esperaban {len(oraciones)}")
        for orac, (toks, tags) in zip(oraciones, datos):
            if toks != orac.tokens:
                raise ValueError(f"Tokens distintos entre archivos en {orac.id} ({tipo})")
            off = orac.offsets()
            for a, b, _ in bio_a_spans(tags):
                orac.entidades.append((orac.id, off[a][0], off[b - 1][1], tipo))
    return oraciones or []


def entidades(oraciones: list[Oracion], tipo: str | None = None) -> list[tuple[str, int, int, str]]:
    return [e for o in oraciones for e in o.entidades if tipo is None or e[3] == tipo]


def es_abreviada(ent: tuple[str, int, int, str], oracion: Oracion) -> bool:
    """True si la entidad contiene o se superpone con una entidad Abbreviation anotada.

    Así se separa, sin anotar nada nuevo, el F1 en entidades abreviadas vs no abreviadas.
    """
    return any(
        a[3] == "Abbreviation" and a[1] < ent[2] and ent[1] < a[2]
        for a in oracion.entidades
        if a is not ent
    )


def resumen(oraciones: list[Oracion]) -> dict:
    """Conteos básicos para describir un split."""
    por_tipo = Counter(e[3] for o in oraciones for e in o.entidades)
    return {
        "oraciones": len(oraciones),
        "tokens": sum(len(o.tokens) for o in oraciones),
        "entidades": sum(por_tipo.values()),
        **{f"n_{t}": por_tipo.get(t, 0) for t in TIPOS},
    }
