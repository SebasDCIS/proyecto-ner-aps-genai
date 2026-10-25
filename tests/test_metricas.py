import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from evaluacion.metricas import (  # noqa: E402
    Conteo,
    alucinaciones,
    bootstrap_f1,
    bootstrap_pareado,
    contar,
    por_documento,
    ubicar_en_texto,
)


def test_ejemplo_guia():
    # 10 entidades gold, el modelo marca 8 y acierta 6 -> F1 ≈ 0,67 (Módulo 7 de la guía)
    gold = [("d", i * 10, i * 10 + 3, "Enfermedad") for i in range(10)]
    pred = gold[:6] + [("d", 500, 503, "Enfermedad"), ("d", 600, 603, "Enfermedad")]
    c = contar(gold, pred, "estricto")
    assert (c.vp, c.fp, c.fn) == (6, 2, 4)
    assert round(c.f1, 2) == 0.67


def test_laxo_vs_estricto():
    gold = [("d", 0, 24, "Enfermedad")]  # "diabetes mellitus tipo 2"
    pred = [("d", 0, 17, "Enfermedad")]  # "diabetes mellitus"
    assert contar(gold, pred, "estricto").f1 == 0.0
    assert contar(gold, pred, "laxo").f1 == 1.0


def test_tipo_equivocado_es_fp_y_fn():
    gold = [("d", 0, 3, "Enfermedad")]
    pred = [("d", 0, 3, "Farmaco")]
    c = contar(gold, pred, "estricto")
    assert (c.vp, c.fp, c.fn) == (0, 1, 1)


def test_ubicar_y_alucinaciones():
    texto = "pcte c/ DM2 desc, en tto c/ metformina. DM2 sin ctrl"
    ents = ubicar_en_texto(texto, [("Enfermedad", "DM2"), ("Enfermedad", "DM2"), ("Farmaco", "insulina")], "d")
    assert len(ents) == 2 and ents[0][1] != ents[1][1]
    assert alucinaciones([("d", "DM2"), ("d", "insulina")], {"d": texto}) == 0.5


def test_bootstrap():
    docs = {f"d{i}": Conteo(8, 2, 2) for i in range(30)}
    f1, lo, hi = bootstrap_f1(docs, n=200)
    assert lo <= f1 <= hi
    dif, lo, hi = bootstrap_pareado(docs, {f"d{i}": Conteo(5, 5, 5) for i in range(30)}, n=200)
    assert dif > 0 and lo > 0


def test_por_documento():
    gold = [("a", 0, 3, "E"), ("b", 0, 3, "E")]
    pred = [("a", 0, 3, "E")]
    pd = por_documento(gold, pred, "estricto")
    assert pd["a"].f1 == 1.0 and pd["b"].fn == 1
