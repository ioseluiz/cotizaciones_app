"""Edición de opciones para el cliente (adicionales y alternativas).

Lo usan el estimador (editor embebido) y Cotizaciones (diálogo). Cada fila de
servicios/actividades/gastos guarda su opción como índice en la lista de
opciones (None = alcance base), por eso al quitar o reordenar opciones hay que
reasignar esos índices con `take_index_map()` + `rebuild_option_combos()`.
"""
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QComboBox, QTableWidgetItem, QDialog, QMessageBox,
)

from utils.estimate_calculator import OPTION_TYPES, OPCION_ADICIONAL
from views.widgets import ResponsiveTable, ViewHelpers, make_button, make_label

BASE_LABEL = "Base"
COL_OPT_NOMBRE, COL_OPT_TIPO, COL_OPT_DESC = range(3)

OPTIONS_HINT = (
    "Adicional: se suma a la base y el cliente puede escoger varios. "
    "Alternativa: cambia parte del alcance y el cliente escoge una. "
    "Asigne cada fila a una opción en la columna \"Opción\"."
)


def option_label(index, nombre):
    return nombre.strip() or f"Opción {index + 1}"


# ------------------------------------------------------------ combos por fila
def make_option_combo(names, selected=None, on_change=None):
    combo = QComboBox()
    combo.addItem(BASE_LABEL, userData=None)
    for i, name in enumerate(names):
        combo.addItem(name, userData=i)
    if selected is not None and 0 <= selected < len(names):
        combo.setCurrentIndex(selected + 1)
    if on_change:
        combo.currentIndexChanged.connect(lambda _i: on_change())
    return combo


def option_of(table, row, col):
    widget = table.cellWidget(row, col)
    return widget.currentData() if widget else None


def rebuild_option_combos(table, col, names, index_map=None, on_change=None):
    """Reconstruye los combos de opción de la tabla. `index_map` ({viejo: nuevo|None})
    reasigna las filas cuando se quitaron o movieron opciones."""
    for row in range(table.rowCount()):
        current = option_of(table, row, col)
        if current is not None and index_map is not None:
            current = index_map.get(current)
        table.setCellWidget(row, col, make_option_combo(names, current, on_change))


