import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from datos.cwlc import Oracion
from modelos.e2_llm import respuesta_gold
from modelos.e4_destilacion import calidad_silver, oraciones_silver, pool_silver, selector_para, seleccionar_gold


def _train(n=300):
    return [Oracion(f"s{i}", ["pcte", "con", "HTA", f"x{i}"], [(f"s{i}", 9, 12, "Disease")]) for i in range(n)]


def test_gold_anidado_y_pool_disjunto():
    tr = _train()
    g10, g100 = seleccionar_gold(tr, 10), seleccionar_gold(tr, 100)
    assert [o.id for o in g10] == [o.id for o in g100[:10]]
    pool = pool_silver(tr, 50)
    assert not ({o.id for o in pool} & {o.id for o in g100}) and len(pool) == 50


def test_selector_solo_busca_en_gold():
    tr = _train()
    assert selector_para([]) is None
    sel = selector_para(seleccionar_gold(tr, 3))
    assert len(sel(tr[0])) == 3 and all(o in seleccionar_gold(tr, 3) for o in sel(tr[0]))


def test_silver_reemplaza_entidades_y_calidad_perfecta():
    pool = _train(5)
    resp = {o.id: {"respuesta": respuesta_gold(o), "segundos": 0} for o in pool}
    silver, ev = oraciones_silver(pool, resp)
    assert [o.entidades for o in silver] == [o.entidades for o in pool]
    assert calidad_silver(pool, silver)["Disease"]["f1"] == 1.0
