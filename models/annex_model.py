"""Anexos del PDF de la cotización: archivos PDF, imágenes y páginas de texto.

Un anexo pertenece a una cotización (`cotizacion_id`) o es fijo de un negocio
(`negocio`) y se agrega a todas sus cotizaciones, salvo que se excluya en una.
Los archivos se copian a la carpeta `anexos/` junto a la base de datos para que
el PDF siga completo aunque el original se mueva o se borre.
"""
import os
import shutil
import uuid

from models.database import Database

TIPO_PDF = "PDF"
TIPO_IMAGEN = "IMAGEN"
TIPO_TEXTO = "TEXTO"
TIPOS = {TIPO_PDF: "PDF", TIPO_IMAGEN: "Imagen", TIPO_TEXTO: "Página de texto"}

IMAGE_EXTENSIONS = (".png", ".jpg", ".jpeg", ".bmp", ".gif", ".webp")
FILE_FILTER = "PDF o imágenes (*.pdf *.png *.jpg *.jpeg *.bmp *.gif *.webp)"

_COLUMNS = "id, cotizacion_id, negocio, tipo, titulo, archivo, contenido, orden"


def file_type(path):
    """Tipo de anexo según la extensión, o None si no se admite."""
    ext = os.path.splitext(path)[1].lower()
    if ext == ".pdf":
        return TIPO_PDF
    if ext in IMAGE_EXTENSIONS:
        return TIPO_IMAGEN
    return None


