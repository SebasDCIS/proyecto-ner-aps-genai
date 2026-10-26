import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from datos.cwlc import Oracion
from modelos.e2_llm import (Cache, SelectorDinamico, SelectorFijo, correr, evaluar_respuestas, mensajes,
                            parsear, respuesta_gold, ubicar)

O = Oracion("t1", ["pcte", "con", "DM2", "y", "DM", "en", "tto", "con", "DM2"],
            [("t1", 9, 12, "Disease"), ("t1", 9, 12, "Abbreviation")])


def test_parsear_json_y_basura():
    assert parsear('{"entidades":[{"tipo":"Disease","texto":"DM2"}]}') == ([("Disease", "DM2")], True)
    assert parsear('```json\n{"entidades":[]}\n```') == ([], True)
    assert parsear("no sé") == ([], False)
    assert parsear('{"entidades":[{"tipo":"Otro","texto":"x"}]}') == ([], True)
    cortado = '{"entidades": [{"tipo": "Disease", "texto": "HTA"}, {"tipo": "Abbreviation", "texto": "X"}, {"tipo": "Abbrev'
    assert parsear(cortado) == ([("Disease", "HTA"), ("Abbreviation", "X")], False)


def test_ubicar_palabra_completa_anidamiento_y_alucinacion():
    ents, faltan = ubicar(O, [("Disease", "DM"), ("Disease", "dm2"), ("Abbreviation", "DM2"), ("Disease", "DM2"),
                              ("Medication", "losartan")])
    assert ("t1", 15, 17, "Disease") in ents            # "DM" solo, no dentro de "DM2"
    assert ("t1", 9, 12, "Disease") in ents and ("t1", 9, 12, "Abbreviation") in ents  # mismo span, dos tipos
    assert ("t1", 29, 32, "Disease") in ents            # segunda aparición de DM2
    assert faltan == 1                                  # losartan no está: alucinación


def test_respuesta_gold_y_mensajes():
    r = respuesta_gold(O)
    assert '"Disease"' in r and '"DM2"' in r
    m = mensajes(O, [O])
    assert m[0]["role"] == "system" and m[-1]["content"].endswith(O.texto) and len(m) == 4


def test_selectores():
    tr = [Oracion(f"s{i}", ["pcte", "con", "HTA", "y", "losartan", "en", "tto", "x"],
                  [(f"s{i}", 9, 12, "Disease"), (f"s{i}", 15, 23, "Medication"), (f"s{i}", 0, 4, "Abbreviation")])
          for i in range(10)]
    assert len(SelectorFijo(tr, k=5, semilla=1)(O)) == 5
    assert SelectorFijo(tr, k=5, semilla=1).ejemplos == SelectorFijo(tr, k=5, semilla=1).ejemplos
    assert len(SelectorDinamico(tr, k=3)(O)) == 3


def test_correr_con_oraculo_y_cache(tmp_path):
    oraculo = lambda modelo, msgs, semilla: respuesta_gold(O)
    cache = Cache(tmp_path / "c.jsonl")
    r = correr("falso", [O], None, cache, llamar=oraculo, registro=lambda *a: None)
    ev = evaluar_respuestas(r, [O])
    assert set(ev["pred"]["Disease"]) == {("t1", 9, 12, "Disease")} and ev["tasa_alucinacion"] == 0
    assert "t1" in Cache(tmp_path / "c.jsonl")          # se retoma desde disco
