"""Formatos de montos, fechas y números compartidos por la UI y el PDF (sin Qt)."""
import re


def money(value):
    return f"${value:,.2f}"


def fmt_date(iso):
    """'2026-11-13' -> '13/11/2026' (deja el texto igual si no es una fecha ISO)."""
    parts = str(iso or "").split("-")
    return f"{parts[2]}/{parts[1]}/{parts[0]}" if len(parts) == 3 else str(iso or "")


def parse_number(text):
    """Acepta '1,234.50', '$1234.5', '8,5' (coma decimal) o vacío."""
    t = str(text or "").strip().replace("$", "").replace(" ", "")
    if not t:
        return 0.0
    if "," in t and "." in t:
        t = t.replace(",", "")
    elif "," in t:
        # Una sola coma con 1-2 decimales => coma decimal; si no, separador de miles
        head, _, tail = t.rpartition(",")
        t = f"{head.replace(',', '')}.{tail}" if len(tail) <= 2 else t.replace(",", "")
    try:
        return float(t)
    except ValueError:
        return 0.0


def html_body(html, keep_style=False):
    """Contenido del <body> de un documento HTML completo (como el que genera
    QTextEdit.toHtml); devuelve el texto igual si no es un documento completo.

    Sirve para incrustar ese HTML dentro de otro: el <head> con estilos propios de
    QTextEdit desalinea el resto del documento al generar el PDF. Con keep_style
    se conserva el estilo del <body> (tamaño de letra base) en un <div>."""
    m = re.search(r"<body([^>]*)>(.*)</body>", html or "", re.S | re.I)
    if not m:
        return html or ""
    content = m.group(2).strip()
    style = re.search(r'style="([^"]*)"', m.group(1))
    if keep_style and style and style.group(1).strip():
        return f'<div style="{style.group(1).strip()}">{content}</div>'
    return content
