from utils.formatting import money, fmt_date, parse_number


def test_money_con_separador_de_miles():
    assert money(1200) == "$1,200.00"
    assert money(1234567.891) == "$1,234,567.89"


def test_fmt_date_iso_a_dd_mm_aaaa():
    assert fmt_date("2026-11-14") == "14/11/2026"
    assert fmt_date("") == ""
    assert fmt_date("14/11/2026") == "14/11/2026"


def test_parse_number_acepta_formatos_de_la_ui():
    assert parse_number("$1,234.50") == 1234.5
    assert parse_number("8,5") == 8.5
    assert parse_number("") == 0.0


def test_html_body_quita_documento_de_qtextedit():
    from utils.formatting import html_body
    doc = ('<!DOCTYPE HTML><html><head><style type="text/css">p, li { white-space: pre-wrap; }</style></head>'
           '<body style=" font-family:\'Segoe UI\';">\n<p><b>Hola</b></p></body></html>')
    assert html_body(doc) == "<p><b>Hola</b></p>"
    assert html_body("<p>simple</p>") == "<p>simple</p>"
    assert html_body(None) == ""
    assert html_body(doc, keep_style=True) == "<div style=\"font-family:'Segoe UI';\"><p><b>Hola</b></p></div>"
