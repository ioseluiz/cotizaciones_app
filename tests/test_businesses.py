import os
import sqlite3

import pytest

import models.database as database
from models.business_model import BusinessModel, format_quote_number, render_message
from models.client_model import ClientModel
from models.quote_model import QuoteModel
from models.seed_data import TIPO_ESTRUCTURAL, TIPO_SOFTWARE

ITEMS = [{"servicio": "S", "descripcion": "", "precio_total": 10.0}]


@pytest.fixture
def db_path(tmp_path, monkeypatch):
    path = str(tmp_path / "test.db")
    monkeypatch.setattr(database, "get_db_path", lambda: path)
    return path


def _create_legacy_db(path):
    """Base de datos como la de la versión anterior: sin negocios ni numeración."""
    conn = sqlite3.connect(path)
    conn.executescript("""
        CREATE TABLE clientes (id INTEGER PRIMARY KEY AUTOINCREMENT, nombre TEXT NOT NULL, email TEXT, celular TEXT);
        CREATE TABLE cotizaciones (id INTEGER PRIMARY KEY AUTOINCREMENT, cliente_id INTEGER, tipo TEXT NOT NULL,
            fecha TEXT NOT NULL, proyecto TEXT NOT NULL, observaciones TEXT);
        CREATE TABLE detalles_cotizacion (id INTEGER PRIMARY KEY AUTOINCREMENT, cotizacion_id INTEGER,
            servicio TEXT NOT NULL, descripcion TEXT, precio_total REAL NOT NULL);
        INSERT INTO clientes (id, nombre) VALUES (1, 'Solo civil'), (2, 'Solo software'), (3, 'Ambos'), (4, 'Sin cotizaciones');
        INSERT INTO cotizaciones (id, cliente_id, tipo, fecha, proyecto) VALUES
            (1, 1, 'INGENIERO CIVIL', '2026-01-01', 'Casa'),
            (2, 2, 'DESARROLLADOR DE SOFTWARE', '2026-01-02', 'App'),
            (3, 3, 'INGENIERO CIVIL', '2026-01-03', 'Galera'),
            (4, 3, 'DESARROLLADOR DE SOFTWARE', '2026-01-04', 'Web');
    """)
    conn.commit()
    conn.close()


def test_migracion_de_base_existente(db_path):
    _create_legacy_db(db_path)
    db = database.Database()
    assert os.path.exists(db_path + ".bak-antes-de-negocios")

    cm, qm = ClientModel(db), QuoteModel(db)
    est = {c[1]: c[0] for c in cm.get_all_clients(TIPO_ESTRUCTURAL)}
    sw = {c[1]: c[0] for c in cm.get_all_clients(TIPO_SOFTWARE)}
    assert set(est) == {"Solo civil", "Ambos", "Sin cotizaciones"}
    assert set(sw) == {"Solo software", "Ambos", "Sin cotizaciones"}

    # Las cotizaciones conservan su número original y quedan con el cliente de su negocio
    est_quotes = {q[0]: q for q in qm.get_all_quotes(TIPO_ESTRUCTURAL)}
    sw_quotes = {q[0]: q for q in qm.get_all_quotes(TIPO_SOFTWARE)}
    assert set(est_quotes) == {1, 3} and set(sw_quotes) == {2, 4}
    assert all(q[1] == q[0] for q in list(est_quotes.values()) + list(sw_quotes.values()))
    assert qm.get_quote_by_id(4)[10] == sw["Ambos"]
    assert qm.get_quote_by_id(3)[10] == est["Ambos"]

    # Volver a abrir no duplica nada
    database.Database()
    assert len(cm.get_all_clients(TIPO_SOFTWARE)) == 3


def test_numeracion_independiente_por_negocio(db_path):
    _create_legacy_db(db_path)
    db = database.Database()
    qm = QuoteModel(db)
    new_est = qm.add_quote(TIPO_ESTRUCTURAL, 1, "2026-11-13", "Nueva", "", ITEMS)
    new_sw = qm.add_quote(TIPO_SOFTWARE, 2, "2026-11-13", "Nueva", "", ITEMS)
    new_sw2 = qm.add_quote(TIPO_SOFTWARE, 2, "2026-11-13", "Otra", "", ITEMS)
    assert qm.get_quote_by_id(new_est)[9] == 4   # máximo previo de Estructural = 3
    assert qm.get_quote_by_id(new_sw)[9] == 5    # máximo previo de Software = 4
    assert qm.get_quote_by_id(new_sw2)[9] == 6
    assert qm.get_quote_by_id(new_sw)[2] == "DESARROLLADOR DE SOFTWARE"


def test_base_nueva_empieza_en_uno(db_path):
    db = database.Database()
    cm, qm = ClientModel(db), QuoteModel(db)
    cid = cm.add_client(TIPO_SOFTWARE, "C", "", "")
    qid = qm.add_quote(TIPO_SOFTWARE, cid, "2026-11-13", "P", "", ITEMS)
    assert qm.get_quote_by_id(qid)[9] == 1
    assert cm.get_all_clients(TIPO_ESTRUCTURAL) == []


def test_datos_de_negocio(db_path):
    bm = BusinessModel(database.Database())
    assert [b[0] for b in bm.get_all()] == [TIPO_ESTRUCTURAL, TIPO_SOFTWARE]
    assert bm.get(TIPO_ESTRUCTURAL)["prefijo"] == "EST"
    bm.update(TIPO_SOFTWARE, {"prefijo": "DEV", "condiciones": "<p>x</p>"})
    assert bm.get(TIPO_SOFTWARE)["prefijo"] == "DEV"
    assert bm.get(TIPO_SOFTWARE)["condiciones"] == "<p>x</p>"


def test_formato_y_mensajes():
    assert format_quote_number("EST", 7) == "EST-0007"
    msg = render_message("Hola {cliente}, cotización {numero} de {proyecto} {otra}",
                         cliente="Ana", numero="SW-0001", proyecto="App")
    assert msg == "Hola Ana, cotización SW-0001 de App {otra}"
