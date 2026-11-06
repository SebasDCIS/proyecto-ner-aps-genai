import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from analisis import errores as A
from datos.cwlc import Oracion


def test_tipologia_clasifica_cada_caso():
    gold = [("d", 0, 10, "Disease"), ("d", 20, 30, "Disease"), ("d", 40, 50, "Disease"), ("d", 60, 70, "Disease")]
    pred = [("d", 0, 10, "Disease"),      # correcta
            ("d", 18, 32, "Disease"),     # más larga
            ("d", 42, 48, "Disease"),     # más corta
            ("d", 80, 90, "Disease")]     # espuria; la de 60-70 queda omitida
    c = A.tipologia(gold, pred)
    assert c == {"correcta": 1, "más larga": 1, "más corta": 1, "espuria": 1, "omitida": 1}


def test_distancia_con_trasposicion_y_corte():
    assert A.distancia("furosemida", "fusrosemida") == 1
    assert A.distancia("cefalea", "cafalea") == 1
    assert A.distancia("abcd", "bacd") == 1
    assert A.distancia("hipertension", "periodontitis", 2) == 3


def test_detector_ortografia_sin_diccionario():
    train = [Oracion(f"t{i}", ["PERIODONTITIS", "CRONICA", "CAMARA"]) for i in range(5)]
    det = A.DetectorOrtografia(train, diccionario=frozenset())
    assert det.correccion("PERIODENTITIS") == "periodontitis"
    assert det.correccion("CAMARAS") is None          # plural, no error
    assert det.correccion("CRÓNICA") is None          # tilde, no error
    assert det.correccion("HTA") is None              # corta


def test_cruce_y_combinaciones():
    gold = [("d", 0, 5, "Disease"), ("d", 10, 15, "Disease"), ("d", 20, 25, "Disease")]
    a = [("d", 0, 5, "Disease")]
    b = [("d", 0, 5, "Disease"), ("d", 10, 15, "Disease"), ("d", 1, 4, "Disease")]
    c = A.cruce(gold, a, b)
    assert (c["ambos"], c["solo B"], c["ninguno"]) == (1, 1, 1) and abs(c["recall_oraculo"] - 2 / 3) < 1e-9
    assert A.rescate_sin_choque(a, b) == [("d", 0, 5, "Disease"), ("d", 10, 15, "Disease")]
    assert A.interseccion(a, b) == a and len(A.union(a, b)) == 3


def test_espurias_sobre_hallazgo_y_recall_pareado():
    o = Oracion("d", ["dolor", "y", "HTA"], [("d", 0, 5, "Finding"), ("d", 8, 11, "Disease")])
    pred = [("d", 0, 5, "Disease"), ("d", 8, 11, "Disease")]
    assert A.espurias_sobre_otros_tipos([o], "Disease", pred) == {"Finding": 1}
    g = [("d", 8, 11, "Disease")]
    obs, lo, hi = A.dif_recall_pareada(g, pred, [], n_boot=50)
    assert obs == 1.0 and lo == hi == 1.0


def test_votacion_mayoria_estricta():
    a, b, c = ("d", 0, 3, "Disease"), ("d", 5, 9, "Disease"), ("d", 12, 15, "Disease")
    preds = [[a, b], [a, c], [a, b]]
    assert A.votacion(preds) == [a, b]               # 2 de 3
    assert A.votacion(preds, minimo=3) == [a]
    assert A.votacion([[a], [a], [b], [b]]) == []    # 4 modelos: hacen falta 3 votos
