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
