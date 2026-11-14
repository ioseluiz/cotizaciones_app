import pytest

import models.database as database
from models.database import Database
from models.estimate_model import EstimateModel
from models.quote_model import QuoteModel
from models.role_model import RoleModel
from models.template_model import TemplateModel
from models.seed_data import TIPO_ESTRUCTURAL, TIPO_SOFTWARE


@pytest.fixture
def db(tmp_path, monkeypatch):
    monkeypatch.setattr(database, "get_db_path", lambda: str(tmp_path / "test.db"))
    d = Database()
    with d.get_connection() as conn:
        conn.execute("INSERT INTO clientes (nombre, email, celular, negocio) VALUES ('Cliente', '', '', 'SOFTWARE')")
        conn.commit()
    return d


def test_semillas_y_reinicio_idempotente(db):
    roles = RoleModel(db).get_all_roles()
    templates = TemplateModel(db).get_templates()
    assert len(roles) > 0
    assert {t[2] for t in templates} == {TIPO_SOFTWARE, TIPO_ESTRUCTURAL}
    Database()  # volver a inicializar no duplica datos
    assert len(RoleModel(db).get_all_roles()) == len(roles)
    assert len(TemplateModel(db).get_templates()) == len(templates)


def test_plantilla_trae_tarifa_del_rol(db):
    tm = TemplateModel(db)
    tpl_id = tm.get_templates(TIPO_ESTRUCTURAL)[0][0]
    tpl = tm.get_template(tpl_id)
    assert tpl["actividades"] and tpl["entregables"]
    assert all(a["tarifa_hora"] > 0 for a in tpl["actividades"])


def test_crud_estimado_y_vinculo_con_cotizacion(db):
    em = EstimateModel(db)
    data = {
        "cliente_id": 1, "tipo": TIPO_SOFTWARE, "proyecto": "App", "fecha": "2026-11-13",
        "contingencia_pct": 10, "margen_pct": 20, "aplica_itbms": True, "notas": "",
        "actividades": [{"fase": "Backend", "actividad": "API", "rol_id": 1, "horas": 10, "tarifa_hora": 35}],
        "gastos": [{"descripcion": "Hosting", "monto": 50}],
        "entregables": ["Código fuente", "Manual"],
    }
    eid = em.add_estimate(data)
    loaded = em.get_estimate(eid)
    assert loaded["actividades"][0]["tarifa_hora"] == 35
    assert loaded["entregables"] == ["Código fuente", "Manual"]
    assert loaded["aplica_itbms"] is True

    data["entregables"] = ["Solo uno"]
    em.update_estimate(eid, data)
    assert em.get_estimate(eid)["entregables"] == ["Solo uno"]

    qm = QuoteModel(db)
    items = [{"servicio": "Backend", "descripcion": "API", "precio_total": 100.0}]
    qid = qm.add_quote(TIPO_SOFTWARE, 1, "2026-11-13", "App", "", items, ["E1", "E2"])
    em.link_quote(eid, qid)
    assert qm.get_quote_deliverables(qid) == ["E1", "E2"]

    # Editar la cotización sin pasar entregables los conserva
    qm.update_quote(qid, 1, "2026-11-13", "App", "", items)
    assert qm.get_quote_deliverables(qid) == ["E1", "E2"]

    qm.delete_quote(qid)
    assert qm.get_quote_deliverables(qid) == []
    assert em.get_estimate(eid)["cotizacion_id"] is None

    em.delete_estimate(eid)
    assert em.get_estimate(eid) is None
