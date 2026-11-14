"""Tema visual de la aplicación (claro profesional con acento por negocio).

Todos los colores salen de aquí. Las vistas solo marcan intención con
propiedades dinámicas, por ejemplo:

    btn.setProperty("variant", "primary")   # primary | danger | ghost
    lbl.setProperty("role", "title")        # title | subtitle | muted | total | chip
"""
import os
import tempfile

from PyQt6.QtCore import Qt, QEvent, QObject
from PyQt6.QtGui import QColor, QPalette, QFont
from PyQt6.QtWidgets import QApplication, QComboBox, QStyledItemDelegate

# Neutros
BG = "#F5F7FA"
SURFACE = "#FFFFFF"
SURFACE_ALT = "#F8FAFC"
HEADER_BG = "#F1F5F9"
BORDER = "#E2E8F0"
BORDER_STRONG = "#CBD5E1"
TEXT = "#1F2937"
TEXT_MUTED = "#64748B"
TEXT_DISABLED = "#94A3B8"
DANGER = "#DC2626"
DANGER_SOFT = "#FEE2E2"
DANGER_BORDER = "#FCA5A5"
SUCCESS = "#16A34A"

ACCENTS = {
    "ESTRUCTURAL": {
        "base": "#1E3A8A", "hover": "#1E40AF", "pressed": "#172554",
        "soft": "#DBEAFE", "sidebar": "#172554", "sidebar_alt": "#1E3A8A",
    },
    "SOFTWARE": {
        "base": "#0F766E", "hover": "#0D9488", "pressed": "#115E59",
        "soft": "#CCFBF1", "sidebar": "#134E4A", "sidebar_alt": "#0F766E",
    },
}
DEFAULT_ACCENT = ACCENTS["ESTRUCTURAL"]


def accent_for(clave):
    return ACCENTS.get(clave, DEFAULT_ACCENT)


def _palette(accent):
    p = QPalette()
    roles = {
        QPalette.ColorRole.Window: BG,
        QPalette.ColorRole.WindowText: TEXT,
        QPalette.ColorRole.Base: SURFACE,
        QPalette.ColorRole.AlternateBase: SURFACE_ALT,
        QPalette.ColorRole.Text: TEXT,
        QPalette.ColorRole.Button: SURFACE,
        QPalette.ColorRole.ButtonText: TEXT,
        QPalette.ColorRole.ToolTipBase: TEXT,
        QPalette.ColorRole.ToolTipText: SURFACE,
        QPalette.ColorRole.PlaceholderText: TEXT_DISABLED,
        QPalette.ColorRole.Highlight: accent["base"],
        QPalette.ColorRole.HighlightedText: "#FFFFFF",
        QPalette.ColorRole.Link: accent["base"],
    }
    for role, color in roles.items():
        p.setColor(role, QColor(color))
    for role in (QPalette.ColorRole.Text, QPalette.ColorRole.ButtonText, QPalette.ColorRole.WindowText):
        p.setColor(QPalette.ColorGroup.Disabled, role, QColor(TEXT_DISABLED))
    return p


_ARROW_SVG = (
    '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="{color}" '
    'stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><path d="{path}"/></svg>'
)


def _arrow_icons():
    """Escribe las flechas de combos/spinbox como SVG temporales (QSS solo acepta rutas)."""
    folder = os.path.join(tempfile.gettempdir(), "cotizacionesapp_theme")
    os.makedirs(folder, exist_ok=True)
    specs = {
        "down": ("m6 9 6 6 6-6", TEXT_MUTED),
        "up": ("m6 15 6-6 6 6", TEXT_MUTED),
        "down_white": ("m6 9 6 6 6-6", "#FFFFFF"),
        "left_white": ("m15 6-6 6 6 6", "#FFFFFF"),
        "right_white": ("m9 6 6 6-6 6", "#FFFFFF"),
    }
    paths = {}
    for name, (path, color) in specs.items():
        file_path = os.path.join(folder, f"{name}.svg")
        try:
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(_ARROW_SVG.format(color=color, path=path))
        except OSError:
            pass
        paths[name] = file_path.replace("\\", "/")
    return paths


