from models.database import Database


class TemplateModel:
    def __init__(self, db: Database):
        self.db = db

    def get_templates(self, tipo=None):
        """Devuelve (id, nombre, tipo). Filtra por tipo si se indica."""
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            if tipo:
                cursor.execute("SELECT id, nombre, tipo FROM plantillas WHERE tipo=? ORDER BY nombre", (tipo,))
            else:
                cursor.execute("SELECT id, nombre, tipo FROM plantillas ORDER BY tipo, nombre")
            return cursor.fetchall()

    def get_template(self, template_id):
        """Devuelve {"actividades": [{fase, actividad, rol_id, horas, tarifa_hora, rol}], "entregables": [str]}.
        La tarifa sale del rol actual, para que la plantilla siempre use tarifas vigentes."""
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT a.fase, a.actividad, a.rol_id, a.horas, COALESCE(r.tarifa_hora, 0), COALESCE(r.nombre, '')
                FROM plantilla_actividades a
                LEFT JOIN roles r ON a.rol_id = r.id
                WHERE a.plantilla_id=? ORDER BY a.orden, a.id
            """, (template_id,))
            actividades = [
                {"fase": r[0] or "", "actividad": r[1], "rol_id": r[2], "horas": r[3],
                 "tarifa_hora": r[4], "rol": r[5]}
                for r in cursor.fetchall()
            ]
            cursor.execute(
                "SELECT descripcion FROM plantilla_entregables WHERE plantilla_id=? ORDER BY orden, id",
                (template_id,),
            )
            entregables = [r[0] for r in cursor.fetchall()]
            return {"actividades": actividades, "entregables": entregables}

    def save_template(self, nombre, tipo, actividades, entregables):
        """Crea la plantilla o reemplaza el contenido de una existente con el mismo nombre y tipo."""
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT id FROM plantillas WHERE nombre=? AND tipo=?", (nombre, tipo))
            row = cursor.fetchone()
            if row:
                template_id = row[0]
                self._delete_children(cursor, template_id)
            else:
                cursor.execute("INSERT INTO plantillas (nombre, tipo) VALUES (?, ?)", (nombre, tipo))
                template_id = cursor.lastrowid
            for orden, a in enumerate(actividades):
                cursor.execute("""
                    INSERT INTO plantilla_actividades (plantilla_id, fase, actividad, rol_id, horas, orden)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (template_id, a.get("fase", ""), a["actividad"], a.get("rol_id"), a.get("horas", 0.0), orden))
            for orden, desc in enumerate(entregables):
                cursor.execute(
                    "INSERT INTO plantilla_entregables (plantilla_id, descripcion, orden) VALUES (?, ?, ?)",
                    (template_id, desc, orden),
                )
            conn.commit()
            return template_id

    def delete_template(self, template_id):
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            self._delete_children(cursor, template_id)
            cursor.execute("DELETE FROM plantillas WHERE id=?", (template_id,))
            conn.commit()

    @staticmethod
    def _delete_children(cursor, template_id):
        cursor.execute("DELETE FROM plantilla_actividades WHERE plantilla_id=?", (template_id,))
        cursor.execute("DELETE FROM plantilla_entregables WHERE plantilla_id=?", (template_id,))
