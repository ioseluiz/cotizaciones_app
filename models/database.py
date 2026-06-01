import sqlite3
import shutil
import os
import sys
import json

APP_NAME = "CotizacionesApp"
DEFAULT_DB_NAME = "cotizaciones.db"
CONFIG_NAME = "config.json"


def get_app_data_dir():
    """Directorio estable por usuario donde se guardan la base de datos y la
    configuración. Sobrevive a instalaciones/desinstalaciones del ejecutable."""
    if sys.platform == "win32":
        base = os.environ.get("APPDATA") or os.path.expanduser("~")
    elif sys.platform == "darwin":
        base = os.path.join(os.path.expanduser("~"), "Library", "Application Support")
    else:
        base = os.environ.get("XDG_DATA_HOME") or os.path.join(
            os.path.expanduser("~"), ".local", "share"
        )
    path = os.path.join(base, APP_NAME)
    os.makedirs(path, exist_ok=True)
    return path


def get_config_path():
    return os.path.join(get_app_data_dir(), CONFIG_NAME)


def _find_legacy_db():
    """Busca una base de datos creada por versiones anteriores, que guardaban el
    archivo relativo al directorio de trabajo o junto al ejecutable."""
    search_dirs = [os.getcwd()]
    if getattr(sys, "frozen", False):
        search_dirs.append(os.path.dirname(sys.executable))

    # 1. Ruta personalizada apuntada por un config.json antiguo
    for d in search_dirs:
        cfg = os.path.join(d, CONFIG_NAME)
        if os.path.exists(cfg):
            try:
                with open(cfg, "r") as f:
                    legacy_path = json.load(f).get("db_path")
                if legacy_path and os.path.exists(legacy_path):
                    return legacy_path
            except Exception:
                pass

    # 2. Base de datos por defecto junto al CWD o al ejecutable
    for d in search_dirs:
        candidate = os.path.join(d, DEFAULT_DB_NAME)
        if os.path.exists(candidate):
            return candidate

    return None


def get_db_path():
    config_path = get_config_path()

    # Respetar una ruta personalizada elegida por el usuario en Configuración
    if os.path.exists(config_path):
        try:
            with open(config_path, "r") as f:
                config = json.load(f)
                db_path = config.get("db_path")
                if db_path and os.path.exists(os.path.dirname(db_path)):
                    return db_path
        except Exception:
            pass

    new_path = os.path.join(get_app_data_dir(), DEFAULT_DB_NAME)

    # Migrar automáticamente la base de datos de una versión anterior la primera
    # vez que se ejecuta esta versión, para no perder los datos existentes.
    if not os.path.exists(new_path):
        legacy = _find_legacy_db()
        if legacy and os.path.abspath(legacy) != os.path.abspath(new_path):
            try:
                shutil.copy2(legacy, new_path)
            except Exception:
                pass

    return new_path


def set_db_path(new_path):
    config_path = get_config_path()
    config = {}
    if os.path.exists(config_path):
        with open(config_path, "r") as f:
            try:
                config = json.load(f)
            except Exception:
                pass
    config["db_path"] = new_path
    with open(config_path, "w") as f:
        json.dump(config, f)


class Database:
    def __init__(self):
        self.db_path = get_db_path()
        self.init_db()

    def get_connection(self):
        return sqlite3.connect(self.db_path)

    def init_db(self):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS clientes (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    nombre TEXT NOT NULL,
                    email TEXT,
                    celular TEXT
                )
            ''')
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS cotizaciones (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    cliente_id INTEGER,
                    tipo TEXT NOT NULL,
                    fecha TEXT NOT NULL,
                    proyecto TEXT NOT NULL,
                    observaciones TEXT,
                    FOREIGN KEY (cliente_id) REFERENCES clientes (id)
                )
            ''')
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS detalles_cotizacion (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    cotizacion_id INTEGER,
                    servicio TEXT NOT NULL,
                    descripcion TEXT,
                    precio_total REAL NOT NULL,
                    FOREIGN KEY (cotizacion_id) REFERENCES cotizaciones (id)
                )
            ''')
            conn.commit()

    def move_db(self, new_dir):
        new_path = os.path.join(new_dir, os.path.basename(self.db_path))
        if self.db_path != new_path:
            shutil.copy2(self.db_path, new_path)
            self.db_path = new_path
            set_db_path(new_path)

    def backup_db(self, backup_path):
        shutil.copy2(self.db_path, backup_path)
