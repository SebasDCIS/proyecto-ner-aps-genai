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


def test_llamador_api_sin_clave_da_error_claro(monkeypatch):
    import pytest
    from modelos.e2_llm import crear_llamador_api
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    with pytest.raises(RuntimeError, match="OPENAI_API_KEY"):
        crear_llamador_api("openai")


def test_cargar_claves(tmp_path, monkeypatch):
    import os
    from modelos.e2_llm import cargar_claves
    (tmp_path / ".env").write_text("# comentario\nGEMINI_API_KEY='abc'\n")
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    assert cargar_claves(tmp_path / ".env") == ["GEMINI_API_KEY"] and os.environ["GEMINI_API_KEY"] == "abc"


def test_llamador_api_reintenta_sin_parametro_rechazado(monkeypatch):
    import openai
    from types import SimpleNamespace
    from modelos import e2_llm
    llamadas = []

    class Falso:
        def __init__(self, **kw):
            self.chat = SimpleNamespace(completions=SimpleNamespace(create=self.create))

        def create(self, model, messages, **params):
            llamadas.append(dict(params))
            if "temperature" in params:
                class Rechazo(openai.BadRequestError):
                    def __init__(self, msg):
                        Exception.__init__(self, msg)
                raise Rechazo("Unsupported parameter: temperature")
            return SimpleNamespace(choices=[SimpleNamespace(message=SimpleNamespace(content='{"entidades":[]}'))],
                                   usage=SimpleNamespace(prompt_tokens=10, completion_tokens=3))

    monkeypatch.setenv("OPENAI_API_KEY", "x")
    monkeypatch.setattr(openai, "OpenAI", Falso)
    llamar = e2_llm.crear_llamador_api("openai")
    assert llamar("m", [{"role": "user", "content": "hola"}]) == '{"entidades":[]}'
    assert llamar.parametros_omitidos == ["temperature"] and llamar.ultimo_uso == {"entrada": 10, "salida": 3}
    assert "temperature" not in llamadas[-1]
