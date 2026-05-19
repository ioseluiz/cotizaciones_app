from models.database import Database

class ClientModel:
    def __init__(self, db: Database):
        self.db = db

    def get_all_clients(self):
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT id, nombre, email, celular FROM clientes ORDER BY nombre")
            return cursor.fetchall()

    def add_client(self, nombre, email, celular):
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO clientes (nombre, email, celular) VALUES (?, ?, ?)",
                (nombre, email, celular)
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

    def delete_client(self, client_id):
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            # Idealmente se debería chequear si tiene cotizaciones, pero para mantenerlo simple:
            cursor.execute("DELETE FROM clientes WHERE id=?", (client_id,))
            conn.commit()