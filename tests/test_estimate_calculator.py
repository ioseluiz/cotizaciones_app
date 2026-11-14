import pytest

from utils.estimate_calculator import Activity, Expense, calculate, build_quote_items


def test_calculo_completo():
    acts = [Activity("Diseño", "Cálculo", 10, 40.0, "Ing. Sr")]
    exps = [Expense("Impresión de planos", 100.0)]
    s = calculate(acts, exps, contingencia_pct=10, margen_pct=20, aplica_itbms=True)
    assert s.horas_totales == 10
    assert s.costo_horas == pytest.approx(400.0)
    assert s.costo_base == pytest.approx(500.0)
    assert s.contingencia == pytest.approx(50.0)
    assert s.margen == pytest.approx(110.0)        # (500 + 50) * 20%
    assert s.subtotal == pytest.approx(660.0)
    assert s.itbms == pytest.approx(46.2)
    assert s.total == pytest.approx(706.2)
    assert s.horas_por_rol == {"Ing. Sr": 10}


def test_sin_ajustes():
    s = calculate([Activity("", "x", 3, 20.0)], [])
    assert s.total == pytest.approx(60.0)
    assert s.itbms == 0


def test_estimado_vacio():
    s = calculate([], [], 10, 20, True)
    assert s.total == 0
    assert build_quote_items([], [], 10, 20, True) == []


def test_items_por_fase_suman_total():
    acts = [
        Activity("Análisis", "Modelo", 7, 33.33),
        Activity("Diseño", "Vigas", 5.5, 25.0),
        Activity("Análisis", "Sismo", 3, 40.0),
        Activity("", "Sin fase", 1, 10.0),
    ]
    exps = [Expense("Viáticos", 75.5)]
    items = build_quote_items(acts, exps, contingencia_pct=12.5, margen_pct=17, aplica_itbms=True)
    s = calculate(acts, exps, 12.5, 17, True)

    assert [i["servicio"] for i in items] == ["Análisis", "Diseño", "General", "Gastos", "ITBMS (7%)"]
    assert "Modelo; Sismo (10 h)" == items[0]["descripcion"]
    assert sum(i["precio_total"] for i in items) == pytest.approx(round(s.total, 2), abs=0.001)
    assert sum(i["precio_total"] for i in items[:-1]) == pytest.approx(round(s.subtotal, 2), abs=0.001)
    for i in items:
        assert round(i["precio_total"], 2) == i["precio_total"]


def test_items_sin_itbms_ni_gastos():
    items = build_quote_items([Activity("Backend", "API", 10, 35.0)], [], 0, 0, False)
    assert items == [{"servicio": "Backend", "descripcion": "API (10 h)", "precio_total": 350.0}]
