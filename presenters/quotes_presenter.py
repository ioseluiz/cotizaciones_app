import os
import subprocess
import tempfile
import urllib.parse
from PyQt6.QtCore import QObject, QUrl, QMimeData, Qt, QDate
from PyQt6.QtWidgets import QTableWidgetItem, QFileDialog
from PyQt6.QtGui import QDesktopServices, QGuiApplication
from models.quote_model import QuoteModel
from models.client_model import ClientModel
from models.business_model import BusinessModel, format_quote_number, render_message
from views.quotes_view import QuotesView, COL_PRECIO, COL_OPCION
from views.options_widgets import make_option_combo, option_of, rebuild_option_combos, option_label
from views.widgets import money, parse_number, numeric_item, fmt_date
from utils.pdf_generator import PDFGenerator
from utils.email_worker import EmailWorker

# Índices de la fila devuelta por QuoteModel.get_quote_by_id
Q_ID, Q_CLIENTE, Q_TIPO, Q_FECHA, Q_PROYECTO, Q_OBS, Q_EMAIL, Q_CELULAR, Q_NEGOCIO, Q_NUMERO, Q_CLIENTE_ID = range(11)


class QuotesPresenter(QObject):
    def __init__(
        self, view: QuotesView, quote_model: QuoteModel, client_model: ClientModel,
        business_model: BusinessModel, context
    ):
        super().__init__()
        self.view = view
        self.quote_model = quote_model
        self.client_model = client_model
        self.business_model = business_model
        self.context = context

        self.selected_quote_id = None
        self.current_options = []  # [{"nombre", "tipo", "descripcion"}] de la cotización en edición

        self.view.add_item_btn.clicked.connect(self.add_item_row)
        self.view.remove_item_btn.clicked.connect(self.remove_item_row)
        self.view.items_table.itemChanged.connect(self.calculate_total)
        self.view.save_btn.clicked.connect(self.save_quote)
        self.view.clear_btn.clicked.connect(self.clear_form)
        self.view.quotes_table.itemSelectionChanged.connect(self.on_quote_selected)
        self.view.delete_quote_btn.clicked.connect(self.delete_quote)
        self.view.generate_pdf_btn.clicked.connect(self.generate_pdf)
        self.view.whatsapp_btn.clicked.connect(self.send_whatsapp)
        self.view.preview_pdf_btn.clicked.connect(self.preview_pdf)
        self.view.options_btn.clicked.connect(self.edit_options)
        self.context.changed.connect(self.on_business_changed)

        self.load_clients()
        self.load_quotes()
        self.clear_form()

    # ------------------------------------------------------------------ helpers
    def business(self, clave=None):
        return self.business_model.get(clave or self.context.current) or {}

    def quote_code(self, quote):
        prefijo = self.business(quote[Q_NEGOCIO]).get("prefijo", "")
        return format_quote_number(prefijo, quote[Q_NUMERO] or quote[Q_ID])

    def on_business_changed(self, _clave):
        self.load_clients()
        self.load_quotes()
        self.clear_form()

    # -------------------------------------------------------------------- carga
    def load_clients(self):
        current = self.view.client_combo.currentData()
        self.view.client_combo.clear()
        for c in self.client_model.get_all_clients(self.context.current):
            self.view.client_combo.addItem(c[1], userData=c[0])
        idx = self.view.client_combo.findData(current)
        if idx >= 0:
            self.view.client_combo.setCurrentIndex(idx)

    def load_quotes(self):
        prefijo = self.business().get("prefijo", "")
        table = self.view.quotes_table
        table.blockSignals(True)
        table.setRowCount(0)
        for row, q in enumerate(self.quote_model.get_all_quotes(self.context.current)):
            quote_id, numero, cliente, fecha, proyecto = q
            table.insertRow(row)
            num_item = QTableWidgetItem(format_quote_number(prefijo, numero))
            num_item.setData(Qt.ItemDataRole.UserRole, quote_id)
            table.setItem(row, 0, num_item)
            table.setItem(row, 1, QTableWidgetItem(fmt_date(fecha)))
            table.setItem(row, 2, QTableWidgetItem(cliente))
            table.setItem(row, 3, QTableWidgetItem(proyecto))
        table.blockSignals(False)
        self.view.set_count(table.rowCount())
        if self.selected_quote_id:
            self._reselect(self.selected_quote_id)

    def select_quote(self, quote_id):
        """Selecciona y carga una cotización de la lista (si pertenece al negocio activo)."""
        self.view.search_input.clear()
        table = self.view.quotes_table
        for row in range(table.rowCount()):
            if table.item(row, 0).data(Qt.ItemDataRole.UserRole) == quote_id:
                # Seleccionar sin depender de la señal (la fila puede estar ya seleccionada)
                table.blockSignals(True)
                table.selectRow(row)
                table.blockSignals(False)
                table.scrollToItem(table.item(row, 0))
                self.load_quote(quote_id)
                return True
        return False

    def _reselect(self, quote_id):
        table = self.view.quotes_table
        for row in range(table.rowCount()):
            if table.item(row, 0).data(Qt.ItemDataRole.UserRole) == quote_id:
                table.blockSignals(True)
                table.selectRow(row)
                table.blockSignals(False)
                return

    # -------------------------------------------------------------------- items
    def add_item_row(self):
        row = self.view.items_table.rowCount()
        self.view.items_table.insertRow(row)
        self.view.items_table.setItem(row, 0, QTableWidgetItem(""))
        self.view.items_table.setItem(row, 1, QTableWidgetItem(""))
        self.view.items_table.setItem(row, COL_PRECIO, numeric_item("0.00"))
        self.view.items_table.setCellWidget(row, COL_OPCION, self._option_combo())
        self.view.items_table.setCurrentCell(row, 0)
        self.view.items_table.editItem(self.view.items_table.item(row, 0))

    def remove_item_row(self):
        current_row = self.view.items_table.currentRow()
        if current_row >= 0:
            self.view.items_table.removeRow(current_row)
            self.calculate_total()

    def calculate_total(self, *_args):
        """El total mostrado es el del alcance base; las opciones se cotizan aparte."""
        total = 0.0
        table = self.view.items_table
        for row in range(table.rowCount()):
            item = table.item(row, COL_PRECIO)
            if item and option_of(table, row, COL_OPCION) is None:
                total += parse_number(item.text())
        self.view.set_total(money(total), len(self.current_options))

    # ----------------------------------------------------------------- opciones
    def _option_names(self):
        return [option_label(i, o["nombre"]) for i, o in enumerate(self.current_options)]

    def _option_combo(self, opcion=None):
        return make_option_combo(self._option_names(), opcion, self.calculate_total)

    def _set_options(self, options, index_map=None):
        self.current_options = options
        rebuild_option_combos(self.view.items_table, COL_OPCION, self._option_names(), index_map,
                              self.calculate_total)
        self.view.show_option_column(bool(options))
        self.calculate_total()

    def edit_options(self):
        dialog = self.view.make_options_dialog()
        dialog.editor.set_options(self.current_options)
        if not dialog.exec():
            return
        options = dialog.editor.options()
        for i, o in enumerate(options):
            if not o["nombre"]:
                o["nombre"] = f"Opción {i + 1}"
        self._set_options(options, dialog.editor.take_index_map())
        if options:
            self.view.show_toast("Asigne cada servicio a su opción en la columna \"Opción\" y guarde")

    # ------------------------------------------------------------------ guardar
    def save_quote(self):
        client_data = self.view.client_combo.currentData()
        if not client_data:
            self.view.show_error("Debe seleccionar un cliente")
            return

        fecha = self.view.date_edit.date().toString("yyyy-MM-dd")
        proyecto = self.view.project_input.text().strip()
        observaciones = self.view.observations_edit.toHtml()

        if not proyecto:
            self.view.show_error("El proyecto es obligatorio")
            return

        items = []
        table = self.view.items_table
        for row in range(table.rowCount()):
            servicio = table.item(row, 0).text() if table.item(row, 0) else ""
            desc = table.item(row, 1).text() if table.item(row, 1) else ""
            precio = parse_number(table.item(row, COL_PRECIO).text()) if table.item(row, COL_PRECIO) else 0.0
            if servicio:
                items.append({"servicio": servicio, "descripcion": desc, "precio_total": precio,
                              "opcion": option_of(table, row, COL_OPCION)})

        if not any(it["opcion"] is None for it in items):
            self.view.show_error("Debe agregar al menos un servicio en el alcance base")
            return
        for i, o in enumerate(self.current_options):
            if not any(it["opcion"] == i for it in items):
                self.view.show_error(
                    f"La opción '{o['nombre']}' no tiene servicios asignados.\n\n"
                    "Asígnele servicios en la columna \"Opción\" o quítela con el botón Opciones..."
                )
                return

        try:
            if self.selected_quote_id:
                quote_id = self.selected_quote_id
                self.quote_model.update_quote(quote_id, client_data, fecha, proyecto, observaciones, items,
                                              opciones=self.current_options)
                accion = "actualizada"
            else:
                quote_id = self.quote_model.add_quote(
                    self.context.current, client_data, fecha, proyecto, observaciones, items,
                    opciones=self.current_options,
                )
                accion = "creada"
            # Quedarse en la cotización guardada para poder enviarla de inmediato
            self.selected_quote_id = quote_id
            self.load_quotes()
            self.select_quote(quote_id)
            code = self.quote_code(self.quote_model.get_quote_by_id(quote_id))
            self.view.show_toast(f"Cotización {code} {accion}")
        except Exception as e:
            self.view.show_error(f"Error guardando cotización: {str(e)}")

    def clear_form(self):
        self.selected_quote_id = None
        self.view.project_input.clear()
        self.view.date_edit.setDate(QDate.currentDate())
        # Las cotizaciones nuevas arrancan con las condiciones por defecto del negocio
        self.view.observations_edit.set_clean_html(self.business().get("condiciones") or "")
        self.view.items_table.setRowCount(0)
        self._set_options([])
        self.view.set_mode(None)
        self.view.quotes_table.blockSignals(True)
        self.view.quotes_table.clearSelection()
        self.view.quotes_table.blockSignals(False)

    def on_quote_selected(self):
        selected_items = self.view.quotes_table.selectedItems()
        if not selected_items:
            self.clear_form()
            return

        row = selected_items[0].row()
        self.load_quote(self.view.quotes_table.item(row, 0).data(Qt.ItemDataRole.UserRole))

    def load_quote(self, quote_id):
        """Carga la cotización en el formulario en modo edición."""
        quote = self.quote_model.get_quote_by_id(quote_id)
        if not quote:
            return
        self.selected_quote_id = quote_id
        index = self.view.client_combo.findData(quote[Q_CLIENTE_ID])
        if index >= 0:
            self.view.client_combo.setCurrentIndex(index)

        fecha = QDate.fromString(quote[Q_FECHA], "yyyy-MM-dd")
        if fecha.isValid():
            self.view.date_edit.setDate(fecha)
        self.view.project_input.setText(quote[Q_PROYECTO])
        self.view.observations_edit.set_clean_html(quote[Q_OBS] if quote[Q_OBS] else "")

        items = self.quote_model.get_quote_items(self.selected_quote_id)
        self.view.items_table.blockSignals(True)
        self.view.items_table.setRowCount(0)
        self.current_options = self.quote_model.get_quote_options(self.selected_quote_id)
        for r, it in enumerate(items):
            self.view.items_table.insertRow(r)
            self.view.items_table.setItem(r, 0, QTableWidgetItem(it[1]))
            self.view.items_table.setItem(r, 1, QTableWidgetItem(it[2]))
            self.view.items_table.setItem(r, COL_PRECIO, numeric_item(f"{it[3]:,.2f}"))
            self.view.items_table.setCellWidget(r, COL_OPCION, self._option_combo(it[4]))
        self.view.items_table.blockSignals(False)
        self.view.show_option_column(bool(self.current_options))
        self.calculate_total()

        self.view.set_mode(self.quote_code(quote))

    def delete_quote(self):
        if not self.selected_quote_id:
            return
        quote = self.quote_model.get_quote_by_id(self.selected_quote_id)
        code = self.quote_code(quote) if quote else ""
        if not self.view.ask_yes_no(
                f"¿Eliminar la cotización {code}?\n\nEsta acción no se puede deshacer.", "Eliminar cotización"):
            return

        try:
            self.quote_model.delete_quote(self.selected_quote_id)
            self.clear_form()
            self.load_quotes()
            self.view.show_toast(f"Cotización {code} eliminada")
        except Exception as e:
            self.view.show_error(f"Error al eliminar cotización: {str(e)}")

    # --------------------------------------------------------------- PDF/envíos
    def _save_pdf(self, quote, title):
        """Pide la ruta, genera el PDF y devuelve la ruta (o None si se canceló/falló)."""
        code = self.quote_code(quote)
        file_path, _ = QFileDialog.getSaveFileName(
            self.view, title, f"Cotizacion_{code}.pdf", "PDF Files (*.pdf)"
        )
        if not file_path:
            return None
        try:
            PDFGenerator().generate(
                quote,
                self.quote_model.get_quote_items(quote[Q_ID]),
                file_path,
                self.quote_model.get_quote_deliverables(quote[Q_ID]),
                self.business(quote[Q_NEGOCIO]),
                self.quote_model.get_quote_options(quote[Q_ID]),
            )
        except Exception as e:
            self.view.show_error(f"Error al generar PDF: {str(e)}")
            return None
        return file_path

    def _message_values(self, quote):
        return {"cliente": quote[Q_CLIENTE], "proyecto": quote[Q_PROYECTO], "numero": self.quote_code(quote)}

    def preview_pdf(self):
        """Genera el PDF en una carpeta temporal y lo abre con el visor predeterminado."""
        if not self.selected_quote_id:
            return
        quote = self.quote_model.get_quote_by_id(self.selected_quote_id)
        if not quote:
            return
        path = os.path.join(tempfile.gettempdir(), f"Vista_previa_{self.quote_code(quote)}.pdf")
        try:
            PDFGenerator().generate(
                quote,
                self.quote_model.get_quote_items(quote[Q_ID]),
                path,
                self.quote_model.get_quote_deliverables(quote[Q_ID]),
                self.business(quote[Q_NEGOCIO]),
                self.quote_model.get_quote_options(quote[Q_ID]),
            )
        except Exception as e:
            self.view.show_error(f"Error al generar la vista previa: {e}")
            return
        QDesktopServices.openUrl(QUrl.fromLocalFile(path))

    def generate_pdf(self):
        if not self.selected_quote_id:
            return
        quote = self.quote_model.get_quote_by_id(self.selected_quote_id)
        if not quote:
            return

        file_path = self._save_pdf(quote, "Guardar Cotización en PDF")
        if not file_path:
            return

        client_email = quote[Q_EMAIL]
        if not client_email:
            self.view.show_error(
                f"PDF guardado en:\n{file_path}\n\n"
                "El cliente no tiene un correo configurado. El PDF solo se guardó localmente."
            )
            return

        self.view.show_info(
            f"PDF Guardado Exitosamente en:\n{file_path}\n\nSe procederá a enviar por correo en segundo plano."
        )
        business = self.business(quote[Q_NEGOCIO])
        values = self._message_values(quote)
        subject = render_message(business.get("email_asunto"), **values) or None
        body = render_message(business.get("email_cuerpo"), **values) or None

        # Envío en un hilo de trabajo (Worker Thread) para no congelar la UI
        self.email_worker = EmailWorker(client_email, file_path, subject, body)
        self.email_worker.finished_signal.connect(self.on_email_finished)
        self.view.generate_pdf_btn.setEnabled(False)
        self.view.generate_pdf_btn.setText("Enviando...")
        self.email_worker.start()

    def on_email_finished(self, success, message):
        self.view.generate_pdf_btn.setEnabled(True)
        self.view.generate_pdf_btn.setText("Correo")

        if success:
            self.view.show_toast(message)
        else:
            self.view.show_error(f"Error al enviar el correo: {message}")

    def send_whatsapp(self):
        if not self.selected_quote_id:
            return

        quote = self.quote_model.get_quote_by_id(self.selected_quote_id)
        if not quote:
            return

        celular = quote[Q_CELULAR]
        if not celular:
            self.view.show_error(
                "El cliente seleccionado no tiene un número de celular registrado."
            )
            return

        file_path = self._save_pdf(quote, "Guardar Cotización en PDF para enviar por WhatsApp")
        if not file_path:
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
            "2. El PDF ya está copiado: pulse Ctrl+V (Cmd+V en Mac) dentro del chat para adjuntarlo.\n"
            "3. Si no se pega, arrastre el archivo desde la carpeta que se abrió."
        )

        # Limpiar el número de teléfono para la URL (remover espacios, guiones, etc.)
        celular_limpio = "".join(filter(str.isdigit, celular))

        # Si tiene 8 digitos asume que es de Panamá
        if len(celular_limpio) == 8:
            celular_limpio = f"507{celular_limpio}"

        mensaje = render_message(self.business(quote[Q_NEGOCIO]).get("whatsapp_mensaje"),
                                 **self._message_values(quote))
        url = f"https://web.whatsapp.com/send?phone={celular_limpio}&text={urllib.parse.quote(mensaje)}"

        # Abrir el navegador por defecto
        QDesktopServices.openUrl(QUrl(url))
