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


def _read_config():
    config_path = get_config_path()
    if os.path.exists(config_path):
        try:
            with open(config_path, "r") as f:
                return json.load(f)
        except Exception:
            pass
    return {}


def get_config_value(key, default=None):
    return _read_config().get(key, default)


def set_config_value(key, value):
    config = _read_config()
    config[key] = value
    with open(get_config_path(), "w") as f:
        json.dump(config, f)


def set_db_path(new_path):
    set_config_value("db_path", new_path)


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
            self._init_estimator_tables(cursor)
            self._seed_estimator_data(cursor)
            self._init_business_tables(cursor)
            conn.commit()
        self._migrate_to_businesses()

    def _init_estimator_tables(self, cursor):
        cursor.executescript('''
            CREATE TABLE IF NOT EXISTS cotizacion_entregables (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                cotizacion_id INTEGER NOT NULL,
                descripcion TEXT NOT NULL,
                orden INTEGER DEFAULT 0,
                FOREIGN KEY (cotizacion_id) REFERENCES cotizaciones (id)
            );
            CREATE TABLE IF NOT EXISTS roles (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nombre TEXT NOT NULL,
                tarifa_hora REAL NOT NULL DEFAULT 0,
                tipo TEXT NOT NULL DEFAULT 'AMBOS'
            );
            CREATE TABLE IF NOT EXISTS estimados (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                cliente_id INTEGER,
                tipo TEXT NOT NULL,
                proyecto TEXT NOT NULL,
                fecha TEXT NOT NULL,
                contingencia_pct REAL NOT NULL DEFAULT 0,
                margen_pct REAL NOT NULL DEFAULT 0,
                aplica_itbms INTEGER NOT NULL DEFAULT 0,
                cotizacion_id INTEGER,
                notas TEXT,
                FOREIGN KEY (cliente_id) REFERENCES clientes (id)
            );
            CREATE TABLE IF NOT EXISTS estimado_actividades (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                estimado_id INTEGER NOT NULL,
                fase TEXT,
                actividad TEXT NOT NULL,
                rol_id INTEGER,
                horas REAL NOT NULL DEFAULT 0,
                tarifa_hora REAL NOT NULL DEFAULT 0,
                orden INTEGER DEFAULT 0,
                FOREIGN KEY (estimado_id) REFERENCES estimados (id)
            );
            CREATE TABLE IF NOT EXISTS estimado_gastos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                estimado_id INTEGER NOT NULL,
                descripcion TEXT NOT NULL,
                monto REAL NOT NULL DEFAULT 0,
                FOREIGN KEY (estimado_id) REFERENCES estimados (id)
            );
            CREATE TABLE IF NOT EXISTS estimado_entregables (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                estimado_id INTEGER NOT NULL,
                descripcion TEXT NOT NULL,
                orden INTEGER DEFAULT 0,
                FOREIGN KEY (estimado_id) REFERENCES estimados (id)
            );
            CREATE TABLE IF NOT EXISTS plantillas (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nombre TEXT NOT NULL,
                tipo TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS plantilla_actividades (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                plantilla_id INTEGER NOT NULL,
                fase TEXT,
                actividad TEXT NOT NULL,
                rol_id INTEGER,
                horas REAL NOT NULL DEFAULT 0,
                orden INTEGER DEFAULT 0,
                FOREIGN KEY (plantilla_id) REFERENCES plantillas (id)
            );
            CREATE TABLE IF NOT EXISTS plantilla_entregables (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                plantilla_id INTEGER NOT NULL,
                descripcion TEXT NOT NULL,
                orden INTEGER DEFAULT 0,
                FOREIGN KEY (plantilla_id) REFERENCES plantillas (id)
            );
        ''')

    def _seed_estimator_data(self, cursor):
        from models.seed_data import DEFAULT_ROLES, DEFAULT_TEMPLATES

        cursor.execute("SELECT COUNT(*) FROM roles")
        if cursor.fetchone()[0] == 0:
            cursor.executemany(
                "INSERT INTO roles (nombre, tarifa_hora, tipo) VALUES (?, ?, ?)",
                DEFAULT_ROLES,
            )

        cursor.execute("SELECT COUNT(*) FROM plantillas")
        if cursor.fetchone()[0] == 0:
            cursor.execute("SELECT nombre, id FROM roles")
            role_ids = dict(cursor.fetchall())
            for tpl in DEFAULT_TEMPLATES:
                cursor.execute(
                    "INSERT INTO plantillas (nombre, tipo) VALUES (?, ?)",
                    (tpl["nombre"], tpl["tipo"]),
                )
                tpl_id = cursor.lastrowid
                for orden, (fase, actividad, rol, horas) in enumerate(tpl["actividades"]):
                    cursor.execute(
                        "INSERT INTO plantilla_actividades (plantilla_id, fase, actividad, rol_id, horas, orden) "
                        "VALUES (?, ?, ?, ?, ?, ?)",
                        (tpl_id, fase, actividad, role_ids.get(rol), horas, orden),
                    )
                for orden, desc in enumerate(tpl["entregables"]):
                    cursor.execute(
                        "INSERT INTO plantilla_entregables (plantilla_id, descripcion, orden) VALUES (?, ?, ?)",
                        (tpl_id, desc, orden),
                    )

    def move_db(self, new_dir):
        new_path = os.path.join(new_dir, os.path.basename(self.db_path))
        if self.db_path != new_path:
            shutil.copy2(self.db_path, new_path)
            self.db_path = new_path
            set_db_path(new_path)

    def backup_db(self, backup_path):
        shutil.copy2(self.db_path, backup_path)

    # ------------------------------------------------------------ negocios
    def _init_business_tables(self, cursor):
        from models.seed_data import DEFAULT_BUSINESSES

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS negocios (
                clave TEXT PRIMARY KEY,
                nombre TEXT NOT NULL,
                prefijo TEXT NOT NULL,
                encabezado_nombre TEXT,
                encabezado_titulo TEXT,
                ruc TEXT,
                email TEXT,
                telefono TEXT,
                firma TEXT,
                logo_path TEXT,
                condiciones TEXT,
                email_asunto TEXT,
                email_cuerpo TEXT,
                whatsapp_mensaje TEXT
            )
        ''')
        for b in DEFAULT_BUSINESSES:
            cols = ", ".join(b.keys())
            marks = ", ".join("?" for _ in b)
            cursor.execute(f"INSERT OR IGNORE INTO negocios ({cols}) VALUES ({marks})", tuple(b.values()))

        for table, column, decl in (
            ("clientes", "negocio", "TEXT"),
            ("cotizaciones", "negocio", "TEXT"),
            ("cotizaciones", "numero", "INTEGER"),
        ):
            cursor.execute(f"PRAGMA table_info({table})")
            if column not in [r[1] for r in cursor.fetchall()]:
                cursor.execute(f"ALTER TABLE {table} ADD COLUMN {column} {decl}")

    def _needs_business_migration(self, cursor):
        cursor.execute("SELECT COUNT(*) FROM clientes WHERE negocio IS NULL")
        pending = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM cotizaciones WHERE negocio IS NULL")
        return pending + cursor.fetchone()[0] > 0

    def _migrate_to_businesses(self):
        """Asigna cada cotización y cliente existente a un negocio. Las cotizaciones
        conservan su número (= id) para que coincidan con los PDFs ya enviados.
        Los clientes con cotizaciones de ambos negocios (o de ninguno) se duplican."""
        from models.seed_data import TIPO_SOFTWARE, TIPO_ESTRUCTURAL, TIPO_A_TIPO_COTIZACION

        with self.get_connection() as conn:
            cursor = conn.cursor()
            if not self._needs_business_migration(cursor):
                return

        # Backup de seguridad antes de modificar datos existentes
        try:
            shutil.copy2(self.db_path, self.db_path + ".bak-antes-de-negocios")
        except Exception:
            pass

        software_tipo = TIPO_A_TIPO_COTIZACION[TIPO_SOFTWARE]
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "UPDATE cotizaciones SET negocio = CASE WHEN tipo = ? THEN ? ELSE ? END "
                "WHERE negocio IS NULL",
                (software_tipo, TIPO_SOFTWARE, TIPO_ESTRUCTURAL),
            )
            cursor.execute("UPDATE cotizaciones SET numero = id WHERE numero IS NULL")

            cursor.execute("SELECT id, nombre, email, celular FROM clientes WHERE negocio IS NULL")
            for client_id, nombre, email, celular in cursor.fetchall():
                cursor.execute(
                    "SELECT negocio FROM cotizaciones WHERE cliente_id=? "
                    "UNION SELECT tipo FROM estimados WHERE cliente_id=?",
                    (client_id, client_id),
                )
                used = {r[0] for r in cursor.fetchall()}
                if used == {TIPO_SOFTWARE}:
                    cursor.execute("UPDATE clientes SET negocio=? WHERE id=?", (TIPO_SOFTWARE, client_id))
                    continue
                cursor.execute("UPDATE clientes SET negocio=? WHERE id=?", (TIPO_ESTRUCTURAL, client_id))
                if used == {TIPO_ESTRUCTURAL}:
                    continue
                # Ambos negocios o ninguno: copia para Software con sus cotizaciones/estimados
                cursor.execute(
                    "INSERT INTO clientes (nombre, email, celular, negocio) VALUES (?, ?, ?, ?)",
                    (nombre, email, celular, TIPO_SOFTWARE),
                )
                copy_id = cursor.lastrowid
                cursor.execute(
                    "UPDATE cotizaciones SET cliente_id=? WHERE cliente_id=? AND negocio=?",
                    (copy_id, client_id, TIPO_SOFTWARE),
                )
                cursor.execute(
                    "UPDATE estimados SET cliente_id=? WHERE cliente_id=? AND tipo=?",
                    (copy_id, client_id, TIPO_SOFTWARE),
                )
            conn.commit()
