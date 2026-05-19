import sqlite3
import shutil
import os
import json

CONFIG_FILE = "config.json"
DEFAULT_DB_NAME = "cotizaciones.db"

def get_db_path():
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, 'r') as f:
                config = json.load(f)
                db_path = config.get("db_path")
                if db_path and os.path.exists(os.path.dirname(db_path)):
                    return db_path
        except Exception:
            pass
    return os.path.abspath(DEFAULT_DB_NAME)

def set_db_path(new_path):
    config = {}
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, 'r') as f:
            try:
                config = json.load(f)
            except Exception:
                pass
    config["db_path"] = new_path
    with open(CONFIG_FILE, 'w') as f:
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