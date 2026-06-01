import subprocess
import urllib.parse
from PyQt6.QtCore import QObject, QUrl, QMimeData
from PyQt6.QtWidgets import QTableWidgetItem, QFileDialog
from PyQt6.QtGui import QDesktopServices, QGuiApplication
from models.quote_model import QuoteModel
from models.client_model import ClientModel
from views.quotes_view import QuotesView
from utils.pdf_generator import PDFGenerator
from utils.email_worker import EmailWorker


class QuotesPresenter(QObject):
    def __init__(
        self, view: QuotesView, quote_model: QuoteModel, client_model: ClientModel
    ):
        super().__init__()
        self.view = view
        self.quote_model = quote_model
        self.client_model = client_model

        self.selected_quote_id = None
        self.clients_map = {}

        self.view.add_item_btn.clicked.connect(self.add_item_row)
        self.view.remove_item_btn.clicked.connect(self.remove_item_row)
        self.view.items_table.itemChanged.connect(self.calculate_total)
        self.view.save_btn.clicked.connect(self.save_quote)
        self.view.clear_btn.clicked.connect(self.clear_form)
        self.view.quotes_table.itemSelectionChanged.connect(self.on_quote_selected)
        self.view.delete_quote_btn.clicked.connect(self.delete_quote)
        self.view.generate_pdf_btn.clicked.connect(self.generate_pdf)
        self.view.whatsapp_btn.clicked.connect(self.send_whatsapp)

        self.load_clients()
        self.load_quotes()

    def load_clients(self):
        self.view.client_combo.clear()
        self.clients_map.clear()
        clients = self.client_model.get_all_clients()
        for c in clients:
            self.clients_map[c[0]] = c[1]
            self.view.client_combo.addItem(c[1], userData=c[0])

    def load_quotes(self):
        self.view.quotes_table.setRowCount(0)
        quotes = self.quote_model.get_all_quotes()
        for row, q in enumerate(quotes):
            self.view.quotes_table.insertRow(row)
            self.view.quotes_table.setItem(row, 0, QTableWidgetItem(str(q[0])))
            self.view.quotes_table.setItem(row, 1, QTableWidgetItem(q[3]))
            self.view.quotes_table.setItem(row, 2, QTableWidgetItem(q[1]))
            self.view.quotes_table.setItem(row, 3, QTableWidgetItem(q[4]))
            self.view.quotes_table.setItem(row, 4, QTableWidgetItem(q[2]))

    def add_item_row(self):
        row = self.view.items_table.rowCount()
        self.view.items_table.insertRow(row)
        self.view.items_table.setItem(row, 0, QTableWidgetItem(""))
        self.view.items_table.setItem(row, 1, QTableWidgetItem(""))
        self.view.items_table.setItem(row, 2, QTableWidgetItem("0.0"))

    def remove_item_row(self):
        current_row = self.view.items_table.currentRow()
        if current_row >= 0:
            self.view.items_table.removeRow(current_row)
            self.calculate_total()

    def calculate_total(self):
        total = 0.0
        for row in range(self.view.items_table.rowCount()):
            item = self.view.items_table.item(row, 2)
            if item:
                try:
                    val = float(item.text())
                    total += val
                except ValueError:
                    pass
        self.view.total_label.setText(f"Gran Total: ${total:.2f}")

    def save_quote(self):
        client_data = self.view.client_combo.currentData()
        if not client_data:
            self.view.show_error("Debe seleccionar un cliente")
            return

        tipo = self.view.type_combo.currentText()
        fecha = self.view.date_edit.date().toString("yyyy-MM-dd")
        proyecto = self.view.project_input.text().strip()
        observaciones = self.view.observations_edit.toHtml()

        if not proyecto:
            self.view.show_error("El proyecto es obligatorio")
            return

        items = []
        for row in range(self.view.items_table.rowCount()):
            servicio = (
                self.view.items_table.item(row, 0).text()
                if self.view.items_table.item(row, 0)
                else ""
            )
            desc = (
                self.view.items_table.item(row, 1).text()
                if self.view.items_table.item(row, 1)
                else ""
            )
            precio_str = (
                self.view.items_table.item(row, 2).text()
                if self.view.items_table.item(row, 2)
                else "0"
            )
            try:
                precio = float(precio_str)
            except ValueError:
                precio = 0.0

            if servicio:
                items.append(
                    {"servicio": servicio, "descripcion": desc, "precio_total": precio}
                )

        if not items:
            self.view.show_error("Debe agregar al menos un item a la cotización")
            return

        try:
            if self.selected_quote_id:
                self.quote_model.update_quote(
                    self.selected_quote_id,
                    client_data,
                    tipo,
                    fecha,
                    proyecto,
                    observaciones,
                    items,
                )
                self.view.show_info("Cotización actualizada")
            else:
                self.quote_model.add_quote(
                    client_data, tipo, fecha, proyecto, observaciones, items
                )
                self.view.show_info("Cotización creada")

            self.clear_form()
            self.load_quotes()
        except Exception as e:
            self.view.show_error(f"Error guardando cotización: {str(e)}")

    def clear_form(self):
        self.selected_quote_id = None
        self.view.project_input.clear()
        self.view.observations_edit.clear()
        self.view.items_table.setRowCount(0)
        self.calculate_total()
        self.view.save_btn.setText("Guardar Cotización")
        self.view.quotes_table.clearSelection()
        self.view.delete_quote_btn.setEnabled(False)
        self.view.generate_pdf_btn.setEnabled(False)
        self.view.whatsapp_btn.setEnabled(False)

    def on_quote_selected(self):
        selected_items = self.view.quotes_table.selectedItems()
        if not selected_items:
            self.clear_form()
            return

        row = selected_items[0].row()
        self.selected_quote_id = int(self.view.quotes_table.item(row, 0).text())

        quote = self.quote_model.get_quote_by_id(self.selected_quote_id)
        if quote:
            index = self.view.client_combo.findText(quote[1])
            if index >= 0:
                self.view.client_combo.setCurrentIndex(index)

            index_tipo = self.view.type_combo.findText(quote[2])
            if index_tipo >= 0:
                self.view.type_combo.setCurrentIndex(index_tipo)

            self.view.project_input.setText(quote[4])
            self.view.observations_edit.setHtml(quote[5] if quote[5] else "")

            items = self.quote_model.get_quote_items(self.selected_quote_id)
            self.view.items_table.blockSignals(True)
            self.view.items_table.setRowCount(0)
            for r, it in enumerate(items):
                self.view.items_table.insertRow(r)
                self.view.items_table.setItem(r, 0, QTableWidgetItem(it[1]))
                self.view.items_table.setItem(r, 1, QTableWidgetItem(it[2]))
                self.view.items_table.setItem(r, 2, QTableWidgetItem(str(it[3])))
            self.view.items_table.blockSignals(False)
            self.calculate_total()

            self.view.save_btn.setText("Actualizar Cotización")
            self.view.delete_quote_btn.setEnabled(True)
            self.view.generate_pdf_btn.setEnabled(True)
            self.view.whatsapp_btn.setEnabled(True)

    def delete_quote(self):
        if not self.selected_quote_id:
            return

        try:
            self.quote_model.delete_quote(self.selected_quote_id)
            self.clear_form()
            self.load_quotes()
            self.view.show_info("Cotización eliminada")
        except Exception as e:
            self.view.show_error(f"Error al eliminar cotización: {str(e)}")

    def generate_pdf(self):
        if not self.selected_quote_id:
            return

        file_path, _ = QFileDialog.getSaveFileName(
            self.view,
            "Guardar Cotización en PDF",
            f"Cotizacion_{self.selected_quote_id}.pdf",
            "PDF Files (*.pdf)",
        )
        if not file_path:
            return

        quote = self.quote_model.get_quote_by_id(self.selected_quote_id)
        items = self.quote_model.get_quote_items(self.selected_quote_id)

        try:
            generator = PDFGenerator()
            generator.generate(quote, items, file_path)
            self.view.show_info(
                f"PDF Guardado Exitosamente en:\n{file_path}\n\nSe procederá a enviar por correo en segundo plano."
            )

            client_email = quote[6]  # email
            if client_email:
                # Iniciamos el envío de correo en un hilo de trabajo (Worker Thread) para no congelar la UI
                self.email_worker = EmailWorker(client_email, file_path)
                self.email_worker.finished_signal.connect(self.on_email_finished)
                self.view.generate_pdf_btn.setEnabled(False)
                self.view.generate_pdf_btn.setText("Enviando Correo...")
                self.email_worker.start()
            else:
                self.view.show_error(
                    "El cliente no tiene un correo configurado. El PDF solo se guardó localmente."
                )

        except Exception as e:
            self.view.show_error(f"Error al generar/enviar PDF: {str(e)}")

    def on_email_finished(self, success, message):
        self.view.generate_pdf_btn.setEnabled(True)
        self.view.generate_pdf_btn.setText("Enviar por Correo")

        if success:
            self.view.show_info(message)
        else:
            self.view.show_error(f"Error al enviar el correo: {message}")

    def send_whatsapp(self):
        if not self.selected_quote_id:
            return

        quote = self.quote_model.get_quote_by_id(self.selected_quote_id)
        if not quote:
            return

        # quote format: 0:id, 1:nombre, 2:tipo, 3:fecha, 4:proyecto, 5:observaciones, 6:email, 7:celular
        celular = quote[7]

        if not celular:
            self.view.show_error(
                "El cliente seleccionado no tiene un número de celular registrado."
            )
            return

        # Solicitar primero que se guarde el PDF
        file_path, _ = QFileDialog.getSaveFileName(
            self.view,
            "Guardar Cotización en PDF para enviar por WhatsApp",
            f"Cotizacion_{self.selected_quote_id}.pdf",
            "PDF Files (*.pdf)",
        )
        if not file_path:
            return  # El usuario canceló

        items = self.quote_model.get_quote_items(self.selected_quote_id)

        try:
            # Generar y guardar el PDF localmente
            generator = PDFGenerator()
            generator.generate(quote, items, file_path)
        except Exception as e:
            self.view.show_error(f"Error al generar PDF: {str(e)}")
            return

        # Copiar el PDF al portapapeles como archivo para que el usuario solo
        # tenga que pegarlo (Ctrl+V) dentro del chat de WhatsApp Web.
        try:
            mime = QMimeData()
            mime.setUrls([QUrl.fromLocalFile(file_path)])
            QGuiApplication.clipboard().setMimeData(mime)
        except Exception:
            pass  # Si falla el portapapeles, queda el Explorador como respaldo.

        # Abrir el Explorador con el PDF preseleccionado (respaldo para arrastrarlo).
        try:
            subprocess.Popen(["explorer", "/select,", file_path])
        except Exception:
            pass

        self.view.show_info(
            "PDF guardado en:\n"
            f"{file_path}\n\n"
            "Para enviarlo por WhatsApp:\n"
            "1. Se abrirá WhatsApp Web con el mensaje listo.\n"
            "2. El PDF ya está copiado: pulse Ctrl+V dentro del chat para adjuntarlo.\n"
            "3. Si no se pega, arrastre el archivo desde la carpeta que se abrió."
        )

        # Limpiar el número de teléfono para la URL (remover espacios, guiones, etc.)
        celular_limpio = "".join(filter(str.isdigit, celular))

        # Si tiene 8 digitos asume que es de Panamá
        if len(celular_limpio) == 8:
            celular_limpio = f"507{celular_limpio}"

        mensaje = f"Estimado {quote[1]},\n\nAdjunto a este mensaje encontrará la cotización solicitada para el proyecto '{quote[4]}'.\n\nQuedo a su entera disposición para cualquier consulta.\n\nSaludos cordiales,\n\nIng. Jose Luis Munoz\nTel: 64998718\nEmail: joseluism1412@gmail.com"
        mensaje_codificado = urllib.parse.quote(mensaje)

        url = f"https://wa.me/{celular_limpio}?text={mensaje_codificado}"

        # Abrir el navegador por defecto
        QDesktopServices.openUrl(QUrl(url))
