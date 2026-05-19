from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLineEdit, QLabel, QMessageBox, QFileDialog, QGroupBox

class SettingsView(QWidget):
    def __init__(self):
        super().__init__()
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()
        
        # Grupo Base de Datos
        db_group = QGroupBox("Gestión de Base de Datos")
        db_layout = QVBoxLayout()
        
        # Ruta actual
        path_layout = QHBoxLayout()
        path_layout.addWidget(QLabel("Ruta Actual de la BD:"))
        self.db_path_input = QLineEdit()
        self.db_path_input.setReadOnly(True)
        path_layout.addWidget(self.db_path_input)
        db_layout.addLayout(path_layout)
        
        # Botones
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
        self.setLayout(layout)

    def show_error(self, message):
        QMessageBox.critical(self, "Error", message)

    def show_info(self, message):
        QMessageBox.information(self, "Información", message)