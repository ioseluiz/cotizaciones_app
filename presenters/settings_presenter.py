import os
import json
import keyring
from PyQt6.QtCore import QObject
from PyQt6.QtWidgets import QFileDialog
from views.settings_view import SettingsView
from models.database import Database

CONFIG_FILE = "config.json"
KEYRING_SERVICE = "CotizacionesApp"
KEYRING_ACCOUNT = "gmail_app_password"

class SettingsPresenter(QObject):
    def __init__(self, view: SettingsView, db: Database):
        super().__init__()
        self.view = view
        self.db = db
        
        self.view.move_db_btn.clicked.connect(self.move_db)
        self.view.backup_db_btn.clicked.connect(self.backup_db)
        self.view.save_email_btn.clicked.connect(self.save_email_config)
        
        self.update_path_display()
        self.load_email_config()

    def update_path_display(self):
        self.view.db_path_input.setText(self.db.db_path)

    def load_email_config(self):
        try:
            password = keyring.get_password(KEYRING_SERVICE, KEYRING_ACCOUNT)
            if password:
                self.view.app_password_input.setText(password)
        except Exception:
            pass

    def save_email_config(self):
        password = self.view.app_password_input.text().strip()
        
        try:
            if password:
                keyring.set_password(KEYRING_SERVICE, KEYRING_ACCOUNT, password)
            else:
                try:
                    keyring.delete_password(KEYRING_SERVICE, KEYRING_ACCOUNT)
                except keyring.errors.PasswordDeleteError:
                    pass
            self.view.show_info("Contraseña de aplicación guardada exitosamente y de forma segura en el Llavero del sistema.")
            
            # Limpiar la contraseña antigua de config.json si existe
            if os.path.exists(CONFIG_FILE):
                with open(CONFIG_FILE, 'r') as f:
                    config = json.load(f)
                if "email_app_password" in config:
                    del config["email_app_password"]
                    with open(CONFIG_FILE, 'w') as f:
                        json.dump(config, f)
        except Exception as e:
            self.view.show_error(f"Error al guardar la configuración: {str(e)}")

    def move_db(self):
        new_dir = QFileDialog.getExistingDirectory(self.view, "Seleccionar nuevo directorio para la Base de Datos")
        if new_dir:
            try:
                self.db.move_db(new_dir)
                self.update_path_display()
                self.view.show_info("Base de datos movida exitosamente.")
            except Exception as e:
                self.view.show_error(f"Error al mover la base de datos: {str(e)}")

    def backup_db(self):
        file_path, _ = QFileDialog.getSaveFileName(self.view, "Guardar Backup", "backup_cotizaciones.db", "SQLite Database (*.db)")
        if file_path:
            try:
                self.db.backup_db(file_path)
                self.view.show_info("Backup creado exitosamente.")
            except Exception as e:
                self.view.show_error(f"Error al crear backup: {str(e)}")