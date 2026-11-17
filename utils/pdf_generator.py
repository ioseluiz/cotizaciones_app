import os
import tempfile
import jinja2
from pypdf import PdfReader, PdfWriter
from PyQt6.QtGui import QTextDocument, QPageLayout, QPageSize, QFont, QImage, QPainter, QColor
from PyQt6.QtPrintSupport import QPrinter
from PyQt6.QtCore import QMarginsF, QSizeF, QUrl, QRectF, Qt
from utils.resource_path import resource_path
from models.business_model import format_quote_number
from utils.theme import accent_for
from utils.formatting import money, fmt_date, html_body
from utils.estimate_calculator import OPTION_TYPES, split_by_option

class PDFGenerator:
    def __init__(self):
        template_dir = resource_path('templates')
        self.env = jinja2.Environment(loader=jinja2.FileSystemLoader(template_dir))
        self.env.filters["money"] = money

    def generate(self, quote_data, items_data, output_path, deliverables=None, business=None, options=None,
                 annexes=None):
        """quote_data: fila de QuoteModel.get_quote_by_id. items_data: filas de get_quote_items
        (id, servicio, descripcion, precio, opcion). business: dict de BusinessModel.get.
        options: lista de get_quote_options; cada opción se muestra en su propia sección.
        annexes: [{"tipo", "titulo", "path", "contenido"}] que se agregan al final como
        "Anexo 1", "Anexo 2"... (PDF tal cual, imagen en una página, texto con formato)."""
        annexes = annexes or []
        template = self.env.get_template('quote_template.html')
        options = options or []
        base_items, option_items = split_by_option(
            items_data, len(options), option=lambda it: it[4] if len(it) > 4 else None
        )
        total = sum(item[3] for item in base_items)
        option_sections = []
        for i, (opt, rows) in enumerate(zip(options, option_items)):
            precio = sum(item[3] for item in rows)
            option_sections.append({
                "tipo": OPTION_TYPES.get(opt.get("tipo"), "Opción"),
                "nombre": opt.get("nombre") or f"Opción {i + 1}",
                "descripcion": opt.get("descripcion") or "",
                "items": rows,
                "precio": money(precio),
                "total": money(total + precio),
            })
        business = business or {}
        prefijo = business.get("prefijo")
        numero = quote_data[9] if len(quote_data) > 9 and quote_data[9] else quote_data[0]
        quote_number = format_quote_number(prefijo, numero) if prefijo else str(numero).zfill(4)

        # Color del negocio (azul marino Estructural / verde azulado Software)
        clave = business.get("clave") or (quote_data[8] if len(quote_data) > 8 else None)
        accent = accent_for(clave)

        logo_path = business.get("logo_path") or ""
        logo_url = QUrl.fromLocalFile(logo_path).toString() if logo_path and os.path.exists(logo_path) else ""

        html_content = template.render(
            quote_id=quote_number,
            client_name=quote_data[1],
            tipo=business.get("encabezado_titulo") or quote_data[2],
            fecha=fmt_date(quote_data[3]),
            proyecto=quote_data[4],
            observaciones=html_body(quote_data[5], keep_style=True),
            items=base_items,
            options=option_sections,
            deliverables=deliverables or [],
            annex_titles=[a.get("titulo") or f"Anexo {i + 1}" for i, a in enumerate(annexes)],
            total=money(total),
            encabezado_nombre=business.get("encabezado_nombre") or "",
            ruc=business.get("ruc") or "",
            email=business.get("email") or "",
            telefono=business.get("telefono") or "",
            firma=business.get("firma") or "",
            logo_url=logo_url,
            accent=accent["base"],
            accent_tint=accent["tint"],
        )

        if not annexes:
            self._print_html(html_content, output_path)
            return

        # Cotización + anexos: cada parte a un PDF temporal y luego se unen en orden
        with tempfile.TemporaryDirectory() as tmp:
            parts = [os.path.join(tmp, "cotizacion.pdf")]
            self._print_html(html_content, parts[0])
            for i, annex in enumerate(annexes, start=1):
                heading = f"Anexo {i}: {annex.get('titulo') or ''}".rstrip(": ")
                try:
                    parts.append(self._annex_pdf(annex, heading, os.path.join(tmp, f"anexo_{i}.pdf"),
                                                 accent["base"], accent["tint"]))
                except Exception as e:
                    raise ValueError(f"No se pudo agregar el anexo '{annex.get('titulo')}': {e}") from e
            self._merge(parts, output_path)

    # ------------------------------------------------------------------ partes
    @staticmethod
    def _new_printer(output_path):
        # Sin PrinterMode.HighResolution para mantener proporciones
        printer = QPrinter()
        printer.setPageSize(QPageSize(QPageSize.PageSizeId.A4))
        printer.setOutputFormat(QPrinter.OutputFormat.PdfFormat)
        printer.setOutputFileName(output_path)
        # Márgenes horizontales reales de 15mm y verticales muy pequeños (2mm)
        # QMarginsF(Izquierda, Arriba, Derecha, Abajo)
        printer.setPageMargins(QMarginsF(15, 2, 15, 2), QPageLayout.Unit.Millimeter)
        return printer

    def _print_html(self, html_content, output_path):
        document = QTextDocument()
        document.setDocumentMargin(0)

        # Fuente base global para que QTextDocument la use de referencia
        font = QFont("Helvetica")
        font.setPointSize(10)
        document.setDefaultFont(font)

        # QTextDocument ignora mucho CSS como max-width o paddings globales
        document.setHtml(html_content)

        printer = self._new_printer(output_path)
        # Ajustamos el tamaño del documento exactamente al área imprimible (papel restando márgenes)
        page_rect = printer.pageLayout().paintRectPixels(printer.resolution())
        document.setPageSize(QSizeF(page_rect.width(), page_rect.height()))

        document.print(printer)

    def _annex_pdf(self, annex, heading, output_path, accent, accent_tint):
        """Devuelve la ruta de un PDF con el anexo listo para unir."""
        tipo = annex.get("tipo")
        if tipo == "PDF":
            path = annex.get("path") or ""
            if not os.path.exists(path):
                raise FileNotFoundError("el archivo ya no existe")
            return path
        if tipo == "IMAGEN":
            self._print_image(annex.get("path") or "", heading, output_path, accent)
            return output_path
        html = self.env.get_template("annex_template.html").render(
            heading=heading, contenido=html_body(annex.get("contenido"), keep_style=True),
            accent=accent, accent_tint=accent_tint,
        )
        self._print_html(html, output_path)
        return output_path

    def _print_image(self, image_path, heading, output_path, accent):
        image = QImage(image_path)
        if image.isNull():
            raise ValueError("no se pudo abrir la imagen")
        printer = self._new_printer(output_path)
        # Márgenes más amplios arriba y abajo que en la cotización para el título
        printer.setPageMargins(QMarginsF(15, 12, 15, 12), QPageLayout.Unit.Millimeter)
        page = QRectF(printer.pageLayout().paintRectPixels(printer.resolution()))
        page.moveTo(0, 0)
        painter = QPainter(printer)
        try:
            font = QFont("Helvetica")
            font.setPixelSize(max(12, int(page.height() * 0.018)))
            font.setBold(True)
            painter.setFont(font)
            painter.setPen(QColor(accent))
            title_h = painter.fontMetrics().height() * 1.6
            painter.drawText(QRectF(page.left(), page.top(), page.width(), title_h),
                             Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter, heading.upper())
            painter.fillRect(QRectF(page.left(), page.top() + title_h, page.width(), 2), QColor(accent))
            area = QRectF(page.left(), page.top() + title_h + 12, page.width(), page.height() - title_h - 12)
            size = image.size().toSizeF()
            size.scale(area.size(), Qt.AspectRatioMode.KeepAspectRatio)
            # No agrandar imágenes pequeñas más allá de 2x (se verían pixeladas)
            if size.width() > image.width() * 2:
                size = image.size().toSizeF() * 2
            target = QRectF(area.left() + (area.width() - size.width()) / 2, area.top(), size.width(), size.height())
            painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
            painter.drawImage(target, image)
        finally:
            painter.end()

    @staticmethod
    def _merge(parts, output_path):
        writer = PdfWriter()
        for part in parts:
            reader = PdfReader(part)
            if reader.is_encrypted:
                reader.decrypt("")  # PDFs protegidos solo contra edición se pueden leer sin clave
            for page in reader.pages:
                writer.add_page(page)
        with open(output_path, "wb") as f:
            writer.write(f)
