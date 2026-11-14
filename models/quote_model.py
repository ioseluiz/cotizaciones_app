from models.database import Database
from models.seed_data import TIPO_A_TIPO_COTIZACION


def _insert_items(cursor, quote_id, items):
    for item in items:
        cursor.execute(
            "INSERT INTO detalles_cotizacion (cotizacion_id, servicio, descripcion, precio_total) VALUES (?, ?, ?, ?)",
            (quote_id, item['servicio'], item['descripcion'], item['precio_total'])
        )


class QuoteModel:
    def __init__(self, db: Database):
        self.db = db

    def get_all_quotes(self, negocio):
        """Devuelve (id, numero, cliente, fecha, proyecto) del negocio indicado."""
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT q.id, q.numero, COALESCE(c.nombre, ''), q.fecha, q.proyecto
                FROM cotizaciones q
                LEFT JOIN clientes c ON q.cliente_id = c.id
                WHERE q.negocio = ?
                ORDER BY q.fecha DESC, q.numero DESC
            """, (negocio,))
            return cursor.fetchall()

    def get_quote_by_id(self, quote_id):
        """0:id, 1:cliente, 2:tipo, 3:fecha, 4:proyecto, 5:observaciones, 6:email, 7:celular,
        8:negocio, 9:numero, 10:cliente_id"""
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT q.id, COALESCE(c.nombre, ''), q.tipo, q.fecha, q.proyecto, q.observaciones,
                       c.email, c.celular, q.negocio, q.numero, q.cliente_id
                FROM cotizaciones q
                LEFT JOIN clientes c ON q.cliente_id = c.id
                WHERE q.id = ?
            """, (quote_id,))
            return cursor.fetchone()

    def next_number(self, cursor, negocio):
        cursor.execute("SELECT COALESCE(MAX(numero), 0) + 1 FROM cotizaciones WHERE negocio=?", (negocio,))
        return cursor.fetchone()[0]

    def add_quote(self, negocio, cliente_id, fecha, proyecto, observaciones, items, entregables=None):
        """Crea la cotización con el siguiente número correlativo del negocio."""
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            numero = self.next_number(cursor, negocio)
            cursor.execute(
                "INSERT INTO cotizaciones (cliente_id, tipo, fecha, proyecto, observaciones, negocio, numero) "
                "VALUES (?, ?, ?, ?, ?, ?, ?)",
                (cliente_id, TIPO_A_TIPO_COTIZACION.get(negocio, negocio), fecha, proyecto,
                 observaciones, negocio, numero)
            )
            quote_id = cursor.lastrowid
            _insert_items(cursor, quote_id, items)
            if entregables is not None:
                self._replace_deliverables(cursor, quote_id, entregables)
            conn.commit()
            return quote_id

    def update_quote(self, quote_id, cliente_id, fecha, proyecto, observaciones, items, entregables=None):
        """Si `entregables` es None se conservan los entregables actuales. El negocio y número no cambian."""
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "UPDATE cotizaciones SET cliente_id=?, fecha=?, proyecto=?, observaciones=? WHERE id=?",
                (cliente_id, fecha, proyecto, observaciones, quote_id)
            )
            cursor.execute("DELETE FROM detalles_cotizacion WHERE cotizacion_id=?", (quote_id,))
            _insert_items(cursor, quote_id, items)
            if entregables is not None:
                self._replace_deliverables(cursor, quote_id, entregables)
            conn.commit()

    def delete_quote(self, quote_id):
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM detalles_cotizacion WHERE cotizacion_id=?", (quote_id,))
            cursor.execute("DELETE FROM cotizacion_entregables WHERE cotizacion_id=?", (quote_id,))
            cursor.execute("UPDATE estimados SET cotizacion_id=NULL WHERE cotizacion_id=?", (quote_id,))
            cursor.execute("DELETE FROM cotizaciones WHERE id=?", (quote_id,))
            conn.commit()

    def get_quote_items(self, quote_id):
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT id, servicio, descripcion, precio_total FROM detalles_cotizacion WHERE cotizacion_id=?", (quote_id,))
            return cursor.fetchall()

    def get_quote_deliverables(self, quote_id):
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT descripcion FROM cotizacion_entregables WHERE cotizacion_id=? ORDER BY orden, id",
                (quote_id,),
            )
            return [r[0] for r in cursor.fetchall()]

    @staticmethod
    def _replace_deliverables(cursor, quote_id, entregables):
        cursor.execute("DELETE FROM cotizacion_entregables WHERE cotizacion_id=?", (quote_id,))
        for orden, desc in enumerate(entregables):
            cursor.execute(
                "INSERT INTO cotizacion_entregables (cotizacion_id, descripcion, orden) VALUES (?, ?, ?)",
                (quote_id, desc, orden),
            )
