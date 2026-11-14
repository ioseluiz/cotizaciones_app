from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QGridLayout,
    QTableWidget,
    QPushButton,
    QLineEdit,
    QLabel,
    QMessageBox,
    QComboBox,
    QDateEdit,
    QGroupBox,
    QHeaderView,
    QSplitter,
    QListWidget,
    QDoubleSpinBox,
    QCheckBox,
    QInputDialog,
    QScrollArea,
    QTextEdit,
)
from PyQt6.QtCore import Qt, QDate


# Columnas de la tabla de actividades
COL_FASE, COL_ACTIVIDAD, COL_ROL, COL_HORAS, COL_TARIFA, COL_COSTO = range(6)
# Columnas de la tabla de gastos
COL_GASTO_DESC, COL_GASTO_MONTO = range(2)


class EstimatorView(QWidget):
    def __init__(self):
        super().__init__()
        self.init_ui()

    def init_ui(self):
        main_layout = QVBoxLayout()
        splitter = QSplitter(Qt.Orientation.Horizontal)

        # ---------- Panel izquierdo (formulario, con scroll) ----------
        left_content = QWidget()
        left_layout = QVBoxLayout(left_content)

        # Datos generales
        general_group = QGroupBox("Datos Generales")
        glayout = QGridLayout()
        glayout.addWidget(QLabel("Cliente:"), 0, 0)
        self.client_combo = QComboBox()
        glayout.addWidget(self.client_combo, 0, 1)
        glayout.addWidget(QLabel("Fecha:"), 0, 2)
        self.date_edit = QDateEdit()
        self.date_edit.setCalendarPopup(True)
        self.date_edit.setDate(QDate.currentDate())
        glayout.addWidget(self.date_edit, 0, 3)

        glayout.addWidget(QLabel("Proyecto:"), 1, 0)
        self.project_input = QLineEdit()
        glayout.addWidget(self.project_input, 1, 1, 1, 3)

        glayout.addWidget(QLabel("Plantilla:"), 2, 0)
        tpl_layout = QHBoxLayout()
        self.template_combo = QComboBox()
        tpl_layout.addWidget(self.template_combo, 1)
        self.load_template_btn = QPushButton("Cargar")
        self.save_template_btn = QPushButton("Guardar como plantilla")
        self.delete_template_btn = QPushButton("Eliminar plantilla")
        tpl_layout.addWidget(self.load_template_btn)
        tpl_layout.addWidget(self.save_template_btn)
        tpl_layout.addWidget(self.delete_template_btn)
        glayout.addLayout(tpl_layout, 2, 1, 1, 3)
        glayout.setColumnStretch(1, 1)
        glayout.setColumnStretch(3, 1)
        general_group.setLayout(glayout)
        left_layout.addWidget(general_group)

        # Actividades
        act_group = QGroupBox("Actividades")
        alayout = QVBoxLayout()
        self.activities_table = QTableWidget(0, 6)
        self.activities_table.setHorizontalHeaderLabels(
            ["Fase", "Actividad", "Rol", "Horas", "Tarifa/h", "Costo"]
        )
        header = self.activities_table.horizontalHeader()
        header.setSectionResizeMode(COL_ACTIVIDAD, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(COL_ROL, QHeaderView.ResizeMode.ResizeToContents)
        self.activities_table.setMinimumHeight(220)
        alayout.addWidget(self.activities_table)
        act_btns = QHBoxLayout()
        self.add_activity_btn = QPushButton("Añadir Actividad")
        self.remove_activity_btn = QPushButton("Remover Actividad")
        self.roles_btn = QPushButton("Tarifas por rol...")
        act_btns.addWidget(self.add_activity_btn)
        act_btns.addWidget(self.remove_activity_btn)
        act_btns.addStretch()
        act_btns.addWidget(self.roles_btn)
        alayout.addLayout(act_btns)
        act_group.setLayout(alayout)
        left_layout.addWidget(act_group)

        # Gastos fijos y entregables lado a lado
        extras_layout = QHBoxLayout()

        exp_group = QGroupBox("Gastos fijos")
        elayout = QVBoxLayout()
        self.expenses_table = QTableWidget(0, 2)
        self.expenses_table.setHorizontalHeaderLabels(["Descripción", "Monto"])
        self.expenses_table.horizontalHeader().setSectionResizeMode(
            COL_GASTO_DESC, QHeaderView.ResizeMode.Stretch
        )
        self.expenses_table.setMinimumHeight(120)
        elayout.addWidget(self.expenses_table)
        exp_btns = QHBoxLayout()
        self.add_expense_btn = QPushButton("Añadir")
        self.remove_expense_btn = QPushButton("Remover")
        exp_btns.addWidget(self.add_expense_btn)
        exp_btns.addWidget(self.remove_expense_btn)
        elayout.addLayout(exp_btns)
        exp_group.setLayout(elayout)
        extras_layout.addWidget(exp_group)

        del_group = QGroupBox("Entregables")
        dlayout = QVBoxLayout()
        self.deliverables_list = QListWidget()
        self.deliverables_list.setMinimumHeight(120)
        dlayout.addWidget(self.deliverables_list)
        del_btns = QHBoxLayout()
        self.add_deliverable_btn = QPushButton("Añadir")
        self.remove_deliverable_btn = QPushButton("Remover")
        del_btns.addWidget(self.add_deliverable_btn)
        del_btns.addWidget(self.remove_deliverable_btn)
        dlayout.addLayout(del_btns)
        del_group.setLayout(dlayout)
        extras_layout.addWidget(del_group)

        left_layout.addLayout(extras_layout)

        # Notas (van a las observaciones de la cotización)
        notes_group = QGroupBox("Notas / condiciones (se agregan a las observaciones de la cotización)")
        nlayout = QVBoxLayout()
        self.notes_edit = QTextEdit()
        self.notes_edit.setAcceptRichText(True)
        self.notes_edit.setMaximumHeight(90)
        nlayout.addWidget(self.notes_edit)
        notes_group.setLayout(nlayout)
        left_layout.addWidget(notes_group)

        # Resumen
        sum_group = QGroupBox("Resumen")
        slayout = QGridLayout()
        slayout.addWidget(QLabel("Contingencia %:"), 0, 0)
        self.contingency_spin = QDoubleSpinBox()
        self.contingency_spin.setRange(0, 100)
        self.contingency_spin.setDecimals(1)
        self.contingency_spin.setValue(10.0)
        slayout.addWidget(self.contingency_spin, 0, 1)
        slayout.addWidget(QLabel("Margen %:"), 1, 0)
        self.margin_spin = QDoubleSpinBox()
        self.margin_spin.setRange(0, 300)
        self.margin_spin.setDecimals(1)
        self.margin_spin.setValue(0.0)
        slayout.addWidget(self.margin_spin, 1, 1)
        self.itbms_check = QCheckBox("Aplicar ITBMS (7%)")
        slayout.addWidget(self.itbms_check, 2, 0, 1, 2)

        self.summary_labels = {}
        rows = [
            ("horas_totales", "Horas totales:"),
            ("costo_horas", "Costo por horas:"),
            ("gastos", "Gastos fijos:"),
            ("contingencia", "Contingencia:"),
            ("margen", "Margen:"),
            ("subtotal", "Subtotal:"),
            ("itbms", "ITBMS:"),
        ]
        for i, (key, text) in enumerate(rows):
            slayout.addWidget(QLabel(text), i, 2)
            lbl = QLabel("0.00")
            lbl.setAlignment(Qt.AlignmentFlag.AlignRight)
            slayout.addWidget(lbl, i, 3)
            self.summary_labels[key] = lbl
        self.total_label = QLabel("TOTAL: $0.00")
        self.total_label.setAlignment(Qt.AlignmentFlag.AlignRight)
        self.total_label.setStyleSheet("font-weight: bold; font-size: 15px; color: #1A365D;")
        slayout.addWidget(self.total_label, len(rows), 2, 1, 2)
        slayout.setColumnStretch(3, 1)
        sum_group.setLayout(slayout)
        left_layout.addWidget(sum_group)

        # Botones principales
        main_btns = QHBoxLayout()
        self.save_btn = QPushButton("Guardar Estimado")
        self.clear_btn = QPushButton("Limpiar")
        self.generate_quote_btn = QPushButton("Generar Cotización")
        self.generate_quote_btn.setStyleSheet("font-weight: bold;")
        main_btns.addWidget(self.save_btn)
        main_btns.addWidget(self.clear_btn)
        main_btns.addWidget(self.generate_quote_btn)
        left_layout.addLayout(main_btns)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setWidget(left_content)

        # ---------- Panel derecho (estimados guardados) ----------
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        right_layout.addWidget(QLabel("Estimados guardados"))
        self.estimates_table = QTableWidget(0, 5)
        self.estimates_table.setHorizontalHeaderLabels(
            ["ID", "Fecha", "Cliente", "Proyecto", "Cotización"]
        )
        self.estimates_table.horizontalHeader().setSectionResizeMode(
            2, QHeaderView.ResizeMode.Stretch
        )
        self.estimates_table.horizontalHeader().setSectionResizeMode(
            3, QHeaderView.ResizeMode.Stretch
        )
        self.estimates_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.estimates_table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self.estimates_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        right_layout.addWidget(self.estimates_table)
        self.delete_estimate_btn = QPushButton("Eliminar Estimado Seleccionado")
        self.delete_estimate_btn.setEnabled(False)
        right_layout.addWidget(self.delete_estimate_btn)

        splitter.addWidget(scroll)
        splitter.addWidget(right_panel)
        splitter.setSizes([750, 350])

        main_layout.addWidget(splitter)
        self.setLayout(main_layout)

    def show_error(self, message):
        QMessageBox.critical(self, "Error", message)

    def show_info(self, message):
        QMessageBox.information(self, "Información", message)

    def ask_yes_no(self, message):
        return QMessageBox.question(self, "Confirmar", message) == QMessageBox.StandardButton.Yes

    def ask_text(self, title, label, default=""):
        text, ok = QInputDialog.getText(self, title, label, text=default)
        return text.strip() if ok else None
