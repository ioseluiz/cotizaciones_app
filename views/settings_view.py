from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLineEdit, QGroupBox, QFormLayout, QTextEdit, QScrollArea,
    QTabWidget, QFrame,
)

from views.rich_text_edit import RichTextEdit, FormattingToolBar
from views.annex_widgets import AnnexList
from views.widgets import Page, make_button, make_label

PLACEHOLDERS_HINT = "Puede usar {cliente}, {proyecto} y {numero}; se reemplazan al enviar."


def _scroll(widget):
    area = QScrollArea()
    area.setWidgetResizable(True)
    area.setFrameShape(QFrame.Shape.NoFrame)
    widget.setObjectName("pageContent")
    area.setWidget(widget)
    return area


def _form(box):
    form = QFormLayout(box)
    form.setRowWrapPolicy(QFormLayout.RowWrapPolicy.WrapLongRows)
    form.setVerticalSpacing(10)
    form.setHorizontalSpacing(14)
    return form


class SettingsView(Page):
    def __init__(self):
        super().__init__()
        self.init_ui()

    def init_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(20, 16, 20, 0)
        root.setSpacing(6)
        self.title_label = make_label("Configuración", "title")
        root.addWidget(self.title_label)
        root.addWidget(make_label("Los datos de Negocio y Mensajes aplican solo al negocio seleccionado.", "muted"))

        self.tabs = QTabWidget()
        self.tabs.addTab(_scroll(self._build_business_tab()), "Negocio")
        self.tabs.addTab(_scroll(self._build_messages_tab()), "Mensajes")
        self.tabs.addTab(_scroll(self._build_system_tab()), "Sistema")
        root.addWidget(self.tabs, 1)

        # Barra de guardado (solo en las pestañas del negocio)
        self.save_bar = QFrame()
        self.save_bar.setObjectName("actionBar")
        bar = QHBoxLayout(self.save_bar)
        bar.setContentsMargins(0, 10, 0, 10)
        bar.addStretch()
        self.save_business_btn = make_button("Guardar datos del negocio", "primary", "save", "Ctrl+S")
        bar.addWidget(self.save_business_btn)
        root.addWidget(self.save_bar)
        self.tabs.currentChanged.connect(lambda i: self.save_bar.setVisible(i in (0, 1)))

    # ------------------------------------------------------------- pestañas
    def _build_business_tab(self):
        page = QWidget()
        lay = QVBoxLayout(page)
        lay.setContentsMargins(0, 12, 0, 12)
        lay.setSpacing(14)
        self.business_inputs = {}

        ident = QGroupBox("Identidad")
        form = _form(ident)
        for key, label, placeholder in (
            ("nombre", "Nombre del negocio", "Ingeniería Estructural"),
            ("prefijo", "Prefijo de numeración", "EST"),
        ):
            edit = QLineEdit()
            edit.setPlaceholderText(placeholder)
            self.business_inputs[key] = edit
            form.addRow(label, edit)
        self.business_inputs["prefijo"].setMaxLength(6)
        self.business_inputs["prefijo"].setMaximumWidth(120)
        form.addRow(make_label("Las cotizaciones se numeran como PREFIJO-0001.", "muted"))
        lay.addWidget(ident)

        pdf = QGroupBox("Encabezado y pie del PDF")
        form = _form(pdf)
        for key, label in (
            ("encabezado_nombre", "Nombre"),
            ("encabezado_titulo", "Título / profesión"),
            ("ruc", "RUC / línea legal"),
            ("email", "Email de contacto"),
            ("telefono", "Teléfono"),
            ("firma", "Nombre en la firma"),
        ):
            edit = QLineEdit()
            self.business_inputs[key] = edit
            form.addRow(label, edit)
        logo_row = QHBoxLayout()
        self.logo_input = QLineEdit()
        self.logo_input.setPlaceholderText("Sin logo")
        self.logo_input.setReadOnly(True)
        self.logo_browse_btn = make_button("Elegir...", None, "folder")
        self.logo_clear_btn = make_button("", "ghost", "x", "Quitar logo")
        logo_row.addWidget(self.logo_input, 1)
        logo_row.addWidget(self.logo_browse_btn)
        logo_row.addWidget(self.logo_clear_btn)
        form.addRow("Logo", logo_row)
        lay.addWidget(pdf)

        cond = QGroupBox("Condiciones por defecto")
        clay = QVBoxLayout(cond)
        clay.addWidget(make_label("Se cargan en las observaciones de cada cotización nueva.", "muted"))
        self.conditions_edit = RichTextEdit()
        self.conditions_edit.setAcceptRichText(True)
        self.conditions_edit.setMinimumHeight(110)
        self.conditions_toolbar = FormattingToolBar(self.conditions_edit)
        clay.addWidget(self.conditions_toolbar)
        clay.addWidget(self.conditions_edit)
        lay.addWidget(cond)

        annexes = QGroupBox("Anexos fijos del PDF")
        alay = QVBoxLayout(annexes)
        hint = make_label(
            "Se agregan al final del PDF de todas las cotizaciones de este negocio (portafolio, términos, "
            "certificaciones...). Se pueden excluir en una cotización desde su sección Anexos. "
            "Los cambios se guardan al momento.", "muted")
        hint.setWordWrap(True)
        alay.addWidget(hint)
        self.annex_list = AnnexList()
        alay.addWidget(self.annex_list)
        lay.addWidget(annexes)
        lay.addStretch()
        return page

    def _build_messages_tab(self):
        page = QWidget()
        lay = QVBoxLayout(page)
        lay.setContentsMargins(0, 12, 0, 12)
        lay.setSpacing(14)
        lay.addWidget(make_label(PLACEHOLDERS_HINT, "muted"))

        email = QGroupBox("Correo electrónico")
        form = _form(email)
        self.email_subject_input = QLineEdit()
        form.addRow("Asunto", self.email_subject_input)
        self.email_body_edit = QTextEdit()
        self.email_body_edit.setAcceptRichText(False)
        self.email_body_edit.setMinimumHeight(150)
        form.addRow("Mensaje", self.email_body_edit)
        lay.addWidget(email)

        wa = QGroupBox("WhatsApp")
        wlay = QVBoxLayout(wa)
        self.whatsapp_edit = QTextEdit()
        self.whatsapp_edit.setAcceptRichText(False)
        self.whatsapp_edit.setMinimumHeight(150)
        wlay.addWidget(self.whatsapp_edit)
        lay.addWidget(wa)
        lay.addStretch()
        return page

    def _build_system_tab(self):
        page = QWidget()
        lay = QVBoxLayout(page)
        lay.setContentsMargins(0, 12, 0, 12)
        lay.setSpacing(14)

        db = QGroupBox("Base de datos")
        dlay = QVBoxLayout(db)
        dlay.addWidget(make_label("Ubicación actual", "muted"))
        self.db_path_input = QLineEdit()
        self.db_path_input.setReadOnly(True)
        dlay.addWidget(self.db_path_input)
        btns = QHBoxLayout()
        self.backup_db_btn = make_button("Crear backup...", None, "download")
        self.move_db_btn = make_button("Mover base de datos...", None, "folder")
        btns.addWidget(self.backup_db_btn)
        btns.addWidget(self.move_db_btn)
        btns.addStretch()
        dlay.addLayout(btns)
        lay.addWidget(db)

        mail = QGroupBox("Cuenta de Gmail para envíos")
        mlay = QVBoxLayout(mail)
        info = make_label(
            "Use una 'Contraseña de aplicación' de Gmail (no su contraseña normal). "
            "Se guarda de forma segura en el llavero de Windows.", "muted")
        info.setWordWrap(True)
        mlay.addWidget(info)
        row = QHBoxLayout()
        self.app_password_input = QLineEdit()
        self.app_password_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.app_password_input.setPlaceholderText("xxxx xxxx xxxx xxxx")
        row.addWidget(self.app_password_input, 1)
        self.save_email_btn = make_button("Guardar contraseña", None, "save")
        row.addWidget(self.save_email_btn)
        mlay.addLayout(row)
        lay.addWidget(mail)
        lay.addStretch()
        return page

    # ------------------------------------------------------------------ API
    def set_business_data(self, data):
        self.title_label.setText(f"Configuración · {data.get('nombre', '')}")
        for key, edit in self.business_inputs.items():
            edit.setText(data.get(key) or "")
        self.logo_input.setText(data.get("logo_path") or "")
        self.conditions_edit.set_clean_html(data.get("condiciones") or "")
        self.email_subject_input.setText(data.get("email_asunto") or "")
        self.email_body_edit.setPlainText(data.get("email_cuerpo") or "")
        self.whatsapp_edit.setPlainText(data.get("whatsapp_mensaje") or "")

    def get_business_data(self):
        data = {key: edit.text().strip() for key, edit in self.business_inputs.items()}
        data["prefijo"] = data["prefijo"].upper()
        data["logo_path"] = self.logo_input.text().strip()
        data["condiciones"] = self.conditions_edit.toHtml() if self.conditions_edit.toPlainText().strip() else ""
        data["email_asunto"] = self.email_subject_input.text().strip()
        data["email_cuerpo"] = self.email_body_edit.toPlainText()
        data["whatsapp_mensaje"] = self.whatsapp_edit.toPlainText()
        return data

    def shortcut_targets(self):
        return {"save": self.save_business_btn}