def stylesheet(accent):
    a = accent
    ar = _arrow_icons()
    return f"""
* {{ outline: none; }}
QWidget {{ color: {TEXT}; }}
QMainWindow, QDialog, #page, #pageContent {{ background: {BG}; }}
QScrollArea, QScrollArea > QWidget > QWidget {{ background: transparent; border: none; }}
QToolTip {{ background: {TEXT}; color: white; border: none; padding: 4px 8px; }}

/* ---------- Barra lateral ---------- */
#sidebar {{ background: {a['sidebar']}; }}
#sidebar QLabel {{ color: #CBD5E1; }}
#sidebar QLabel#appTitle {{ color: white; font-size: 12pt; font-weight: 700; }}
#sidebar QLabel#sectionLabel {{ color: #94A3B8; font-size: 8pt; font-weight: 600; letter-spacing: 1px; }}
#sidebar QComboBox {{
    background: {a['sidebar_alt']}; color: white; border: 1px solid rgba(255,255,255,0.25);
    border-radius: 6px; padding: 6px 8px; font-weight: 600;
}}
#sidebar QComboBox QAbstractItemView {{ background: white; color: {TEXT}; selection-background-color: {a['soft']};
    selection-color: {TEXT}; font-weight: 500; }}
#sidebar QPushButton, #sidebar QToolButton {{
    text-align: left; padding: 9px 12px; border: none; border-radius: 8px;
    color: #E2E8F0; background: transparent; font-weight: 500;
}}
#sidebar QPushButton:hover, #sidebar QToolButton:hover {{ background: rgba(255,255,255,0.10); }}
#sidebar QPushButton:checked {{ background: rgba(255,255,255,0.18); color: white; font-weight: 700; }}
#sidebar QToolButton#businessBadge {{
    background: {a['sidebar_alt']}; color: white; font-weight: 700; border: 1px solid rgba(255,255,255,0.25);
}}

/* ---------- Tipografía ---------- */
QLabel[role="title"] {{ font-size: 15pt; font-weight: 700; color: {TEXT}; }}
QLabel[role="subtitle"] {{ font-size: 11pt; font-weight: 600; color: {TEXT}; }}
QLabel[role="muted"] {{ color: {TEXT_MUTED}; }}
QLabel[role="total"] {{ font-size: 17pt; font-weight: 700; color: {a['base']}; }}
QLabel[role="chip"] {{
    background: {a['soft']}; color: {a['base']}; border-radius: 10px; padding: 2px 10px; font-weight: 600;
}}
QLabel[role="chip-edit"] {{
    background: #FEF3C7; color: #92400E; border-radius: 10px; padding: 2px 10px; font-weight: 600;
}}
QLabel[role="amount"] {{ font-weight: 600; }}

/* ---------- Tarjetas ---------- */
QGroupBox {{
    background: {SURFACE}; border: 1px solid {BORDER}; border-radius: 10px;
    margin-top: 0px; padding: 34px 12px 12px 12px; font-weight: 600;
}}
QGroupBox::title {{
    subcontrol-origin: padding; subcontrol-position: top left;
    left: 14px; top: 10px; color: {TEXT}; font-size: 10.5pt;
}}
QFrame#card {{ background: {SURFACE}; border: 1px solid {BORDER}; border-radius: 10px; }}
QFrame#actionBar {{ background: {SURFACE}; border-top: 1px solid {BORDER}; }}
QFrame#listPanel {{ background: {SURFACE}; border-right: 1px solid {BORDER}; }}

/* ---------- Campos ---------- */
QLineEdit, QComboBox, QDateEdit, QDoubleSpinBox, QSpinBox, QTextEdit, QPlainTextEdit, QListWidget {{
    background: {SURFACE}; border: 1px solid {BORDER_STRONG}; border-radius: 6px;
    padding: 5px 8px; selection-background-color: {a['base']}; selection-color: white;
}}
QTextEdit, QPlainTextEdit, QListWidget {{ padding: 4px; }}
QLineEdit:focus, QComboBox:focus, QDateEdit:focus, QDoubleSpinBox:focus, QSpinBox:focus,
QTextEdit:focus, QPlainTextEdit:focus, QListWidget:focus {{ border: 1px solid {a['base']}; }}
QLineEdit:disabled, QComboBox:disabled {{ background: {HEADER_BG}; color: {TEXT_DISABLED}; }}
QLineEdit[search="true"] {{ background: {SURFACE_ALT}; border-radius: 16px; padding: 6px 12px; }}
QComboBox QAbstractItemView {{
    background: white; color: {TEXT}; border: 1px solid {BORDER}; outline: 0; padding: 2px;
    selection-background-color: {a['soft']}; selection-color: {TEXT};
}}
QComboBox QAbstractItemView::item {{ color: {TEXT}; background: white; min-height: 26px; padding: 2px 8px; }}
QComboBox QAbstractItemView::item:hover, QComboBox QAbstractItemView::item:selected {{
    color: {TEXT}; background: {a['soft']};
}}
QComboBox::drop-down, QDateEdit::drop-down {{
    subcontrol-origin: padding; subcontrol-position: center right; width: 24px; border: none;
}}
QComboBox::down-arrow, QDateEdit::down-arrow {{ image: url({ar['down']}); width: 12px; height: 12px; }}
#sidebar QComboBox::down-arrow {{ image: url({ar['down_white']}); }}
QAbstractSpinBox {{ padding-right: 22px; }}
QAbstractSpinBox::up-button, QAbstractSpinBox::down-button {{
    subcontrol-origin: border; width: 20px; border: none; background: transparent;
}}
QAbstractSpinBox::up-button {{ subcontrol-position: top right; }}
QAbstractSpinBox::down-button {{ subcontrol-position: bottom right; }}
QAbstractSpinBox::up-arrow {{ image: url({ar['up']}); width: 10px; height: 10px; }}
QAbstractSpinBox::down-arrow {{ image: url({ar['down']}); width: 10px; height: 10px; }}
QDateEdit {{ padding-right: 4px; }}
QTableWidget QComboBox {{ border: none; border-radius: 0; background: transparent; padding: 2px 6px; }}
QTableWidget QLineEdit {{ border: 1px solid {a['base']}; border-radius: 0; padding: 2px 4px; }}
QListWidget::item {{ padding: 5px 4px; border-radius: 4px; }}
QListWidget::item:selected {{ background: {a['soft']}; color: {TEXT}; }}
QCheckBox {{ spacing: 8px; }}

/* ---------- Botones ---------- */
QPushButton {{
    background: {SURFACE}; border: 1px solid {BORDER_STRONG}; border-radius: 6px;
    padding: 6px 14px; color: {TEXT}; font-weight: 500;
}}
QPushButton:hover {{ background: {SURFACE_ALT}; border-color: #94A3B8; }}
QPushButton:pressed {{ background: {BORDER}; }}
QPushButton:disabled {{ color: {TEXT_DISABLED}; background: {HEADER_BG}; border-color: {BORDER}; }}
QPushButton[variant="primary"] {{ background: {a['base']}; border: 1px solid {a['base']}; color: white; font-weight: 600; }}
QPushButton[variant="primary"]:hover {{ background: {a['hover']}; border-color: {a['hover']}; }}
QPushButton[variant="primary"]:pressed {{ background: {a['pressed']}; }}
QPushButton[variant="primary"]:disabled {{ background: {BORDER_STRONG}; border-color: {BORDER_STRONG}; color: white; }}
QPushButton[variant="danger"] {{ color: {DANGER}; border-color: {DANGER_BORDER}; }}
QPushButton[variant="danger"]:hover {{ background: {DANGER_SOFT}; }}
QPushButton[variant="danger"]:disabled {{ color: {TEXT_DISABLED}; border-color: {BORDER}; background: {HEADER_BG}; }}
QPushButton[variant="ghost"] {{ background: transparent; border: none; color: {a['base']}; font-weight: 600; }}
QPushButton[variant="ghost"]:hover {{ background: {a['soft']}; }}
QPushButton[variant="ghost"]:disabled {{ color: {TEXT_DISABLED}; background: transparent; }}

/* ---------- Tablas ---------- */
QTableWidget, QTableView {{
    background: {SURFACE}; alternate-background-color: {SURFACE_ALT}; border: 1px solid {BORDER};
    border-radius: 8px; gridline-color: #EEF2F6;
    selection-background-color: {a['soft']}; selection-color: {TEXT};
}}
QTableWidget::item {{ padding: 0 6px; }}
QHeaderView::section {{
    background: {HEADER_BG}; color: {TEXT_MUTED}; font-weight: 600; border: none;
    border-bottom: 1px solid {BORDER}; padding: 6px 8px;
}}
QTableCornerButton::section {{ background: {HEADER_BG}; border: none; }}

/* ---------- Pestañas internas ---------- */
QTabWidget::pane {{ border: none; }}
QTabBar::tab {{
    background: transparent; padding: 8px 18px; border: none; border-bottom: 2px solid transparent;
    color: {TEXT_MUTED}; font-weight: 600;
}}
QTabBar::tab:selected {{ color: {a['base']}; border-bottom: 2px solid {a['base']}; }}
QTabBar::tab:hover {{ color: {TEXT}; }}

/* ---------- Scroll, splitter, status ---------- */
QScrollBar:vertical {{ background: transparent; width: 10px; margin: 2px; }}
QScrollBar:horizontal {{ background: transparent; height: 10px; margin: 2px; }}
QScrollBar::handle:vertical {{ background: {BORDER_STRONG}; border-radius: 4px; min-height: 30px; }}
QScrollBar::handle:horizontal {{ background: {BORDER_STRONG}; border-radius: 4px; min-width: 30px; }}
QScrollBar::handle:hover {{ background: {TEXT_DISABLED}; }}
QScrollBar::add-line, QScrollBar::sub-line {{ width: 0; height: 0; }}
QScrollBar::add-page, QScrollBar::sub-page {{ background: none; }}
QSplitter::handle {{ background: {BORDER}; }}
QSplitter::handle:horizontal {{ width: 1px; }}
QStatusBar {{ background: {SURFACE}; border-top: 1px solid {BORDER}; color: {TEXT_MUTED}; }}
QStatusBar QLabel {{ color: {TEXT_MUTED}; padding: 0 8px; }}
QCalendarWidget QWidget#qt_calendar_navigationbar {{ background: {a['base']}; }}
QCalendarWidget QToolButton {{
    color: white; background: transparent; border: none; font-weight: 600; padding: 4px 8px;
}}
QCalendarWidget QToolButton:hover {{ background: rgba(255,255,255,0.15); border-radius: 4px; }}
QCalendarWidget QToolButton::menu-indicator {{ image: none; }}
QCalendarWidget QToolButton#qt_calendar_prevmonth {{ qproperty-icon: url({ar['left_white']}); }}
QCalendarWidget QToolButton#qt_calendar_nextmonth {{ qproperty-icon: url({ar['right_white']}); }}
QCalendarWidget QSpinBox {{ color: {TEXT}; background: white; }}
QCalendarWidget QAbstractItemView {{
    background: white; color: {TEXT}; selection-background-color: {a['base']}; selection-color: white; outline: 0;
}}
QMenu {{ background: white; border: 1px solid {BORDER}; padding: 4px; }}
QMenu::item {{ padding: 6px 18px; border-radius: 4px; }}
QMenu::item:selected {{ background: {a['soft']}; color: {TEXT}; }}
"""


