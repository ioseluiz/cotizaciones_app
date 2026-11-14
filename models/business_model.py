from models.database import Database

BUSINESS_FIELDS = [
    "clave", "nombre", "prefijo", "encabezado_nombre", "encabezado_titulo", "ruc",
    "email", "telefono", "firma", "logo_path", "condiciones", "email_asunto",
    "email_cuerpo", "whatsapp_mensaje",
]
EDITABLE_FIELDS = [f for f in BUSINESS_FIELDS if f != "clave"]


def format_quote_number(prefijo, numero):
    """EST-0007, SW-0012..."""
    return f"{prefijo}-{int(numero or 0):04d}"


def render_message(template, **values):
    """Reemplaza {cliente}, {proyecto}, {numero} sin fallar si el usuario escribe otras llaves."""
    text = template or ""
    for key, value in values.items():
        text = text.replace("{" + key + "}", str(value))
    return text


class BusinessModel:
    def __init__(self, db: Database):
        self.db = db

    def get_all(self):
        """Lista de (clave, nombre) en orden fijo: Estructural, Software."""
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT clave, nombre FROM negocios ORDER BY clave")
            return cursor.fetchall()

    def get(self, clave):
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(f"SELECT {', '.join(BUSINESS_FIELDS)} FROM negocios WHERE clave=?", (clave,))
            row = cursor.fetchone()
            return dict(zip(BUSINESS_FIELDS, row)) if row else None

    def update(self, clave, data):
        fields = [f for f in EDITABLE_FIELDS if f in data]
        if not fields:
            return
        with self.db.get_connection() as conn:
            conn.execute(
                f"UPDATE negocios SET {', '.join(f + '=?' for f in fields)} WHERE clave=?",
                tuple(data[f] for f in fields) + (clave,),
            )
            conn.commit()
