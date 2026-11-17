"""Opciones para el cliente: adicionales y alternativas dentro de una cotización."""
import sqlite3

import jinja2
import pytest

import models.database as database
from models.database import Database
from models.estimate_model import EstimateModel
from models.quote_model import QuoteModel
from models.seed_data import TIPO_ESTRUCTURAL
from utils.estimate_calculator import (
    Activity, Expense, OPCION_ADICIONAL, OPCION_ALTERNATIVA, build_quote_groups, build_quote_items,
    split_by_option,
)
from utils.formatting import money
from utils.resource_path import resource_path

OPCIONES = [
    {"nombre": "Supervisión", "tipo": OPCION_ADICIONAL, "descripcion": "Visitas semanales"},
    {"nombre": "Losa postensada", "tipo": OPCION_ALTERNATIVA, "descripcion": ""},
]


@pytest.fixture
def db(tmp_path, monkeypatch):
    path = str(tmp_path / "test.db")
    monkeypatch.setattr(database, "get_db_path", lambda: path)
    d = Database()
    with d.get_connection() as conn:
        conn.execute("INSERT INTO clientes (nombre, negocio) VALUES ('Cliente', 'ESTRUCTURAL')")
        conn.commit()
    return d


# ------------------------------------------------------------------ cálculo
def test_grupos_separan_base_y_opciones():
    acts = [
        Activity("Diseño", "Cálculo", 10, 40.0),
        Activity("Supervisión", "Visitas", 8, 33.33, opcion=0),
        Activity("Diseño PT", "Cálculo PT", 5, 45.0, opcion=1),
    ]
    exps = [Expense("Planos", 50.0), Expense("Transporte", 20.0, opcion=0)]
    g = build_quote_groups(acts, exps, OPCIONES, 10, 15, True)

    assert [i["servicio"] for i in g["base"]["items"]] == ["Diseño", "Gastos", "ITBMS (7%)"]
    assert all(i["opcion"] is None for i in g["base"]["items"])
    sup, pt = g["opciones"]
    assert sup["nombre"] == "Supervisión" and sup["tipo"] == OPCION_ADICIONAL
    assert [i["servicio"] for i in sup["items"]] == ["Supervisión", "Gastos", "ITBMS (7%)"]
    assert all(i["opcion"] == 0 for i in sup["items"])
    assert all(i["opcion"] == 1 for i in pt["items"])
    # Cada grupo cuadra al centavo con su propio total (incluye ITBMS)
    for group in [g["base"], sup, pt]:
        assert sum(i["precio_total"] for i in group["items"]) == pytest.approx(round(group["summary"].total, 2))


def test_sin_opciones_igual_que_antes():
    acts = [Activity("A", "x", 3, 20.0), Activity("B", "y", 2, 15.5)]
    exps = [Expense("G", 10.0)]
    g = build_quote_groups(acts, exps, [], 10, 20, True)
    expected = build_quote_items(acts, exps, 10, 20, True)
    assert [{k: v for k, v in i.items() if k != "opcion"} for i in g["base"]["items"]] == expected
    assert g["opciones"] == []


def test_opcion_inexistente_cuenta_como_base():
    acts = [Activity("A", "x", 1, 100.0), Activity("B", "y", 1, 50.0, opcion=5)]
    g = build_quote_groups(acts, [], OPCIONES[:1], 0, 0, False)
    assert g["base"]["summary"].total == pytest.approx(150.0)
    assert g["opciones"][0]["items"] == []


def test_split_by_option():
    items = [{"opcion": None, "precio_total": 1}, {"opcion": 0, "precio_total": 2}, {"opcion": 9, "precio_total": 3}]
    base, groups = split_by_option(items, 1)
    assert [i["precio_total"] for i in base] == [1, 3]
    assert [i["precio_total"] for i in groups[0]] == [2]


# ------------------------------------------------------------------- modelos
def test_estimado_con_opciones_roundtrip(db):
    em = EstimateModel(db)
    data = {
        "cliente_id": 1, "tipo": TIPO_ESTRUCTURAL, "proyecto": "Casa", "fecha": "2026-11-16",
        "actividades": [
            {"fase": "Diseño", "actividad": "Cálculo", "horas": 10, "tarifa_hora": 40},
            {"fase": "Sup", "actividad": "Visitas", "horas": 8, "tarifa_hora": 30, "opcion": 0},
        ],
        "gastos": [{"descripcion": "Transporte", "monto": 20, "opcion": 1}],
        "entregables": [],
        "opciones": OPCIONES,
    }
    eid = em.add_estimate(data)
    loaded = em.get_estimate(eid)
    assert loaded["opciones"] == OPCIONES
    assert [a["opcion"] for a in loaded["actividades"]] == [None, 0]
    assert loaded["gastos"][0]["opcion"] == 1

    data["opciones"] = OPCIONES[:1]
    data["gastos"] = []
    em.update_estimate(eid, data)
    assert em.get_estimate(eid)["opciones"] == OPCIONES[:1]
    em.delete_estimate(eid)
    with db.get_connection() as conn:
        assert conn.execute("SELECT COUNT(*) FROM estimado_opciones").fetchone()[0] == 0


