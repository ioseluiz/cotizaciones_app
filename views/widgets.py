"""Componentes y utilidades de UI compartidos por todas las vistas."""
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtWidgets import (
    QTableWidget, QTableWidgetItem, QHeaderView, QPushButton, QLabel, QLineEdit,
    QMessageBox, QInputDialog, QHBoxLayout, QVBoxLayout, QWidget, QFrame, QAbstractItemView,
)

from utils.icons import icon
from utils import theme
from utils.formatting import money, fmt_date, parse_number  # noqa: F401 — reexportados


def numeric_item(text, editable=True):
    item = QTableWidgetItem(text)
    item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
    if not editable:
        item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
    return item


# ------------------------------------------------------------------ fábricas
def make_button(text="", variant=None, icon_name=None, tooltip=None):
    btn = QPushButton(text)
    if variant:
        btn.setProperty("variant", variant)
    if icon_name:
        color = {"primary": "#FFFFFF", "danger": theme.DANGER}.get(variant, theme.TEXT)
        btn.setIcon(icon(icon_name, color))
    if tooltip:
        btn.setToolTip(tooltip)
    btn.setCursor(Qt.CursorShape.PointingHandCursor)
    return btn


def set_button_icon_color(btn, icon_name, color):
    btn.setIcon(icon(icon_name, color))


def make_label(text="", role=None):
    lbl = QLabel(text)
    if role:
        lbl.setProperty("role", role)
    return lbl


def set_role(label, role):
    label.setProperty("role", role)
    theme.repolish(label)


def make_search(placeholder="Buscar..."):
    edit = QLineEdit()
    edit.setPlaceholderText(placeholder)
    edit.setProperty("search", True)
    edit.setClearButtonEnabled(True)
    edit.addAction(icon("search", theme.TEXT_MUTED, 16), QLineEdit.ActionPosition.LeadingPosition)
    return edit


def page_header(title_label, subtitle_label=None, right_widgets=()):
    """Fila de encabezado de página: título (+subtítulo) a la izquierda, acciones a la derecha."""
    row = QHBoxLayout()
    left = QVBoxLayout()
    left.setSpacing(2)
    left.addWidget(title_label)
    if subtitle_label is not None:
        left.addWidget(subtitle_label)
    row.addLayout(left)
    row.addStretch()
    for w in right_widgets:
        row.addWidget(w)
    return row


def card(layout=None):
    frame = QFrame()
    frame.setObjectName("card")
    if layout is not None:
        frame.setLayout(layout)
    return frame


# ------------------------------------------------------------------ tablas
class ResponsiveTable(QTableWidget):
    """Tabla con estilo uniforme que oculta columnas secundarias cuando no caben.

    set_hide_rules([(col, ancho_minimo), ...]): la columna `col` se oculta si el
    ancho visible de la tabla es menor que `ancho_minimo`.
    """

    def __init__(self, rows, columns, headers, read_only=False, parent=None):
        super().__init__(rows, columns, parent)
        self.setHorizontalHeaderLabels(headers)
        self.verticalHeader().setVisible(False)
        self.verticalHeader().setDefaultSectionSize(34)
        self.setAlternatingRowColors(True)
        self.setShowGrid(False)
        self.setWordWrap(False)
        self.horizontalHeader().setHighlightSections(False)
        self.horizontalHeader().setDefaultAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        self.setHorizontalScrollMode(QAbstractItemView.ScrollMode.ScrollPerPixel)
        self.setVerticalScrollMode(QAbstractItemView.ScrollMode.ScrollPerPixel)
        if read_only:
            self.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
            self.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
            self.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self._hide_rules = []
        self._proportional = {}

    def set_proportional(self, col, ratio, min_width, max_width):
        """La columna ocupa `ratio` del ancho visible, acotado entre min y max."""
        self._proportional[col] = (ratio, min_width, max_width)
        self._apply_proportional()

    def _apply_proportional(self):
        width = self.viewport().width()
        for col, (ratio, lo, hi) in self._proportional.items():
            self.setColumnWidth(col, max(lo, min(hi, int(width * ratio))))

    def set_modes(self, modes):
        """modes: {col: 'stretch' | 'contents' | int(ancho fijo)}"""
        header = self.horizontalHeader()
        for col, mode in modes.items():
            if mode == "stretch":
                header.setSectionResizeMode(col, QHeaderView.ResizeMode.Stretch)
            elif mode == "contents":
                header.setSectionResizeMode(col, QHeaderView.ResizeMode.ResizeToContents)
            else:
                header.setSectionResizeMode(col, QHeaderView.ResizeMode.Interactive)
                self.setColumnWidth(col, int(mode))

    def set_hide_rules(self, rules):
        self._hide_rules = rules
        self._apply_hide_rules()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._apply_hide_rules()
        self._apply_proportional()

    def _apply_hide_rules(self):
        width = self.viewport().width()
        for col, min_width in self._hide_rules:
            self.setColumnHidden(col, width < min_width)


def attach_search(line_edit, table):
    """Filtra filas de la tabla por texto (en cualquier columna visible o no)."""
    def apply():
        text = line_edit.text().strip().lower()
        for row in range(table.rowCount()):
            match = not text or any(
                table.item(row, c) and text in table.item(row, c).text().lower()
                for c in range(table.columnCount())
            )
            table.setRowHidden(row, not match)

    line_edit.textChanged.connect(apply)
    # Re-aplicar el filtro cuando el presenter recarga la tabla
    table.model().rowsInserted.connect(lambda *_: QTimer.singleShot(0, apply))
    return apply


def empty_state(text):
    lbl = make_label(text, "muted")
    lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
    lbl.setWordWrap(True)
    return lbl


# ------------------------------------------------------------------ mensajes
class ViewHelpers:
    """Mixin con los diálogos comunes. show_toast muestra un aviso breve en la barra
    de estado (no bloquea); show_info se reserva para mensajes que hay que leer."""

    def show_error(self, message):
        QMessageBox.critical(self, "Error", message)

    def show_info(self, message):
        QMessageBox.information(self, "Información", message)

    def show_toast(self, message, timeout=5000):
        win = self.window()
        if hasattr(win, "statusBar") and win is not self:
            win.statusBar().showMessage(f"✓  {message}", timeout)
        else:
            self.show_info(message)

    def ask_yes_no(self, message, title="Confirmar"):
        return QMessageBox.question(self, title, message) == QMessageBox.StandardButton.Yes

    def ask_text(self, title, label, default=""):
        text, ok = QInputDialog.getText(self, title, label, text=default)
        return text.strip() if ok else None


class Page(QWidget, ViewHelpers):
    """Base de las páginas principales (fondo y márgenes uniformes)."""

    def __init__(self):
        super().__init__()
        self.setObjectName("page")
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
