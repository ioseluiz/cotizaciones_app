from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLineEdit, QLabel, QMessageBox,
    QGroupBox, QFormLayout, QTextEdit, QScrollArea,
)


class SettingsView(QWidget):
    def __init__(self):
        super().__init__()
        self.init_ui()

    def init_ui(self):
        outer = QVBoxLayout(self)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        content = QWidget()
        layout = QVBoxLayout(content)

        # Grupo Negocio activo
        self.business_group = QGroupBox("Datos del negocio")
        form = QFormLayout()
        info = QLabel(
            "Estos datos aplican solo al negocio seleccionado arriba. En los mensajes puede usar "
            "{cliente}, {proyecto} y {numero}."
        )
        info.setWordWrap(True)
        form.addRow(info)

        self.business_inputs = {}
        for key, label in (
            ("nombre", "Nombre del negocio:"),
            ("prefijo", "Prefijo de numeración:"),
            ("encabezado_nombre", "Encabezado del PDF (nombre):"),
            ("encabezado_titulo", "Encabezado del PDF (título):"),
            ("ruc", "RUC / línea legal:"),
            ("email", "Email de contacto:"),
            ("telefono", "Teléfono:"),
            ("firma", "Nombre en la firma:"),
        ):
            edit = QLineEdit()
            self.business_inputs[key] = edit
            form.addRow(label, edit)
        self.business_inputs["prefijo"].setMaxLength(6)

        logo_layout = QHBoxLayout()
        self.logo_input = QLineEdit()
        self.logo_input.setPlaceholderText("(sin logo)")
        self.logo_browse_btn = QPushButton("Buscar...")
        self.logo_clear_btn = QPushButton("Quitar")
        logo_layout.addWidget(self.logo_input)
        logo_layout.addWidget(self.logo_browse_btn)
        logo_layout.addWidget(self.logo_clear_btn)
        form.addRow("Logo (PDF):", logo_layout)

        self.conditions_edit = QTextEdit()
        self.conditions_edit.setAcceptRichText(True)
        self.conditions_edit.setMaximumHeight(110)
        form.addRow("Condiciones por defecto:", self.conditions_edit)

        self.email_subject_input = QLineEdit()
        form.addRow("Asunto del correo:", self.email_subject_input)
        self.email_body_edit = QTextEdit()
        self.email_body_edit.setAcceptRichText(False)
        self.email_body_edit.setMaximumHeight(130)
        form.addRow("Cuerpo del correo:", self.email_body_edit)
        self.whatsapp_edit = QTextEdit()
        self.whatsapp_edit.setAcceptRichText(False)
        self.whatsapp_edit.setMaximumHeight(130)
        form.addRow("Mensaje de WhatsApp:", self.whatsapp_edit)

        self.save_business_btn = QPushButton("Guardar datos del negocio")
        form.addRow(self.save_business_btn)
        self.business_group.setLayout(form)
        layout.addWidget(self.business_group)

        # Grupo Base de Datos
        db_group = QGroupBox("Gestión de Base de Datos")
        db_layout = QVBoxLayout()
        path_layout = QHBoxLayout()
        path_layout.addWidget(QLabel("Ruta Actual de la BD:"))
        self.db_path_input = QLineEdit()
        self.db_path_input.setReadOnly(True)
        path_layout.addWidget(self.db_path_input)
        db_layout.addLayout(path_layout)
        btn_layout = QHBoxLayout()
        self.move_db_btn = QPushButton("Mover Base de Datos...")
        self.backup_db_btn = QPushButton("Crear Backup de Base de Datos...")
        btn_layout.addWidget(self.move_db_btn)
        btn_layout.addWidget(self.backup_db_btn)
        db_layout.addLayout(btn_layout)
        db_group.setLayout(db_layout)
        layout.addWidget(db_group)

        # Grupo Email
        email_group = QGroupBox("Configuración de Correo (Gmail)")
        email_layout = QVBoxLayout()
        email_info = QLabel("Para enviar correos, debes usar una 'Contraseña de Aplicación' de Gmail, no tu contraseña normal.")
        email_info.setWordWrap(True)
        email_layout.addWidget(email_info)
        pass_layout = QHBoxLayout()
        pass_layout.addWidget(QLabel("Contraseña de App:"))
        self.app_password_input = QLineEdit()
        self.app_password_input.setEchoMode(QLineEdit.EchoMode.Password)
        pass_layout.addWidget(self.app_password_input)
        email_layout.addLayout(pass_layout)
        self.save_email_btn = QPushButton("Guardar Contraseña")
        email_layout.addWidget(self.save_email_btn)
        email_group.setLayout(email_layout)
        layout.addWidget(email_group)

        layout.addStretch()
        scroll.setWidget(content)
        outer.addWidget(scroll)

    def set_business_data(self, data):
        self.business_group.setTitle(f"Datos del negocio: {data.get('nombre', '')}")
        for key, edit in self.business_inputs.items():
            edit.setText(data.get(key) or "")
        self.logo_input.setText(data.get("logo_path") or "")
        self.conditions_edit.setHtml(data.get("condiciones") or "")
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

    def show_error(self, message):
        QMessageBox.critical(self, "Error", message)

    def show_info(self, message):
        QMessageBox.information(self, "Información", message)
