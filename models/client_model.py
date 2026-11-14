from models.database import Database

class ClientModel:
    def __init__(self, db: Database):
        self.db = db

    def get_all_clients(self, negocio):
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT id, nombre, email, celular FROM clientes WHERE negocio=? ORDER BY nombre",
                (negocio,),
            )
            return cursor.fetchall()

    def add_client(self, negocio, nombre, email, celular):
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO clientes (nombre, email, celular, negocio) VALUES (?, ?, ?, ?)",
                (nombre, email, celular, negocio)
            )
            conn.commit()
            return cursor.lastrowid

    def update_client(self, client_id, nombre, email, celular):
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "UPDATE clientes SET nombre=?, email=?, celular=? WHERE id=?",
                (nombre, email, celular, client_id)
            )
            conn.commit()

    def count_quotes(self, client_id):
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM cotizaciones WHERE cliente_id=?", (client_id,))
            return cursor.fetchone()[0]

    def delete_client(self, client_id):
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM clientes WHERE id=?", (client_id,))
            conn.commit()
