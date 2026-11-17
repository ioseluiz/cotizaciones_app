"""Anexos del PDF: archivos PDF, imágenes y páginas de texto."""
import os

import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import models.database as database  # noqa: E402
from models.database import Database  # noqa: E402
from models.annex_model import AnnexModel, TIPO_PDF, TIPO_IMAGEN, TIPO_TEXTO, file_type  # noqa: E402
from models.quote_model import QuoteModel  # noqa: E402
from models.seed_data import TIPO_ESTRUCTURAL  # noqa: E402

ITEMS = [{"servicio": "Diseño", "descripcion": "", "precio_total": 100.0}]


@pytest.fixture
def db(tmp_path, monkeypatch):
    path = str(tmp_path / "data" / "test.db")
    os.makedirs(os.path.dirname(path))
    monkeypatch.setattr(database, "get_db_path", lambda: path)
    d = Database()
    with d.get_connection() as conn:
        conn.execute("INSERT INTO clientes (nombre, negocio) VALUES ('Cliente', 'ESTRUCTURAL')")
        conn.commit()
    return d


@pytest.fixture(scope="module")
def qapp():
    from PyQt6.QtWidgets import QApplication
    return QApplication.instance() or QApplication([])


def _make_pdf(path, pages):
    from pypdf import PdfWriter
    w = PdfWriter()
    for _ in range(pages):
        w.add_blank_page(width=595, height=842)
    with open(path, "wb") as f:
        w.write(f)
    return path


def _make_png(path, qapp):
    from PyQt6.QtGui import QImage, QColor
    img = QImage(400, 200, QImage.Format.Format_RGB32)
    img.fill(QColor("#3366CC"))
    assert img.save(path)
    return path


def test_tipo_por_extension():
    assert file_type("a.PDF") == TIPO_PDF
    assert file_type("diagrama.jpeg") == TIPO_IMAGEN
    assert file_type("notas.docx") is None


def test_anexos_se_copian_y_se_borran(db, tmp_path):
    am = AnnexModel(db)
    qid = QuoteModel(db).add_quote(TIPO_ESTRUCTURAL, 1, "2026-11-16", "P", "", ITEMS)
    src = _make_pdf(str(tmp_path / "planos.pdf"), 2)

    annex_id = am.add_file(src, quote_id=qid)
    annex = am.get(annex_id)
    assert annex["titulo"] == "planos" and annex["tipo"] == TIPO_PDF
    copy = am.file_path(annex)
    assert os.path.dirname(copy) == os.path.join(os.path.dirname(db.db_path), "anexos")
    os.remove(src)  # el original puede desaparecer: la copia sigue
    assert os.path.exists(copy)

    am.delete(annex_id)
    assert not os.path.exists(copy) and am.get(annex_id) is None

    with pytest.raises(ValueError):
        am.add_file(str(tmp_path / "notas.docx"), quote_id=qid)


def test_fijos_del_negocio_exclusion_y_orden(db):
    am = AnnexModel(db)
    qid = QuoteModel(db).add_quote(TIPO_ESTRUCTURAL, 1, "2026-11-16", "P", "", ITEMS)
    portafolio = am.add_text("Portafolio", "<p>x</p>", negocio=TIPO_ESTRUCTURAL)
    terminos = am.add_text("Términos", "<p>y</p>", negocio=TIPO_ESTRUCTURAL)
    am.add_text("Otro negocio", "<p>z</p>", negocio="SOFTWARE")
    alcance = am.add_text("Alcance", "<p>a</p>", quote_id=qid)
    metodo = am.add_text("Metodología", "<p>b</p>", quote_id=qid)

    titles = [a["titulo"] for a in am.annexes_for_pdf(qid, TIPO_ESTRUCTURAL)]
    assert titles == ["Portafolio", "Términos", "Alcance", "Metodología"]

    am.set_excluded(qid, portafolio, True)
    am.reorder([metodo, alcance])
    titles = [a["titulo"] for a in am.annexes_for_pdf(qid, TIPO_ESTRUCTURAL)]
    assert titles == ["Términos", "Metodología", "Alcance"]

    am.set_excluded(qid, portafolio, False)
    assert am.get_excluded(qid) == set()
    assert am.get(terminos)["tipo"] == TIPO_TEXTO

    am.delete_for_quote(qid)
    assert am.get_quote_annexes(qid) == []
    assert len(am.get_business_annexes(TIPO_ESTRUCTURAL)) == 2


def test_pdf_con_anexos(db, tmp_path, qapp):
    from pypdf import PdfReader
    from utils.pdf_generator import PDFGenerator

    am = AnnexModel(db)
    qm = QuoteModel(db)
    qid = qm.add_quote(TIPO_ESTRUCTURAL, 1, "2026-11-16", "P", "", ITEMS)
    am.add_file(_make_pdf(str(tmp_path / "planos.pdf"), 3), quote_id=qid)
    am.add_file(_make_png(str(tmp_path / "diagrama.png"), qapp), "Diagrama", quote_id=qid)
    am.add_text("Alcance detallado", "<p><b>Incluye</b> todo</p>", quote_id=qid)
    annexes = [dict(a, path=am.file_path(a)) for a in am.annexes_for_pdf(qid, TIPO_ESTRUCTURAL)]

    quote = qm.get_quote_by_id(qid)
    plain = str(tmp_path / "sin.pdf")
    full = str(tmp_path / "con.pdf")
    PDFGenerator().generate(quote, qm.get_quote_items(qid), plain, [], {"clave": TIPO_ESTRUCTURAL})
    PDFGenerator().generate(quote, qm.get_quote_items(qid), full, [], {"clave": TIPO_ESTRUCTURAL},
                            annexes=annexes)

    base_pages = len(PdfReader(plain).pages)
    reader = PdfReader(full)
    assert len(reader.pages) == base_pages + 3 + 1 + 1
    text = "".join(p.extract_text() or "" for p in reader.pages)
    assert "Anexo 1: planos" in text  # listado en la cotización
    assert "ANEXO 3: ALCANCE DETALLADO" in text.upper()


def test_pdf_anexo_faltante_da_error_claro(db, tmp_path, qapp):
    from utils.pdf_generator import PDFGenerator
    qm = QuoteModel(db)
    qid = qm.add_quote(TIPO_ESTRUCTURAL, 1, "2026-11-16", "P", "", ITEMS)
    annexes = [{"tipo": TIPO_PDF, "titulo": "Planos", "path": str(tmp_path / "no_existe.pdf")}]
    with pytest.raises(ValueError, match="Planos"):
        PDFGenerator().generate(qm.get_quote_by_id(qid), qm.get_quote_items(qid), str(tmp_path / "x.pdf"),
                                annexes=annexes)
