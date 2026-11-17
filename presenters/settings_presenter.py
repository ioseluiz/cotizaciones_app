import os
import json
import keyring
from PyQt6.QtCore import QObject, pyqtSignal
from PyQt6.QtWidgets import QFileDialog
from views.settings_view import SettingsView
from models.database import Database, get_config_path
from models.business_model import BusinessModel
from presenters.annex_controller import AnnexController

KEYRING_SERVICE = "CotizacionesApp"
KEYRING_ACCOUNT = "gmail_app_password"

class SettingsPresenter(QObject):
    business_changed_signal = pyqtSignal()

    def __init__(self, view: SettingsView, db: Database, business_model: BusinessModel = None, context=None,
                 annex_model=None):
        super().__init__()
        self.view = view
        self.db = db
        self.business_model = business_model
        self.context = context
        self.annexes = AnnexController(view.annex_list, annex_model, view, quote_mode=False) if annex_model else None
        
        self.view.move_db_btn.clicked.connect(self.move_db)
        self.view.backup_db_btn.clicked.connect(self.backup_db)
        self.view.save_email_btn.clicked.connect(self.save_email_config)
        
        self.view.save_business_btn.clicked.connect(self.save_business)
        self.view.logo_browse_btn.clicked.connect(self.browse_logo)
        self.view.logo_clear_btn.clicked.connect(self.view.logo_input.clear)
        if self.context is not None:
            self.context.changed.connect(lambda _c: self.load_business())

        self.update_path_display()
        self.load_email_config()
        self.load_business()

    def load_business(self):
        if self.business_model is None or self.context is None:
            return
        data = self.business_model.get(self.context.current)
        if data:
            self.view.set_business_data(data)
        if self.annexes:
            self.annexes.set_owner(self.context.current)

    def browse_logo(self):
        path, _ = QFileDialog.getOpenFileName(
            self.view, "Seleccionar logo", "", "Imágenes (*.png *.jpg *.jpeg *.bmp)"
        )
        if path:
            self.view.logo_input.setText(path)

    def save_business(self):
        data = self.view.get_business_data()
        if not data["nombre"]:
            self.view.show_error("El nombre del negocio es obligatorio")
            return
        if not data["prefijo"] or not data["prefijo"].isalnum():
            self.view.show_error("El prefijo es obligatorio y solo puede tener letras y números (ej. EST, SW)")
            return
        other = [b for b in self.business_model.get_all() if b[0] != self.context.current]
        if any((self.business_model.get(b[0]) or {}).get("prefijo") == data["prefijo"] for b in other):
            self.view.show_error("El prefijo ya lo usa el otro negocio; elija uno distinto")
            return
        try:
            self.business_model.update(self.context.current, data)
        except Exception as e:
            self.view.show_error(f"Error guardando los datos del negocio: {e}")
            return
        self.load_business()
        self.business_changed_signal.emit()
        self.view.show_toast("Datos del negocio guardados")

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
            config_file = get_config_path()
            if os.path.exists(config_file):
                with open(config_file, 'r') as f:
                    config = json.load(f)
                if "email_app_password" in config:
                    del config["email_app_password"]
                    with open(config_file, 'w') as f:
                        json.dump(config, f)
        except Exception as e:
            self.view.show_error(f"Error al guardar la configuración: {str(e)}")

    def move_db(self):
        new_dir = QFileDialog.getExistingDirectory(self.view, "Seleccionar nuevo directorio para la Base de Datos")
        if new_dir:
            try:
                self.db.move_db(new_dir)
                self.update_path_display()
                self.view.show_toast("Base de datos movida")
            except Exception as e:
                self.view.show_error(f"Error al mover la base de datos: {str(e)}")

    def backup_db(self):
        file_path, _ = QFileDialog.getSaveFileName(self.view, "Guardar Backup", "backup_cotizaciones.db", "SQLite Database (*.db)")
        if file_path:
            try:
                self.db.backup_db(file_path)
                self.view.show_toast("Backup creado")
            except Exception as e:
                self.view.show_error(f"Error al crear backup: {str(e)}")