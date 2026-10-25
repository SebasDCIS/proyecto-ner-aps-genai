import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from datos.cwlc import Oracion, bio_a_spans, cargar_split, es_abreviada  # noqa: E402


def test_bio_a_spans():
    assert bio_a_spans(["B-D", "I-D", "O", "B-D"]) == [(0, 2, "D"), (3, 4, "D")]
    assert bio_a_spans(["O", "I-D", "I-D"]) == [(1, 3, "D")]  # I- huérfano


def test_cargar_split_y_abreviadas(tmp_path):
    textos = {
        "Disease": "pcte O\nc/ O\nDM2 B-Disease\ndesc I-Disease\n\n",
        "Abbreviation": "pcte B-Abbreviation\nc/ B-Abbreviation\nDM2 B-Abbreviation\ndesc B-Abbreviation\n\n",
    }
    for tipo, contenido in textos.items():
        (tmp_path / tipo).mkdir()
        (tmp_path / tipo / f"{tipo}_test.conll").write_text(contenido, encoding="utf-8")
    ors = cargar_split(tmp_path, "test", ["Disease", "Abbreviation"])
    assert len(ors) == 1
    o = ors[0]
    enf = [e for e in o.entidades if e[3] == "Disease"][0]
    assert o.mencion(enf) == "DM2 desc"
    assert es_abreviada(enf, o)


def test_offsets():
    o = Oracion("x", ["HTA", "y", "DM2"])
    assert o.texto == "HTA y DM2" and o.offsets() == [(0, 3), (4, 5), (6, 9)]
