from PyQt6.QtWidgets import (
    QVBoxLayout, QHBoxLayout, QGridLayout, QLineEdit, QComboBox, QDateEdit, QTextEdit,
    QGroupBox, QSplitter, QFrame, QScrollArea, QWidget, QSizePolicy,
)
from PyQt6.QtCore import Qt, QDate

from views.widgets import (
    Page, ResponsiveTable, make_button, make_label, make_search, attach_search, set_role,
)

COL_SERVICIO, COL_DESCRIPCION, COL_PRECIO = range(3)


class QuotesView(Page):
    def __init__(self):
        super().__init__()
        self.init_ui()

    def init_ui(self):
        root = QHBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.setChildrenCollapsible(False)
        splitter.addWidget(self._build_list_panel())
        splitter.addWidget(self._build_form_panel())
        splitter.setStretchFactor(0, 0)
        splitter.setStretchFactor(1, 1)
        splitter.setSizes([340, 800])
        root.addWidget(splitter)

    # -------------------------------------------------------------- lista
    def _build_list_panel(self):
        panel = QFrame()
        panel.setObjectName("listPanel")
        panel.setMinimumWidth(250)
        panel.setMaximumWidth(460)
        lay = QVBoxLayout(panel)
        lay.setContentsMargins(16, 16, 16, 16)
        lay.setSpacing(10)

        head = QHBoxLayout()
        head.addWidget(make_label("Cotizaciones", "title"))
        head.addStretch()
        self.clear_btn = make_button("Nueva", "primary", "plus", "Nueva cotización (Ctrl+N)")
        head.addWidget(self.clear_btn)
        lay.addLayout(head)

        self.search_input = make_search("Buscar por número, cliente o proyecto...")
        lay.addWidget(self.search_input)

        self.quotes_table = ResponsiveTable(0, 4, ["No.", "Fecha", "Cliente", "Proyecto"], read_only=True)
        self.quotes_table.set_modes({0: "contents", 1: "contents", 2: "stretch", 3: "stretch"})
        self.quotes_table.set_hide_rules([(1, 330), (3, 300)])
        lay.addWidget(self.quotes_table, 1)
        attach_search(self.search_input, self.quotes_table)

        self.count_label = make_label("", "muted")
        lay.addWidget(self.count_label)
        return panel

    # ---------------------------------------------------------- formulario
    def _build_form_panel(self):
        panel = QWidget()
        outer = QVBoxLayout(panel)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        content = QWidget()
        content.setObjectName("pageContent")
        lay = QVBoxLayout(content)
        lay.setContentsMargins(20, 16, 20, 16)
        lay.setSpacing(14)

        # Encabezado: título + estado
        head = QHBoxLayout()
        self.form_title = make_label("Nueva cotización", "title")
        head.addWidget(self.form_title)
        self.number_label = make_label("Nueva", "chip")
        head.addWidget(self.number_label)
        head.addStretch()
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
        self.project_input.setPlaceholderText("Nombre o descripción corta del proyecto")
        grid.addWidget(self.project_input, 3, 0, 1, 2)
        grid.setColumnStretch(0, 1)
        lay.addWidget(general)

        # Servicios
        items = QGroupBox("Servicios")
        ilay = QVBoxLayout(items)
        self.items_table = ResponsiveTable(0, 3, ["Servicio", "Descripción", "Precio"])
        self.items_table.set_modes({COL_SERVICIO: 170, COL_DESCRIPCION: "stretch", COL_PRECIO: 110})
        self.items_table.setMinimumHeight(200)
        ilay.addWidget(self.items_table)
        row = QHBoxLayout()
        self.add_item_btn = make_button("Agregar servicio", "ghost", "plus")
        self.remove_item_btn = make_button("Quitar", "ghost", "minus", "Quitar el servicio seleccionado")
        row.addWidget(self.add_item_btn)
        row.addWidget(self.remove_item_btn)
        row.addStretch()
        row.addWidget(make_label("Total", "muted"))
        self.total_label = make_label("$0.00", "total")
        row.addWidget(self.total_label)
        ilay.addLayout(row)
        lay.addWidget(items, 1)

        # Observaciones
        obs = QGroupBox("Observaciones y condiciones")
        olay = QVBoxLayout(obs)
        self.observations_edit = QTextEdit()
        self.observations_edit.setAcceptRichText(True)
        self.observations_edit.setPlaceholderText("Condiciones, forma de pago, validez, alcance...")
        self.observations_edit.setMinimumHeight(90)
        self.observations_edit.setMaximumHeight(170)
        olay.addWidget(self.observations_edit)
        lay.addWidget(obs)

        scroll.setWidget(content)
        outer.addWidget(scroll, 1)
        outer.addWidget(self._build_action_bar())
        return panel

    def _build_action_bar(self):
        bar = QFrame()
        bar.setObjectName("actionBar")
        lay = QHBoxLayout(bar)
        lay.setContentsMargins(20, 10, 20, 10)
        self.delete_quote_btn = make_button("Eliminar", "danger", "trash", "Eliminar esta cotización")
        lay.addWidget(self.delete_quote_btn)
        lay.addStretch()
        self.preview_pdf_btn = make_button("Ver PDF", None, "eye", "Abrir una vista previa del PDF")
        self.generate_pdf_btn = make_button("Correo", None, "mail", "Guardar el PDF y enviarlo por correo")
        self.whatsapp_btn = make_button("WhatsApp", None, "chat", "Guardar el PDF y abrir WhatsApp Web")
        self.save_btn = make_button("Guardar", "primary", "save", "Guardar cotización (Ctrl+S)")
        for b in (self.preview_pdf_btn, self.generate_pdf_btn, self.whatsapp_btn, self.save_btn):
            lay.addWidget(b)
        return bar

    # -------------------------------------------------------------- estado
    def set_mode(self, code=None):
        """code=None => cotización nueva; si no, se está editando `code`."""
        editing = code is not None
        self.form_title.setText(f"Cotización {code}" if editing else "Nueva cotización")
        self.number_label.setText("Editando" if editing else "Nueva")
        set_role(self.number_label, "chip-edit" if editing else "chip")
        self.save_btn.setText("Guardar cambios" if editing else "Guardar")
        for b in (self.delete_quote_btn, self.preview_pdf_btn, self.generate_pdf_btn, self.whatsapp_btn):
            b.setEnabled(editing)

    def set_count(self, n):
        self.count_label.setText("Sin cotizaciones todavía" if n == 0 else f"{n} cotización(es)")

    def shortcut_targets(self):
        return {"new": self.clear_btn, "save": self.save_btn, "search": self.search_input}
