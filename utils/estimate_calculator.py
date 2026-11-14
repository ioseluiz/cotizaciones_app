"""Cálculo de estimados de proyecto: horas x tarifa por rol + ajustes.

Módulo puro (sin Qt ni base de datos) para poder probarlo fácilmente.

    costo_actividad = horas x tarifa
    costo_base      = suma(costo_actividad) + suma(gastos fijos)
    contingencia    = costo_base x contingencia%
    margen          = (costo_base + contingencia) x margen%
    subtotal        = costo_base + contingencia + margen
    itbms           = subtotal x 7%   (si aplica)
    total           = subtotal + itbms
"""
from dataclasses import dataclass, field
from typing import List

ITBMS_RATE = 0.07
SIN_FASE = "General"


@dataclass
class Activity:
    fase: str
    actividad: str
    horas: float
    tarifa: float
    rol: str = ""

    @property
    def costo(self) -> float:
        return self.horas * self.tarifa


@dataclass
class Expense:
    descripcion: str
    monto: float


@dataclass
class EstimateSummary:
    horas_totales: float = 0.0
    costo_horas: float = 0.0
    gastos: float = 0.0
    costo_base: float = 0.0
    contingencia: float = 0.0
    margen: float = 0.0
    subtotal: float = 0.0
    itbms: float = 0.0
    total: float = 0.0
    horas_por_rol: dict = field(default_factory=dict)


def calculate(activities: List[Activity], expenses: List[Expense],
              contingencia_pct: float = 0.0, margen_pct: float = 0.0,
              aplica_itbms: bool = False) -> EstimateSummary:
    s = EstimateSummary()
    for a in activities:
        s.horas_totales += a.horas
        s.costo_horas += a.costo
        key = a.rol or "Sin rol"
        s.horas_por_rol[key] = s.horas_por_rol.get(key, 0.0) + a.horas
    s.gastos = sum(e.monto for e in expenses)
    s.costo_base = s.costo_horas + s.gastos
    s.contingencia = s.costo_base * contingencia_pct / 100.0
    s.margen = (s.costo_base + s.contingencia) * margen_pct / 100.0
    s.subtotal = s.costo_base + s.contingencia + s.margen
    s.itbms = s.subtotal * ITBMS_RATE if aplica_itbms else 0.0
    s.total = s.subtotal + s.itbms
    return s


def _fmt_horas(h: float) -> str:
    return f"{h:g}"


def build_quote_items(activities: List[Activity], expenses: List[Expense],
                      contingencia_pct: float = 0.0, margen_pct: float = 0.0,
                      aplica_itbms: bool = False) -> List[dict]:
    """Convierte el estimado en items de cotización (servicio, descripcion,
    precio_total): un item por fase, uno de gastos y uno de ITBMS.

    La contingencia y el margen se reparten proporcionalmente entre fases y
    gastos, de modo que la suma de items sea exactamente el total del estimado.
    """
    summary = calculate(activities, expenses, contingencia_pct, margen_pct, aplica_itbms)
    factor = summary.subtotal / summary.costo_base if summary.costo_base else 1.0

    # Agrupar por fase conservando el orden de aparición
    phases = {}
    for a in activities:
        fase = (a.fase or "").strip() or SIN_FASE
        phases.setdefault(fase, []).append(a)

    raw_items = []
    for fase, acts in phases.items():
        horas = sum(a.horas for a in acts)
        nombres = "; ".join(a.actividad for a in acts if a.actividad)
        descripcion = f"{nombres} ({_fmt_horas(horas)} h)" if nombres else f"{_fmt_horas(horas)} h"
        raw_items.append({
            "servicio": fase,
            "descripcion": descripcion,
            "precio_total": sum(a.costo for a in acts) * factor,
        })

    if expenses and summary.gastos:
        raw_items.append({
            "servicio": "Gastos",
            "descripcion": "; ".join(e.descripcion for e in expenses if e.descripcion),
            "precio_total": summary.gastos * factor,
        })

    # Redondeo a centavos, ajustando el último item para que cuadre el subtotal
    items = [dict(it, precio_total=round(it["precio_total"], 2)) for it in raw_items]
    if items:
        diff = round(round(summary.subtotal, 2) - sum(it["precio_total"] for it in items), 2)
        items[-1]["precio_total"] = round(items[-1]["precio_total"] + diff, 2)

    if aplica_itbms and summary.itbms:
        items.append({
            "servicio": "ITBMS (7%)",
            "descripcion": "Impuesto de Transferencia de Bienes Muebles y Servicios",
            "precio_total": round(round(summary.total, 2) - round(summary.subtotal, 2), 2),
        })
    return items