# ----------------------------------------------------------------- editor
class OptionsEditor(QWidget):
    """Tabla Nombre / Tipo / Descripción con botones Agregar y Quitar.

    Emite `changed` cuando se agrega, quita o renombra una opción o cambia su tipo.
    """

    changed = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        lay = QVBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(8)
        self.table = ResponsiveTable(0, 3, ["Nombre", "Tipo", "Descripción para el cliente"])
        self.table.set_modes({COL_OPT_NOMBRE: 200, COL_OPT_TIPO: 130, COL_OPT_DESC: "stretch"})
        self.table.set_proportional(COL_OPT_NOMBRE, 0.3, 140, 260)
        self.table.verticalHeader().setDefaultSectionSize(38)
        self.table.setMinimumHeight(110)
        lay.addWidget(self.table)

        btns = QHBoxLayout()
        self.add_btn = make_button("Agregar opción", "ghost", "plus")
        self.remove_btn = make_button("Quitar", "ghost", "minus", "Quitar la opción seleccionada")
        btns.addWidget(self.add_btn)
        btns.addWidget(self.remove_btn)
        btns.addStretch()
        lay.addLayout(btns)

        self._next_key = 0
        self._baseline = []
        self.add_btn.clicked.connect(self._on_add)
        self.remove_btn.clicked.connect(self._on_remove)
        self.table.itemChanged.connect(lambda _item: self.changed.emit())

    # -- datos
    def set_options(self, options):
        self.table.blockSignals(True)
        self.table.setRowCount(0)
        self._next_key = 0
        for o in options:
            self._insert_row(o.get("nombre", ""), o.get("tipo", OPCION_ADICIONAL), o.get("descripcion", ""))
        self.table.blockSignals(False)
        self._baseline = self._keys()
        self.changed.emit()

    def options(self):
        result = []
        for row in range(self.table.rowCount()):
            name_item = self.table.item(row, COL_OPT_NOMBRE)
            desc_item = self.table.item(row, COL_OPT_DESC)
            combo = self.table.cellWidget(row, COL_OPT_TIPO)
            result.append({
                "nombre": name_item.text().strip() if name_item else "",
                "tipo": combo.currentData() if combo else OPCION_ADICIONAL,
                "descripcion": desc_item.text().strip() if desc_item else "",
            })
        return result

    def names(self):
        return [option_label(i, o["nombre"]) for i, o in enumerate(self.options())]

    def take_index_map(self):
        """{índice anterior: índice actual | None} desde la última llamada (o set_options)."""
        keys = self._keys()
        mapping = {old: (keys.index(k) if k in keys else None) for old, k in enumerate(self._baseline)}
        self._baseline = keys
        return mapping

    # -- interno
    def _keys(self):
        return [self.table.item(r, COL_OPT_NOMBRE).data(Qt.ItemDataRole.UserRole)
                for r in range(self.table.rowCount())]

    def _insert_row(self, nombre, tipo, descripcion):
        row = self.table.rowCount()
        self.table.insertRow(row)
        name_item = QTableWidgetItem(nombre)
        name_item.setData(Qt.ItemDataRole.UserRole, self._next_key)
        self._next_key += 1
        self.table.setItem(row, COL_OPT_NOMBRE, name_item)
        combo = QComboBox()
        for key, label in OPTION_TYPES.items():
            combo.addItem(label, userData=key)
        idx = combo.findData(tipo)
        combo.setCurrentIndex(idx if idx >= 0 else 0)
        combo.currentIndexChanged.connect(lambda _i: self.changed.emit())
        self.table.setCellWidget(row, COL_OPT_TIPO, combo)
        self.table.setItem(row, COL_OPT_DESC, QTableWidgetItem(descripcion))
        return row

    def _on_add(self):
        self.table.blockSignals(True)
        row = self._insert_row(f"Opción {self.table.rowCount() + 1}", OPCION_ADICIONAL, "")
        self.table.blockSignals(False)
        self.changed.emit()
        self.table.setCurrentCell(row, COL_OPT_NOMBRE)
        self.table.editItem(self.table.item(row, COL_OPT_NOMBRE))

    def _on_remove(self):
        row = self.table.currentRow()
        if row < 0:
            return
        name = option_label(row, self.options()[row]["nombre"])
        answer = QMessageBox.question(
            self, "Quitar opción",
            f"¿Quitar la opción '{name}'?\n\nLas filas asignadas a ella pasarán al alcance base.",
        )
        if answer != QMessageBox.StandardButton.Yes:
            return
        self.table.removeRow(row)
        self.changed.emit()


# ----------------------------------------------------------------- diálogo
class OptionsDialog(QDialog, ViewHelpers):
    """Diálogo para administrar las opciones de una cotización."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Opciones para el cliente")
        self.resize(760, 380)
        lay = QVBoxLayout(self)
        lay.setContentsMargins(16, 16, 16, 16)
        lay.setSpacing(10)
        lay.addWidget(make_label("Opciones para el cliente", "subtitle"))
        hint = make_label(OPTIONS_HINT, "muted")
        hint.setWordWrap(True)
        lay.addWidget(hint)
        self.editor = OptionsEditor()
        lay.addWidget(self.editor, 1)

        btns = QHBoxLayout()
        btns.addStretch()
        cancel = make_button("Cancelar")
        cancel.clicked.connect(self.reject)
        ok = make_button("Aceptar", "primary")
        ok.clicked.connect(self.accept)
        btns.addWidget(cancel)
        btns.addWidget(ok)
        lay.addLayout(btns)
