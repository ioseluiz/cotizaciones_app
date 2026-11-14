import jinja2

from utils.resource_path import resource_path
from utils.formatting import money
from utils.theme import ACCENTS, accent_for


def _render(clave):
    env = jinja2.Environment(loader=jinja2.FileSystemLoader(resource_path("templates")))
    env.filters["money"] = money
    accent = accent_for(clave)
    return env.get_template("quote_template.html").render(
        items=[], deliverables=[], accent=accent["base"], accent_tint=accent["tint"]
    )


def test_template_usa_color_de_cada_negocio():
    est = _render("ESTRUCTURAL")
    sof = _render("SOFTWARE")
    assert ACCENTS["ESTRUCTURAL"]["base"] in est and ACCENTS["SOFTWARE"]["base"] not in est
    assert ACCENTS["SOFTWARE"]["base"] in sof and ACCENTS["ESTRUCTURAL"]["base"] not in sof
    assert "#1A365D" not in est  # sin el color fijo anterior


def test_negocio_desconocido_usa_color_por_defecto():
    assert accent_for(None) == ACCENTS["ESTRUCTURAL"]
