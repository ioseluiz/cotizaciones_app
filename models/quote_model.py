from models.database import Database

class QuoteModel:
    def __init__(self, db: Database):
        self.db = db

    def get_all_quotes(self):
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT q.id, c.nombre, q.tipo, q.fecha, q.proyecto, q.observaciones
                FROM cotizaciones q
                JOIN clientes c ON q.cliente_id = c.id
                ORDER BY q.fecha DESC, q.id DESC
            """)
            return cursor.fetchall()
            
    def get_quote_by_id(self, quote_id):
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT q.id, c.nombre, q.tipo, q.fecha, q.proyecto, q.observaciones, c.email, c.celular
                FROM cotizaciones q
                JOIN clientes c ON q.cliente_id = c.id
                WHERE q.id = ?
            """, (quote_id,))
            return cursor.fetchone()

    def add_quote(self, cliente_id, tipo, fecha, proyecto, observaciones, items):
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO cotizaciones (cliente_id, tipo, fecha, proyecto, observaciones) VALUES (?, ?, ?, ?, ?)",
                (cliente_id, tipo, fecha, proyecto, observaciones)
            )
            quote_id = cursor.lastrowid
            
            for item in items:
                cursor.execute(
                    "INSERT INTO detalles_cotizacion (cotizacion_id, servicio, descripcion, precio_total) VALUES (?, ?, ?, ?)",
                    (quote_id, item['servicio'], item['descripcion'], item['precio_total'])
                )
            conn.commit()
            return quote_id

    def update_quote(self, quote_id, cliente_id, tipo, fecha, proyecto, observaciones, items):
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "UPDATE cotizaciones SET cliente_id=?, tipo=?, fecha=?, proyecto=?, observaciones=? WHERE id=?",
                (cliente_id, tipo, fecha, proyecto, observaciones, quote_id)
            )
            
            # Recrear items
            cursor.execute("DELETE FROM detalles_cotizacion WHERE cotizacion_id=?", (quote_id,))
            for item in items:
                cursor.execute(
                    "INSERT INTO detalles_cotizacion (cotizacion_id, servicio, descripcion, precio_total) VALUES (?, ?, ?, ?)",
                    (quote_id, item['servicio'], item['descripcion'], item['precio_total'])
                )
            conn.commit()

    def delete_quote(self, quote_id):
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM detalles_cotizacion WHERE cotizacion_id=?", (quote_id,))
            cursor.execute("DELETE FROM cotizaciones WHERE id=?", (quote_id,))
            conn.commit()

    def get_quote_items(self, quote_id):
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT id, servicio, descripcion, precio_total FROM detalles_cotizacion WHERE cotizacion_id=?", (quote_id,))
            return cursor.fetchall()