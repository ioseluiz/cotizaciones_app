from PyQt6.QtCore import QObject, pyqtSignal
from PyQt6.QtWidgets import QTableWidgetItem
from models.client_model import ClientModel
from views.clients_view import ClientsView

class ClientsPresenter(QObject):
    client_changed_signal = pyqtSignal()

    def __init__(self, view: ClientsView, model: ClientModel):
        super().__init__()
        self.view = view
        self.model = model
        
        self.selected_client_id = None
        
        # Conectar señales
        self.view.add_btn.clicked.connect(self.add_client)
        self.view.update_btn.clicked.connect(self.update_client)
        self.view.delete_btn.clicked.connect(self.delete_client)
        self.view.clear_btn.clicked.connect(self.clear_selection)
        self.view.table.itemSelectionChanged.connect(self.on_client_selected)
        
        self.load_clients()

    def load_clients(self):
        self.view.table.setRowCount(0)
        clients = self.model.get_all_clients()
        for row, client in enumerate(clients):
            self.view.table.insertRow(row)
            self.view.table.setItem(row, 0, QTableWidgetItem(str(client[0])))
            self.view.table.setItem(row, 1, QTableWidgetItem(client[1]))
            self.view.table.setItem(row, 2, QTableWidgetItem(client[2]))
            self.view.table.setItem(row, 3, QTableWidgetItem(client[3]))
        
        self.client_changed_signal.emit()

    def add_client(self):
        data = self.view.get_form_data()
        if not data["nombre"]:
            self.view.show_error("El nombre es obligatorio")
            return
            
        try:
            self.model.add_client(data["nombre"], data["email"], data["celular"])
            self.view.clear_form()
            self.load_clients()
            self.view.show_info("Cliente agregado exitosamente")
        except Exception as e:
            self.view.show_error(f"Error al agregar cliente: {str(e)}")

    def update_client(self):
        if not self.selected_client_id:
            return
            
        data = self.view.get_form_data()
        if not data["nombre"]:
            self.view.show_error("El nombre es obligatorio")
            return
            
        try:
            self.model.update_client(self.selected_client_id, data["nombre"], data["email"], data["celular"])
            self.view.clear_form()
            self.selected_client_id = None
            self.load_clients()
            self.view.show_info("Cliente actualizado exitosamente")
        except Exception as e:
            self.view.show_error(f"Error al actualizar cliente: {str(e)}")

    def delete_client(self):
        if not self.selected_client_id:
            return
            
        try:
            self.model.delete_client(self.selected_client_id)
            self.view.clear_form()
            self.selected_client_id = None
            self.load_clients()
            self.view.show_info("Cliente eliminado exitosamente")
        except Exception as e:
            self.view.show_error(f"Error al eliminar cliente: {str(e)}")

    def on_client_selected(self):
        selected_items = self.view.table.selectedItems()
        if not selected_items:
            self.clear_selection()
            return
            
        row = selected_items[0].row()
        self.selected_client_id = int(self.view.table.item(row, 0).text())
        nombre = self.view.table.item(row, 1).text()
        email = self.view.table.item(row, 2).text()
        celular = self.view.table.item(row, 3).text()
        
        self.view.set_form_data(nombre, email, celular)
        self.view.add_btn.setEnabled(False)
        self.view.update_btn.setEnabled(True)
        self.view.delete_btn.setEnabled(True)

    def clear_selection(self):
        self.selected_client_id = None
        self.view.clear_form()
        self.view.table.clearSelection()