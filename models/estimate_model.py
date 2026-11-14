from models.database import Database


class EstimateModel:
    """Estimados de proyecto. Estructura de `data` usada en add/update/get:

    {
        "cliente_id", "tipo", "proyecto", "fecha", "contingencia_pct",
        "margen_pct", "aplica_itbms", "notas",
        "actividades": [{"fase", "actividad", "rol_id", "horas", "tarifa_hora"}],
        "gastos": [{"descripcion", "monto"}],
        "entregables": [str],
    }
    """

    def __init__(self, db: Database):
        self.db = db

    def get_all_estimates(self, negocio):
        """Devuelve (id, fecha, cliente, proyecto, cotizacion_id, numero_cotizacion) del negocio."""
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT e.id, e.fecha, COALESCE(c.nombre, ''), e.proyecto, e.cotizacion_id, q.numero
                FROM estimados e
                LEFT JOIN clientes c ON e.cliente_id = c.id
                LEFT JOIN cotizaciones q ON e.cotizacion_id = q.id
                WHERE e.tipo = ?
                ORDER BY e.fecha DESC, e.id DESC
            """, (negocio,))
            return cursor.fetchall()

    def get_quote_number(self, quote_id):
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT numero FROM cotizaciones WHERE id=?", (quote_id,))
            row = cursor.fetchone()
            return row[0] if row else None

    def get_estimate(self, estimate_id):
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT cliente_id, tipo, proyecto, fecha, contingencia_pct, margen_pct,
                       aplica_itbms, notas, cotizacion_id
                FROM estimados WHERE id=?
            """, (estimate_id,))
            row = cursor.fetchone()
            if not row:
                return None
            data = {
                "id": estimate_id,
                "cliente_id": row[0],
                "tipo": row[1],
                "proyecto": row[2],
                "fecha": row[3],
                "contingencia_pct": row[4],
                "margen_pct": row[5],
                "aplica_itbms": bool(row[6]),
                "notas": row[7] or "",
                "cotizacion_id": row[8],
            }
            cursor.execute("""
                SELECT a.fase, a.actividad, a.rol_id, a.horas, a.tarifa_hora, COALESCE(r.nombre, '')
                FROM estimado_actividades a
                LEFT JOIN roles r ON a.rol_id = r.id
                WHERE a.estimado_id=? ORDER BY a.orden, a.id
            """, (estimate_id,))
            data["actividades"] = [
                {"fase": r[0] or "", "actividad": r[1], "rol_id": r[2], "horas": r[3],
                 "tarifa_hora": r[4], "rol": r[5]}
                for r in cursor.fetchall()
            ]
            cursor.execute(
                "SELECT descripcion, monto FROM estimado_gastos WHERE estimado_id=? ORDER BY id",
                (estimate_id,),
            )
            data["gastos"] = [{"descripcion": r[0], "monto": r[1]} for r in cursor.fetchall()]
            cursor.execute(
                "SELECT descripcion FROM estimado_entregables WHERE estimado_id=? ORDER BY orden, id",
                (estimate_id,),
            )
            data["entregables"] = [r[0] for r in cursor.fetchall()]
            return data

    def add_estimate(self, data):
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO estimados (cliente_id, tipo, proyecto, fecha, contingencia_pct,
                                       margen_pct, aplica_itbms, notas)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, self._header_values(data))
            estimate_id = cursor.lastrowid
            self._insert_children(cursor, estimate_id, data)
            conn.commit()
            return estimate_id

    def update_estimate(self, estimate_id, data):
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE estimados SET cliente_id=?, tipo=?, proyecto=?, fecha=?, contingencia_pct=?,
                                     margen_pct=?, aplica_itbms=?, notas=?
                WHERE id=?
            """, self._header_values(data) + (estimate_id,))
            self._delete_children(cursor, estimate_id)
            self._insert_children(cursor, estimate_id, data)
            conn.commit()

    def delete_estimate(self, estimate_id):
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            self._delete_children(cursor, estimate_id)
            cursor.execute("DELETE FROM estimados WHERE id=?", (estimate_id,))
            conn.commit()

    def link_quote(self, estimate_id, quote_id):
        with self.db.get_connection() as conn:
            conn.execute("UPDATE estimados SET cotizacion_id=? WHERE id=?", (quote_id, estimate_id))
            conn.commit()

    def quote_exists(self, quote_id):
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT 1 FROM cotizaciones WHERE id=?", (quote_id,))
            return cursor.fetchone() is not None

    @staticmethod
    def _header_values(data):
        return (
            data.get("cliente_id"),
            data["tipo"],
            data["proyecto"],
            data["fecha"],
            data.get("contingencia_pct", 0.0),
            data.get("margen_pct", 0.0),
            1 if data.get("aplica_itbms") else 0,
            data.get("notas", ""),
        )

    @staticmethod
    def _delete_children(cursor, estimate_id):
        for table in ("estimado_actividades", "estimado_gastos", "estimado_entregables"):
            cursor.execute(f"DELETE FROM {table} WHERE estimado_id=?", (estimate_id,))

    @staticmethod
    def _insert_children(cursor, estimate_id, data):
        for orden, a in enumerate(data.get("actividades", [])):
            cursor.execute("""
                INSERT INTO estimado_actividades (estimado_id, fase, actividad, rol_id, horas, tarifa_hora, orden)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (estimate_id, a.get("fase", ""), a["actividad"], a.get("rol_id"),
                  a.get("horas", 0.0), a.get("tarifa_hora", 0.0), orden))
        for g in data.get("gastos", []):
            cursor.execute(
                "INSERT INTO estimado_gastos (estimado_id, descripcion, monto) VALUES (?, ?, ?)",
                (estimate_id, g["descripcion"], g.get("monto", 0.0)),
            )
        for orden, desc in enumerate(data.get("entregables", [])):
            cursor.execute(
                "INSERT INTO estimado_entregables (estimado_id, descripcion, orden) VALUES (?, ?, ?)",
                (estimate_id, desc, orden),
            )
