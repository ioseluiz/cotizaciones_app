from models.database import Database
from models.seed_data import TIPO_AMBOS


class RoleModel:
    def __init__(self, db: Database):
        self.db = db

    def get_all_roles(self):
        """Devuelve (id, nombre, tarifa_hora, tipo)."""
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT id, nombre, tarifa_hora, tipo FROM roles ORDER BY tipo, nombre")
            return cursor.fetchall()

    def get_roles_for_type(self, tipo):
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT id, nombre, tarifa_hora, tipo FROM roles WHERE tipo IN (?, ?) ORDER BY nombre",
                (tipo, TIPO_AMBOS),
            )
            return cursor.fetchall()

    def add_role(self, nombre, tarifa_hora, tipo):
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO roles (nombre, tarifa_hora, tipo) VALUES (?, ?, ?)",
                (nombre, tarifa_hora, tipo),
            )
            conn.commit()
            return cursor.lastrowid

    def update_role(self, role_id, nombre, tarifa_hora, tipo):
        with self.db.get_connection() as conn:
            conn.execute(
                "UPDATE roles SET nombre=?, tarifa_hora=?, tipo=? WHERE id=?",
                (nombre, tarifa_hora, tipo, role_id),
            )
            conn.commit()

    def delete_role(self, role_id):
        with self.db.get_connection() as conn:
            conn.execute("DELETE FROM roles WHERE id=?", (role_id,))
            conn.commit()
