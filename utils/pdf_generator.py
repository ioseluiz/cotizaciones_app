import os
import jinja2
from PyQt6.QtGui import QTextDocument, QPageLayout, QPageSize, QFont
from PyQt6.QtPrintSupport import QPrinter
from PyQt6.QtCore import QMarginsF, QSizeF, QUrl
from utils.resource_path import resource_path
from models.business_model import format_quote_number

class PDFGenerator:
    def __init__(self):
        template_dir = resource_path('templates')
        self.env = jinja2.Environment(loader=jinja2.FileSystemLoader(template_dir))

    def generate(self, quote_data, items_data, output_path, deliverables=None, business=None):
        """quote_data: fila de QuoteModel.get_quote_by_id. business: dict de BusinessModel.get."""
        template = self.env.get_template('quote_template.html')
        total = sum(item[3] for item in items_data)
        business = business or {}
        prefijo = business.get("prefijo")
        numero = quote_data[9] if len(quote_data) > 9 and quote_data[9] else quote_data[0]
        quote_number = format_quote_number(prefijo, numero) if prefijo else str(numero).zfill(4)

        logo_path = business.get("logo_path") or ""
        logo_url = QUrl.fromLocalFile(logo_path).toString() if logo_path and os.path.exists(logo_path) else ""

        html_content = template.render(
            quote_id=quote_number,
            client_name=quote_data[1],
            tipo=business.get("encabezado_titulo") or quote_data[2],
            fecha=quote_data[3],
            proyecto=quote_data[4],
            observaciones=quote_data[5] if quote_data[5] else "",
            items=items_data,
            deliverables=deliverables or [],
            total=f"{total:.2f}",
            encabezado_nombre=business.get("encabezado_nombre") or "",
            ruc=business.get("ruc") or "",
            email=business.get("email") or "",
            telefono=business.get("telefono") or "",
            firma=business.get("firma") or "",
            logo_url=logo_url,
        )

        document = QTextDocument()
        document.setDocumentMargin(0)
        
        # Establecemos una fuente base global para que QDocument la use de referencia
        font = QFont("Helvetica")
        font.setPointSize(10)
        document.setDefaultFont(font)
        
        # Le pasamos el HTML limpio, QTextDocument ignora mucho CSS como max-width o paddings globales
        document.setHtml(html_content)
        
        # Configurar la impresora sin PrinterMode.HighResolution para mantener proporciones
        printer = QPrinter()
        printer.setPageSize(QPageSize(QPageSize.PageSizeId.A4))
        printer.setOutputFormat(QPrinter.OutputFormat.PdfFormat)
        printer.setOutputFileName(output_path)
        
        # IMPORTANTE: Aquí aplicamos márgenes horizontales reales de 15mm y verticales muy pequeños (2mm)
        # QMarginsF(Izquierda, Arriba, Derecha, Abajo)
        printer.setPageMargins(QMarginsF(15, 2, 15, 2), QPageLayout.Unit.Millimeter)
        
        # Ajustamos el tamaño del documento exactamente al área imprimible (papel restando márgenes)
        page_rect = printer.pageLayout().paintRectPixels(printer.resolution())
        document.setPageSize(QSizeF(page_rect.width(), page_rect.height()))
        
        document.print(printer)