def test_cotizacion_con_opciones(db):
    qm = QuoteModel(db)
    items = [
        {"servicio": "Diseño", "descripcion": "", "precio_total": 100.0},
        {"servicio": "Supervisión", "descripcion": "", "precio_total": 40.0, "opcion": 0},
    ]
    qid = qm.add_quote(TIPO_ESTRUCTURAL, 1, "2026-11-16", "Casa", "", items, opciones=OPCIONES[:1])
    assert qm.get_quote_options(qid) == OPCIONES[:1]
    assert [r[4] for r in qm.get_quote_items(qid)] == [None, 0]

    # Sin pasar opciones se conservan; con lista vacía se quitan
    qm.update_quote(qid, 1, "2026-11-16", "Casa", "", items)
    assert qm.get_quote_options(qid) == OPCIONES[:1]
    qm.update_quote(qid, 1, "2026-11-16", "Casa", "", items[:1], opciones=[])
    assert qm.get_quote_options(qid) == []

    qm.update_quote(qid, 1, "2026-11-16", "Casa", "", items, opciones=OPCIONES)
    qm.delete_quote(qid)
    assert qm.get_quote_options(qid) == []


def test_bd_anterior_queda_toda_en_base(tmp_path, monkeypatch):
    """Una BD de la versión 1.1.0 (sin columnas de opción) se migra sin cambiar montos."""
    path = str(tmp_path / "old.db")
    monkeypatch.setattr(database, "get_db_path", lambda: path)
    Database()
    conn = sqlite3.connect(path)
    # Simular el esquema anterior: recrear detalles_cotizacion sin la columna opcion
    conn.executescript("""
        DROP TABLE detalles_cotizacion;
        CREATE TABLE detalles_cotizacion (id INTEGER PRIMARY KEY AUTOINCREMENT, cotizacion_id INTEGER,
            servicio TEXT NOT NULL, descripcion TEXT, precio_total REAL NOT NULL);
        INSERT INTO clientes (nombre, negocio) VALUES ('C', 'ESTRUCTURAL');
        INSERT INTO cotizaciones (cliente_id, tipo, fecha, proyecto, negocio, numero)
            VALUES (1, 'INGENIERO CIVIL', '2026-10-25', 'P', 'ESTRUCTURAL', 1);
        INSERT INTO detalles_cotizacion (cotizacion_id, servicio, descripcion, precio_total)
            VALUES (1, 'A', '', 300.0), (1, 'B', '', 325.0);
    """)
    conn.commit()
    conn.close()

    d = Database()
    qm = QuoteModel(d)
    rows = qm.get_quote_items(1)
    assert [r[4] for r in rows] == [None, None]
    assert sum(r[3] for r in rows) == pytest.approx(625.0)
    assert qm.get_quote_options(1) == []


# ----------------------------------------------------------------------- PDF
def _render(**kwargs):
    env = jinja2.Environment(loader=jinja2.FileSystemLoader(resource_path("templates")))
    env.filters["money"] = money
    params = dict(items=[(1, "Diseño", "", 100.0, None)], deliverables=[], accent="#123456",
                  accent_tint="#EEEEEE", total="$100.00", options=[])
    params.update(kwargs)
    return env.get_template("quote_template.html").render(**params)


def test_pdf_sin_opciones_conserva_gran_total():
    html = _render()
    assert "GRAN TOTAL" in html
    assert "ALCANCE BASE" not in html and "aprobada" not in html


def test_pdf_con_opciones_muestra_cada_seccion():
    html = _render(options=[{
        "tipo": "Adicional", "nombre": "Supervisión", "descripcion": "Visitas semanales",
        "items": [(2, "Supervisión", "8 visitas", 640.0, 0)], "precio": "$640.00", "total": "$740.00",
    }])
    assert "TOTAL BASE" in html and "GRAN TOTAL" not in html
    assert "Adicional: Supervisión" in html and "Visitas semanales" in html
    assert "+ $640.00" in html and "$740.00" in html
    assert "aprobada" in html
