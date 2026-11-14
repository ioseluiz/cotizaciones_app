from PyQt6.QtCore import QObject, Qt, pyqtSignal
from PyQt6.QtWidgets import QTableWidgetItem
from models.client_model import ClientModel
from views.clients_view import ClientsView


class ClientsPresenter(QObject):
    client_changed_signal = pyqtSignal()

    def __init__(self, view: ClientsView, model: ClientModel, context):
        super().__init__()
        self.view = view
        self.model = model
        self.context = context
        self.context.changed.connect(self.on_business_changed)

        self.selected_client_id = None

        self.view.save_btn.clicked.connect(self.save_client)
        self.view.delete_btn.clicked.connect(self.delete_client)
        self.view.clear_btn.clicked.connect(self.clear_selection)
        self.view.table.itemSelectionChanged.connect(self.on_client_selected)

        self.load_clients()

    def load_clients(self):
        table = self.view.table
        table.blockSignals(True)
        table.setRowCount(0)
        for row, (client_id, nombre, email, celular) in enumerate(self.model.get_all_clients(self.context.current)):
            table.insertRow(row)
            name_item = QTableWidgetItem(nombre)
            name_item.setData(Qt.ItemDataRole.UserRole, client_id)
            table.setItem(row, 0, name_item)
            table.setItem(row, 1, QTableWidgetItem(email or ""))
            table.setItem(row, 2, QTableWidgetItem(celular or ""))
        table.blockSignals(False)
        self.view.set_count(table.rowCount())
        if self.selected_client_id:
            self._reselect(self.selected_client_id)
        self.client_changed_signal.emit()

    def _reselect(self, client_id):
        table = self.view.table
        for row in range(table.rowCount()):
            if table.item(row, 0).data(Qt.ItemDataRole.UserRole) == client_id:
                table.blockSignals(True)
                table.selectRow(row)
                table.blockSignals(False)
                return

    def save_client(self):
        data = self.view.get_form_data()
        if not data["nombre"]:
            self.view.show_error("El nombre es obligatorio")
            self.view.name_input.setFocus()
            return
        try:
            if self.selected_client_id:
                self.model.update_client(self.selected_client_id, data["nombre"], data["email"], data["celular"])
                self.view.show_toast(f"Cliente '{data['nombre']}' actualizado")
            else:
                self.selected_client_id = self.model.add_client(
                    self.context.current, data["nombre"], data["email"], data["celular"]
                )
                self.view.show_toast(f"Cliente '{data['nombre']}' agregado")
            self.load_clients()
            self.view.set_mode(True)
        except Exception as e:
            self.view.show_error(f"Error al guardar cliente: {str(e)}")

    def delete_client(self):
        if not self.selected_client_id:
            return
        nombre = self.view.name_input.text().strip()
        n_quotes = self.model.count_quotes(self.selected_client_id)
        message = f"¿Eliminar al cliente '{nombre}'?"
        if n_quotes:
            message += (f"\n\nTiene {n_quotes} cotización(es); quedarán sin cliente asignado.")
        if not self.view.ask_yes_no(message, "Eliminar cliente"):
            return
        try:
            self.model.delete_client(self.selected_client_id)
            self.clear_selection()
            self.load_clients()
            self.view.show_toast(f"Cliente '{nombre}' eliminado")
        except Exception as e:
            self.view.show_error(f"Error al eliminar cliente: {str(e)}")

    def on_client_selected(self):
        selected_items = self.view.table.selectedItems()
        if not selected_items:
            return
        row = selected_items[0].row()
        self.selected_client_id = self.view.table.item(row, 0).data(Qt.ItemDataRole.UserRole)
        self.view.set_form_data(
            self.view.table.item(row, 0).text(),
            self.view.table.item(row, 1).text(),
            self.view.table.item(row, 2).text(),
        )
        self.view.set_mode(True)

    def clear_selection(self):
        self.selected_client_id = None
        self.view.table.blockSignals(True)
        self.view.table.clearSelection()
        self.view.table.blockSignals(False)
        self.view.clear_form()

    def on_business_changed(self, _clave):
        self.clear_selection()
        self.load_clients()
