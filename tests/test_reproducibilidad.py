import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import numpy as np
import torch

from datos.cwlc import Oracion
from datos.auditoria import normalizar, duplicados_entre_splits, conflictos_de_etiqueta, menciones_vistas
from reproducibilidad import (agregar_semillas, fijar_semilla_total, huella_archivos, huella_config,
                              huella_corpus, huella_predicciones)


def test_semilla_reproduce_azar():
    fijar_semilla_total(7); a = (np.random.rand(3), torch.rand(3))
    fijar_semilla_total(7); b = (np.random.rand(3), torch.rand(3))
    assert np.allclose(a[0], b[0]) and torch.equal(a[1], b[1])


def test_huellas_estables_y_sensibles(tmp_path):
    (tmp_path / "a.conll").write_text("x\tO\n")
    h1 = huella_archivos(tmp_path)["combinada"]
    assert h1 == huella_archivos(tmp_path)["combinada"]
    (tmp_path / "a.conll").write_text("x\tB-Disease\n")
    assert h1 != huella_archivos(tmp_path)["combinada"]
    assert huella_config({"a": 1, "b": 2}) == huella_config({"b": 2, "a": 1})
    assert huella_predicciones([("1", 0, 3, "D")]) != huella_predicciones([("1", 0, 4, "D")])


def test_huella_corpus_cambia_con_etiquetas():
    o1 = Oracion("1", ["pcte", "con", "hta"], [("1", 9, 12, "Disease")])
    o2 = Oracion("1", ["pcte", "con", "hta"], [])
    assert huella_corpus([o1]) != huella_corpus([o2])


def test_agregar_semillas():
    r = agregar_semillas([0.70, 0.72, 0.74])
    assert abs(r["media"] - 0.72) < 1e-9 and abs(r["de"] - 0.02) < 1e-9 and r["n"] == 3


def test_auditoria_detecta_duplicados_y_conflictos():
    tr = [Oracion("t1", ["Pcte", "con", "HTA"], [("t1", 9, 12, "Disease")])]
    te = [Oracion("s1", ["pcte", "con", "hta"], []), Oracion("s2", ["dolor", "lumbar"], [])]
    d = duplicados_entre_splits({"train": tr, "dev": te[1:], "test": te})
    assert d["train∩test"]["oraciones_repetidas_en_test"] == 1
    assert normalizar("Diabétes  Mellitus") == "diabetes mellitus"
    c = conflictos_de_etiqueta({"train": tr, "test": [Oracion("s", ["Pcte", "con", "HTA"], [])]})
    assert c["textos_con_anotacion_inconsistente"] == 1 and c["que_cruzan_splits"] == 1
    m = menciones_vistas(tr, [Oracion("s3", ["hta"], [("s3", 0, 3, "Disease")])], "Disease")
    assert m["ya_vistas_en_train"] == 1