class _ComboPopupFixer(QObject):
    """Da a cada QComboBox un QStyledItemDelegate para que las reglas QSS de los
    items del desplegable se apliquen (el delegado por defecto las ignora y hereda
    colores del combo, p.ej. texto blanco sobre fondo blanco en la barra lateral)."""

    def eventFilter(self, obj, event):
        if event.type() == QEvent.Type.Polish and isinstance(obj, QComboBox):
            if type(obj.itemDelegate()) is not QStyledItemDelegate:
                obj.setItemDelegate(QStyledItemDelegate(obj))
            view = obj.view()
            pal = view.palette()
            pal.setColor(QPalette.ColorRole.Text, QColor(TEXT))
            pal.setColor(QPalette.ColorRole.Base, QColor(SURFACE))
            view.setPalette(pal)
        return False


_combo_fixer = None


def apply_theme(app: QApplication, clave=None):
    """Aplica el tema claro con el acento del negocio indicado.
    Ignora el modo oscuro de Windows para que la app se vea siempre igual."""
    accent = accent_for(clave)
    try:
        app.styleHints().setColorScheme(Qt.ColorScheme.Light)
    except Exception:
        pass
    app.setStyle("Fusion")
    font = QFont("Segoe UI", 10)
    app.setFont(font)
    app.setPalette(_palette(accent))
    app.setStyleSheet(stylesheet(accent))
    global _combo_fixer
    if _combo_fixer is None:
        _combo_fixer = _ComboPopupFixer(app)
        app.installEventFilter(_combo_fixer)


def repolish(widget):
    """Re-aplica el estilo tras cambiar una propiedad dinámica (variant/role)."""
    widget.style().unpolish(widget)
    widget.style().polish(widget)
    widget.update()
