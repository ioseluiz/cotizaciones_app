from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QLineEdit, QComboBox, QDateEdit, QGroupBox,
    QListWidget, QDoubleSpinBox, QCheckBox, QScrollArea, QFrame, QDialog, QSizePolicy,
    QAbstractItemView,
)
from PyQt6.QtCore import Qt, QDate

from views.rich_text_edit import RichTextEdit, FormattingToolBar
from views.widgets import (
    Page, ViewHelpers, ResponsiveTable, make_button, make_label, make_search, attach_search, set_role,
)

# Columnas de la tabla de actividades
COL_FASE, COL_ACTIVIDAD, COL_ROL, COL_HORAS, COL_TARIFA, COL_COSTO = range(6)
# Columnas de la tabla de gastos
COL_GASTO_DESC, COL_GASTO_MONTO = range(2)


class EstimatesDialog(QDialog, ViewHelpers):
    """Lista de estimados guardados del negocio activo."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Abrir estimado")
        self.resize(720, 460)
        lay = QVBoxLayout(self)
        lay.setContentsMargins(16, 16, 16, 16)
        lay.setSpacing(10)
        lay.addWidget(make_label("Estimados guardados", "subtitle"))
        self.search_input = make_search("Buscar por cliente o proyecto...")
        lay.addWidget(self.search_input)
        self.estimates_table = ResponsiveTable(
            0, 5, ["#", "Fecha", "Cliente", "Proyecto", "Cotización"], read_only=True
        )
        self.estimates_table.set_modes({0: "contents", 1: "contents", 2: "stretch", 3: "stretch", 4: "contents"})
        lay.addWidget(self.estimates_table, 1)
        attach_search(self.search_input, self.estimates_table)
        self.empty_label = make_label("Todavía no hay estimados guardados para este negocio.", "muted")
        lay.addWidget(self.empty_label)

        btns = QHBoxLayout()
        self.delete_estimate_btn = make_button("Eliminar", "danger", "trash")
        btns.addWidget(self.delete_estimate_btn)
        btns.addStretch()
        cancel = make_button("Cancelar")
        cancel.clicked.connect(self.reject)
        self.open_estimate_btn = make_button("Abrir", "primary", "folder")
        btns.addWidget(cancel)
        btns.addWidget(self.open_estimate_btn)
        lay.addLayout(btns)

        self.estimates_table.itemSelectionChanged.connect(self._update_buttons)
        self._update_buttons()

    def _update_buttons(self):
        has = bool(self.estimates_table.selectedItems())
        self.open_estimate_btn.setEnabled(has)
        self.delete_estimate_btn.setEnabled(has)

    def refresh_empty_state(self):
        empty = self.estimates_table.rowCount() == 0
        self.empty_label.setVisible(empty)
        self._update_buttons()

    def selected_id(self):
        items = self.estimates_table.selectedItems()
        if not items:
            return None
        return int(self.estimates_table.item(items[0].row(), 0).text())


class EstimatorView(Page):
    def __init__(self):
        super().__init__()
        self.estimates_dialog = EstimatesDialog(self)
        # Alias para el presenter
        self.estimates_table = self.estimates_dialog.estimates_table
        self.delete_estimate_btn = self.estimates_dialog.delete_estimate_btn
        self.init_ui()

    def init_ui(self):
        root = QHBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)
        root.addWidget(self._build_form(), 1)
        root.addWidget(self._build_summary())

    # ---------------------------------------------------------- formulario
    def _build_form(self):
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        content = QWidget()
        content.setObjectName("pageContent")
        lay = QVBoxLayout(content)
        lay.setContentsMargins(20, 16, 16, 16)
        lay.setSpacing(14)

        # Encabezado
        head = QHBoxLayout()
        self.form_title = make_label("Nuevo estimado", "title")
        head.addWidget(self.form_title)
        self.status_chip = make_label("Nuevo", "chip")
        head.addWidget(self.status_chip)
        head.addStretch()
        self.open_estimates_btn = make_button("Abrir...", None, "folder", "Abrir un estimado guardado")
        self.clear_btn = make_button("Nuevo", None, "plus", "Empezar un estimado nuevo (Ctrl+N)")
        head.addWidget(self.open_estimates_btn)
        head.addWidget(self.clear_btn)
        lay.addLayout(head)

        # Datos generales
        general = QGroupBox("Datos generales")
        grid = QGridLayout(general)
        grid.setHorizontalSpacing(12)
        grid.setVerticalSpacing(6)
        grid.addWidget(make_label("Cliente", "muted"), 0, 0)
        grid.addWidget(make_label("Fecha", "muted"), 0, 1)
        self.client_combo = QComboBox()
        self.client_combo.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        grid.addWidget(self.client_combo, 1, 0)
        self.date_edit = QDateEdit()
        self.date_edit.setCalendarPopup(True)
        self.date_edit.setDisplayFormat("dd/MM/yyyy")
        self.date_edit.setDate(QDate.currentDate())
        self.date_edit.setMinimumWidth(130)
        grid.addWidget(self.date_edit, 1, 1)
        grid.addWidget(make_label("Proyecto", "muted"), 2, 0, 1, 2)
        self.project_input = QLineEdit()
        self.project_input.setPlaceholderText("Nombre del proyecto a estimar")
        grid.addWidget(self.project_input, 3, 0, 1, 2)
        grid.setColumnStretch(0, 1)
        lay.addWidget(general)

        # Actividades
        act = QGroupBox("Actividades")
        alay = QVBoxLayout(act)
        tpl_row = QHBoxLayout()
        tpl_row.addWidget(make_label("Plantilla", "muted"))
        self.template_combo = QComboBox()
        self.template_combo.setMinimumWidth(160)
        tpl_row.addWidget(self.template_combo, 1)
        self.load_template_btn = make_button("Cargar", None, "download", "Reemplazar actividades y entregables")
        self.save_template_btn = make_button("Guardar como...", "ghost", "save",
                                             "Guardar las actividades actuales como plantilla")
        self.delete_template_btn = make_button("", "ghost", "trash", "Eliminar la plantilla seleccionada")
        tpl_row.addWidget(self.load_template_btn)
        tpl_row.addWidget(self.save_template_btn)
        tpl_row.addWidget(self.delete_template_btn)
        alay.addLayout(tpl_row)

        self.activities_table = ResponsiveTable(0, 6, ["Fase", "Actividad", "Rol", "Horas", "Tarifa/h", "Costo"])
        self.activities_table.set_modes({
            COL_FASE: 120, COL_ACTIVIDAD: "stretch", COL_ROL: 190, COL_HORAS: 64, COL_TARIFA: 80, COL_COSTO: 90,
        })
        self.activities_table.set_hide_rules([(COL_TARIFA, 620)])
        self.activities_table.set_proportional(COL_FASE, 0.17, 90, 150)
        self.activities_table.set_proportional(COL_ROL, 0.26, 140, 230)
        self.activities_table.verticalHeader().setDefaultSectionSize(38)
        self.activities_table.setMinimumHeight(240)
        alay.addWidget(self.activities_table)
        act_btns = QHBoxLayout()
        self.add_activity_btn = make_button("Agregar actividad", "ghost", "plus")
        self.remove_activity_btn = make_button("Quitar", "ghost", "minus", "Quitar la actividad seleccionada")
        act_btns.addWidget(self.add_activity_btn)
        act_btns.addWidget(self.remove_activity_btn)
        act_btns.addStretch()
        self.roles_btn = make_button("Tarifas por rol...", "ghost", "tag", "Editar roles y tarifas por hora")
        act_btns.addWidget(self.roles_btn)
        alay.addLayout(act_btns)
        lay.addWidget(act)

        # Gastos fijos y entregables (lado a lado; se apilan si no caben)
        extras = QWidget()
        self.extras_layout = QHBoxLayout(extras)
        self.extras_layout.setContentsMargins(0, 0, 0, 0)
        self.extras_layout.setSpacing(14)

        exp = QGroupBox("Gastos fijos")
        elay = QVBoxLayout(exp)
        self.expenses_table = ResponsiveTable(0, 2, ["Descripción", "Monto"])
        self.expenses_table.set_modes({COL_GASTO_DESC: "stretch", COL_GASTO_MONTO: 100})
        self.expenses_table.setMinimumHeight(110)
        elay.addWidget(self.expenses_table)
        exp_btns = QHBoxLayout()
        self.add_expense_btn = make_button("Agregar gasto", "ghost", "plus")
        self.remove_expense_btn = make_button("Quitar", "ghost", "minus")
        exp_btns.addWidget(self.add_expense_btn)
        exp_btns.addWidget(self.remove_expense_btn)
        exp_btns.addStretch()
        elay.addLayout(exp_btns)
        self.extras_layout.addWidget(exp)

        dlv = QGroupBox("Entregables")
        dlay = QVBoxLayout(dlv)
        add_row = QHBoxLayout()
        self.deliverable_input = QLineEdit()
        self.deliverable_input.setPlaceholderText("Escriba un entregable y presione Enter")
        add_row.addWidget(self.deliverable_input, 1)
        self.add_deliverable_btn = make_button("", None, "plus", "Agregar entregable")
        add_row.addWidget(self.add_deliverable_btn)
        dlay.addLayout(add_row)
        self.deliverables_list = QListWidget()
        self.deliverables_list.setMinimumHeight(90)
        self.deliverables_list.setDragDropMode(QAbstractItemView.DragDropMode.InternalMove)
        self.deliverables_list.setToolTip("Doble clic para editar · arrastre para reordenar")
        dlay.addWidget(self.deliverables_list)
        del_btns = QHBoxLayout()
        self.remove_deliverable_btn = make_button("Quitar", "ghost", "minus")
        del_btns.addWidget(self.remove_deliverable_btn)
        del_btns.addStretch()
        dlay.addLayout(del_btns)
        self.extras_layout.addWidget(dlv)
        lay.addWidget(extras)

        # Notas
        notes = QGroupBox("Notas para la cotización")
        nlay = QVBoxLayout(notes)
        self.notes_edit = RichTextEdit()
        self.notes_edit.setAcceptRichText(True)
        self.notes_edit.setPlaceholderText(
            "Alcance, supuestos o exclusiones. Se agregan a las observaciones junto con las condiciones del negocio."
        )
        self.notes_edit.setMinimumHeight(90)
        self.notes_edit.setMaximumHeight(170)
        self.notes_toolbar = FormattingToolBar(self.notes_edit)
        nlay.addWidget(self.notes_toolbar)
        nlay.addWidget(self.notes_edit)
        lay.addWidget(notes)
        lay.addStretch()

        scroll.setWidget(content)
        self._form_scroll = scroll
        return scroll

    # ------------------------------------------------------------- resumen
    def _build_summary(self):
        panel = QFrame()
        panel.setObjectName("listPanel")
        panel.setStyleSheet("#listPanel { border-right: none; border-left: 1px solid #E2E8F0; }")
        panel.setMinimumWidth(260)
        panel.setMaximumWidth(320)
        outer = QVBoxLayout(panel)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        content = QWidget()
        lay = QVBoxLayout(content)
        lay.setContentsMargins(16, 16, 16, 16)
        lay.setSpacing(10)
        lay.addWidget(make_label("Resumen", "subtitle"))

        params = QGridLayout()
        params.setVerticalSpacing(8)
        params.addWidget(make_label("Contingencia", "muted"), 0, 0)
        self.contingency_spin = QDoubleSpinBox()
        self.contingency_spin.setRange(0, 100)
        self.contingency_spin.setDecimals(1)
        self.contingency_spin.setSuffix(" %")
        self.contingency_spin.setValue(10.0)
        self.contingency_spin.setToolTip("Imprevistos sobre el costo base")
        params.addWidget(self.contingency_spin, 0, 1)
        params.addWidget(make_label("Margen", "muted"), 1, 0)
        self.margin_spin = QDoubleSpinBox()
        self.margin_spin.setRange(0, 300)
        self.margin_spin.setDecimals(1)
        self.margin_spin.setSuffix(" %")
        self.margin_spin.setToolTip("Utilidad sobre costo + contingencia")
        params.addWidget(self.margin_spin, 1, 1)
        self.itbms_check = QCheckBox("Aplicar ITBMS (7%)")
        params.addWidget(self.itbms_check, 2, 0, 1, 2)
        lay.addLayout(params)

        line = QFrame()
        line.setFrameShape(QFrame.Shape.HLine)
        line.setStyleSheet("color: #E2E8F0;")
        lay.addWidget(line)

        self.summary_labels = {}
        breakdown = QGridLayout()
        breakdown.setVerticalSpacing(6)
        rows = [
            ("horas_totales", "Horas totales"),
            ("costo_horas", "Costo por horas"),
            ("gastos", "Gastos fijos"),
            ("contingencia", "Contingencia"),
            ("margen", "Margen"),
            ("subtotal", "Subtotal"),
            ("itbms", "ITBMS"),
        ]
        for i, (key, text) in enumerate(rows):
            breakdown.addWidget(make_label(text, "muted"), i, 0)
            lbl = make_label("0.00", "amount")
            lbl.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            breakdown.addWidget(lbl, i, 1)
            self.summary_labels[key] = lbl
        lay.addLayout(breakdown)

        total_box = QFrame()
        total_box.setObjectName("card")
        tlay = QVBoxLayout(total_box)
        tlay.setContentsMargins(12, 10, 12, 10)
        tlay.addWidget(make_label("Total a cotizar", "muted"))
        self.total_label = make_label("$0.00", "total")
        tlay.addWidget(self.total_label)
        lay.addWidget(total_box)
        lay.addStretch()
        scroll.setWidget(content)
        outer.addWidget(scroll, 1)

        # Acciones fijas al pie del panel
        actions = QFrame()
        actions.setObjectName("actionBar")
        alay = QVBoxLayout(actions)
        alay.setContentsMargins(16, 12, 16, 12)
        alay.setSpacing(8)
        self.generate_quote_btn = make_button("Generar cotización", "primary", "arrow-right",
                                              "Guardar el estimado y crear/actualizar su cotización")
        self.save_btn = make_button("Guardar estimado", None, "save", "Guardar estimado (Ctrl+S)")
        alay.addWidget(self.generate_quote_btn)
        alay.addWidget(self.save_btn)
        outer.addWidget(actions)
        return panel

    # ------------------------------------------------------------ responsive
    def resizeEvent(self, event):
        super().resizeEvent(event)
        # Gastos y entregables: lado a lado si hay espacio, apilados si no
        narrow = self._form_scroll.viewport().width() < 620
        direction = QVBoxLayout.Direction.TopToBottom if narrow else QVBoxLayout.Direction.LeftToRight
        if self.extras_layout.direction() != direction:
            self.extras_layout.setDirection(direction)

    # ---------------------------------------------------------------- estado
    def set_mode(self, estimate_id=None, quote_code=None):
        if estimate_id is None:
            self.form_title.setText("Nuevo estimado")
            self.status_chip.setText("Nuevo")
            set_role(self.status_chip, "chip")
        else:
            self.form_title.setText(f"Estimado #{estimate_id}")
            self.status_chip.setText(f"Cotización {quote_code}" if quote_code else "Sin cotización")
            set_role(self.status_chip, "chip-edit" if not quote_code else "chip")
        self.generate_quote_btn.setText("Actualizar cotización" if quote_code else "Generar cotización")

    def shortcut_targets(self):
        return {"new": self.clear_btn, "save": self.save_btn}
