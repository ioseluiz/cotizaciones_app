from PyQt6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QTableWidget,
    QTableWidgetItem,
    QPushButton,
    QComboBox,
    QHeaderView,
    QMessageBox,
    QLabel,
)
from PyQt6.QtCore import Qt

from models.seed_data import TIPO_SOFTWARE, TIPO_ESTRUCTURAL, TIPO_AMBOS

ROLE_TYPES = [TIPO_SOFTWARE, TIPO_ESTRUCTURAL, TIPO_AMBOS]


class RolesDialog(QDialog):
    """Edición de roles y tarifas por hora. Devuelve las filas con get_rows();
    el presenter se encarga de persistir los cambios."""

    def __init__(self, roles, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Tarifas por rol")
        self.resize(560, 420)

        layout = QVBoxLayout(self)
        layout.addWidget(QLabel(
            "Las tarifas nuevas se aplican al elegir el rol en una actividad. "
            "Los estimados ya guardados conservan su tarifa."
        ))

        self.table = QTableWidget(0, 3)
        self.table.setHorizontalHeaderLabels(["Rol", "Tarifa/h ($)", "Tipo"])
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        layout.addWidget(self.table)

        btns = QHBoxLayout()
        add_btn = QPushButton("Añadir rol")
        remove_btn = QPushButton("Remover rol")
        btns.addWidget(add_btn)
        btns.addWidget(remove_btn)
        btns.addStretch()
        save_btn = QPushButton("Guardar")
        cancel_btn = QPushButton("Cancelar")
        btns.addWidget(save_btn)
        btns.addWidget(cancel_btn)
        layout.addLayout(btns)

        add_btn.clicked.connect(lambda: self._add_row(None, "", 0.0, TIPO_AMBOS))
        remove_btn.clicked.connect(self._remove_row)
        save_btn.clicked.connect(self._on_save)
        cancel_btn.clicked.connect(self.reject)

        for role_id, nombre, tarifa, tipo in roles:
            self._add_row(role_id, nombre, tarifa, tipo)

    def _add_row(self, role_id, nombre, tarifa, tipo):
        row = self.table.rowCount()
        self.table.insertRow(row)
        name_item = QTableWidgetItem(nombre)
        name_item.setData(Qt.ItemDataRole.UserRole, role_id)
        self.table.setItem(row, 0, name_item)
        self.table.setItem(row, 1, QTableWidgetItem(f"{tarifa:.2f}"))
        combo = QComboBox()
        combo.addItems(ROLE_TYPES)
        combo.setCurrentText(tipo)
        self.table.setCellWidget(row, 2, combo)

    def _remove_row(self):
        row = self.table.currentRow()
        if row >= 0:
            self.table.removeRow(row)

    def _on_save(self):
        try:
            self.get_rows()
        except ValueError as e:
            QMessageBox.critical(self, "Error", str(e))
            return
        self.accept()

    def get_rows(self):
        """Lista de (id|None, nombre, tarifa, tipo). Lanza ValueError si hay datos inválidos."""
        rows = []
        for r in range(self.table.rowCount()):
            name_item = self.table.item(r, 0)
            nombre = name_item.text().strip() if name_item else ""
            if not nombre:
                raise ValueError(f"El rol de la fila {r + 1} no tiene nombre.")
            tarifa_item = self.table.item(r, 1)
            try:
                tarifa = float(tarifa_item.text()) if tarifa_item else 0.0
            except ValueError:
                raise ValueError(f"La tarifa del rol '{nombre}' no es un número válido.")
            if tarifa < 0:
                raise ValueError(f"La tarifa del rol '{nombre}' no puede ser negativa.")
            tipo = self.table.cellWidget(r, 2).currentText()
            rows.append((name_item.data(Qt.ItemDataRole.UserRole), nombre, tarifa, tipo))
        return rows