class AnnexModel:
    def __init__(self, db: Database):
        self.db = db

    # ------------------------------------------------------------ archivos
    def annex_dir(self):
        path = os.path.join(os.path.dirname(os.path.abspath(self.db.db_path)), "anexos")
        os.makedirs(path, exist_ok=True)
        return path

    def file_path(self, annex):
        return os.path.join(self.annex_dir(), annex["archivo"]) if annex.get("archivo") else ""

    def _remove_file(self, archivo):
        if archivo:
            try:
                os.remove(os.path.join(self.annex_dir(), archivo))
            except OSError:
                pass

    # ------------------------------------------------------------- lectura
    @staticmethod
    def _row(r):
        return {"id": r[0], "cotizacion_id": r[1], "negocio": r[2], "tipo": r[3], "titulo": r[4],
                "archivo": r[5], "contenido": r[6] or "", "orden": r[7]}

    def get(self, annex_id):
        with self.db.get_connection() as conn:
            r = conn.execute(f"SELECT {_COLUMNS} FROM anexos WHERE id=?", (annex_id,)).fetchone()
            return self._row(r) if r else None

    def get_business_annexes(self, negocio):
        with self.db.get_connection() as conn:
            rows = conn.execute(
                f"SELECT {_COLUMNS} FROM anexos WHERE negocio=? AND cotizacion_id IS NULL ORDER BY orden, id",
                (negocio,),
            ).fetchall()
            return [self._row(r) for r in rows]

    def get_quote_annexes(self, quote_id):
        with self.db.get_connection() as conn:
            rows = conn.execute(
                f"SELECT {_COLUMNS} FROM anexos WHERE cotizacion_id=? ORDER BY orden, id", (quote_id,)
            ).fetchall()
            return [self._row(r) for r in rows]

    def get_excluded(self, quote_id):
        with self.db.get_connection() as conn:
            rows = conn.execute(
                "SELECT anexo_id FROM cotizacion_anexos_excluidos WHERE cotizacion_id=?", (quote_id,)
            ).fetchall()
            return {r[0] for r in rows}

    def annexes_for_pdf(self, quote_id, negocio):
        """Anexos fijos del negocio (no excluidos) y luego los de la cotización, en orden."""
        excluded = self.get_excluded(quote_id) if quote_id else set()
        fixed = [a for a in self.get_business_annexes(negocio) if a["id"] not in excluded] if negocio else []
        own = self.get_quote_annexes(quote_id) if quote_id else []
        return fixed + own

    # ----------------------------------------------------------- escritura
    def _next_order(self, cursor, quote_id, negocio):
        if quote_id:
            cursor.execute("SELECT COALESCE(MAX(orden), -1) + 1 FROM anexos WHERE cotizacion_id=?", (quote_id,))
        else:
            cursor.execute(
                "SELECT COALESCE(MAX(orden), -1) + 1 FROM anexos WHERE negocio=? AND cotizacion_id IS NULL",
                (negocio,),
            )
        return cursor.fetchone()[0]

    def _insert(self, quote_id, negocio, tipo, titulo, archivo=None, contenido=""):
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            orden = self._next_order(cursor, quote_id, negocio)
            cursor.execute(
                "INSERT INTO anexos (cotizacion_id, negocio, tipo, titulo, archivo, contenido, orden) "
                "VALUES (?, ?, ?, ?, ?, ?, ?)",
                (quote_id, None if quote_id else negocio, tipo, titulo, archivo, contenido, orden),
            )
            conn.commit()
            return cursor.lastrowid

    def add_file(self, source_path, titulo=None, quote_id=None, negocio=None):
        """Copia el archivo a la carpeta de anexos y lo registra. Devuelve el id."""
        tipo = file_type(source_path)
        if tipo is None:
            raise ValueError("Solo se admiten archivos PDF o imágenes (PNG, JPG, BMP, GIF, WEBP).")
        ext = os.path.splitext(source_path)[1].lower()
        archivo = f"{uuid.uuid4().hex}{ext}"
        shutil.copy2(source_path, os.path.join(self.annex_dir(), archivo))
        titulo = (titulo or os.path.splitext(os.path.basename(source_path))[0]).strip()
        try:
            return self._insert(quote_id, negocio, tipo, titulo, archivo=archivo)
        except Exception:
            self._remove_file(archivo)
            raise

    def add_text(self, titulo, contenido, quote_id=None, negocio=None):
        return self._insert(quote_id, negocio, TIPO_TEXTO, titulo.strip(), contenido=contenido)

    def update(self, annex_id, titulo, contenido=None):
        with self.db.get_connection() as conn:
            if contenido is None:
                conn.execute("UPDATE anexos SET titulo=? WHERE id=?", (titulo.strip(), annex_id))
            else:
                conn.execute("UPDATE anexos SET titulo=?, contenido=? WHERE id=?",
                             (titulo.strip(), contenido, annex_id))
            conn.commit()

    def reorder(self, annex_ids):
        with self.db.get_connection() as conn:
            for orden, annex_id in enumerate(annex_ids):
                conn.execute("UPDATE anexos SET orden=? WHERE id=?", (orden, annex_id))
            conn.commit()

    def set_excluded(self, quote_id, annex_id, excluded):
        with self.db.get_connection() as conn:
            conn.execute("DELETE FROM cotizacion_anexos_excluidos WHERE cotizacion_id=? AND anexo_id=?",
                         (quote_id, annex_id))
            if excluded:
                conn.execute("INSERT INTO cotizacion_anexos_excluidos (cotizacion_id, anexo_id) VALUES (?, ?)",
                             (quote_id, annex_id))
            conn.commit()

    def delete(self, annex_id):
        annex = self.get(annex_id)
        if not annex:
            return
        with self.db.get_connection() as conn:
            conn.execute("DELETE FROM cotizacion_anexos_excluidos WHERE anexo_id=?", (annex_id,))
            conn.execute("DELETE FROM anexos WHERE id=?", (annex_id,))
            conn.commit()
        self._remove_file(annex["archivo"])

    def delete_for_quote(self, quote_id):
        """Borra los anexos propios de la cotización (y sus archivos) y sus exclusiones."""
        annexes = self.get_quote_annexes(quote_id)
        with self.db.get_connection() as conn:
            conn.execute("DELETE FROM anexos WHERE cotizacion_id=?", (quote_id,))
            conn.execute("DELETE FROM cotizacion_anexos_excluidos WHERE cotizacion_id=?", (quote_id,))
            conn.commit()
        for a in annexes:
            self._remove_file(a["archivo"])
