from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QVBoxLayout, QHBoxLayout, QLineEdit, QFormLayout, QSplitter, QFrame, QWidget, QGroupBox,
)

from views.widgets import (
    Page, ResponsiveTable, make_button, make_label, make_search, attach_search, set_role,
)


class ClientsView(Page):
    def __init__(self):
        super().__init__()
        self.init_ui()

    def init_ui(self):
        root = QHBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.setChildrenCollapsible(False)
        splitter.addWidget(self._build_list())
        splitter.addWidget(self._build_form())
        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 0)
        splitter.setSizes([700, 420])
        root.addWidget(splitter)

    def _build_list(self):
        panel = QFrame()
        panel.setObjectName("listPanel")
        panel.setMinimumWidth(320)
        lay = QVBoxLayout(panel)
        lay.setContentsMargins(16, 16, 16, 16)
        lay.setSpacing(10)
        head = QHBoxLayout()
        head.addWidget(make_label("Clientes", "title"))
        head.addStretch()
        self.clear_btn = make_button("Nuevo", "primary", "plus", "Nuevo cliente (Ctrl+N)")
        head.addWidget(self.clear_btn)
        lay.addLayout(head)
        self.search_input = make_search("Buscar por nombre, email o celular...")
        lay.addWidget(self.search_input)
        self.table = ResponsiveTable(0, 3, ["Nombre", "Email", "Celular"], read_only=True)
        self.table.set_modes({0: "stretch", 1: "stretch", 2: "contents"})
        self.table.set_hide_rules([(1, 420)])
        lay.addWidget(self.table, 1)
        attach_search(self.search_input, self.table)
        self.count_label = make_label("", "muted")
        lay.addWidget(self.count_label)
        return panel

    def _build_form(self):
        panel = QWidget()
        panel.setObjectName("pageContent")
        panel.setMinimumWidth(320)
        panel.setMaximumWidth(520)
        lay = QVBoxLayout(panel)
        lay.setContentsMargins(20, 16, 20, 16)
        lay.setSpacing(14)
        head = QHBoxLayout()
        self.form_title = make_label("Nuevo cliente", "title")
        head.addWidget(self.form_title)
        self.status_chip = make_label("Nuevo", "chip")
        head.addWidget(self.status_chip)
        head.addStretch()
        lay.addLayout(head)

        box = QGroupBox("Datos de contacto")
        form = QFormLayout(box)
        form.setRowWrapPolicy(QFormLayout.RowWrapPolicy.WrapLongRows)
        form.setVerticalSpacing(10)
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("Nombre o razón social")
        self.email_input = QLineEdit()
        self.email_input.setPlaceholderText("correo@ejemplo.com")
        self.phone_input = QLineEdit()
        self.phone_input.setPlaceholderText("6000-0000")
        form.addRow("Nombre *", self.name_input)
        form.addRow("Email", self.email_input)
        form.addRow("Celular", self.phone_input)
        hint = make_label("El email se usa para enviar cotizaciones y el celular para WhatsApp.", "muted")
        hint.setWordWrap(True)
        form.addRow(hint)
        lay.addWidget(box)

        btns = QHBoxLayout()
        self.delete_btn = make_button("Eliminar", "danger", "trash")
        btns.addWidget(self.delete_btn)
        btns.addStretch()
        self.save_btn = make_button("Guardar", "primary", "save", "Guardar cliente (Ctrl+S)")
        btns.addWidget(self.save_btn)
        lay.addLayout(btns)
        lay.addStretch()
        self.name_input.returnPressed.connect(self.save_btn.click)
        self.email_input.returnPressed.connect(self.save_btn.click)
        self.phone_input.returnPressed.connect(self.save_btn.click)
        self.set_mode(False)
        return panel

    # ------------------------------------------------------------------ API
    def get_form_data(self):
        return {
            "nombre": self.name_input.text().strip(),
            "email": self.email_input.text().strip(),
            "celular": self.phone_input.text().strip(),
        }

    def set_form_data(self, nombre, email, celular):
        self.name_input.setText(nombre)
        self.email_input.setText(email)
        self.phone_input.setText(celular)

    def clear_form(self):
        self.name_input.clear()
        self.email_input.clear()
        self.phone_input.clear()
        self.set_mode(False)
        self.name_input.setFocus()

    def set_mode(self, editing):
        self.form_title.setText("Editar cliente" if editing else "Nuevo cliente")
        self.status_chip.setText("Editando" if editing else "Nuevo")
        set_role(self.status_chip, "chip-edit" if editing else "chip")
        self.save_btn.setText("Guardar cambios" if editing else "Guardar")
        self.delete_btn.setEnabled(editing)

    def set_count(self, n):
        self.count_label.setText("Sin clientes todavía" if n == 0 else f"{n} cliente(s)")

    def shortcut_targets(self):
        return {"new": self.clear_btn, "save": self.save_btn, "search": self.search_input}
