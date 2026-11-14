"""Formatos de montos, fechas y números compartidos por la UI y el PDF (sin Qt)."""


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
