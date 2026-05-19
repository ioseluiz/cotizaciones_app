from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem, 
    QPushButton, QLineEdit, QLabel, QMessageBox, QHeaderView
)

class ClientsView(QWidget):
    def __init__(self):
        super().__init__()
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()
        
        # Formulario
        form_layout = QHBoxLayout()
        
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("Nombre del Cliente")
        self.email_input = QLineEdit()
        self.email_input.setPlaceholderText("Correo Electrónico")
        self.phone_input = QLineEdit()
        self.phone_input.setPlaceholderText("Celular")
        
        self.add_btn = QPushButton("Agregar Cliente")
        self.update_btn = QPushButton("Actualizar Cliente")
        self.delete_btn = QPushButton("Eliminar Cliente")
        self.clear_btn = QPushButton("Limpiar Formulario")
        
        self.update_btn.setEnabled(False)
        self.delete_btn.setEnabled(False)
        
        form_layout.addWidget(QLabel("Nombre:"))
        form_layout.addWidget(self.name_input)
        form_layout.addWidget(QLabel("Email:"))
        form_layout.addWidget(self.email_input)
        form_layout.addWidget(QLabel("Celular:"))
        form_layout.addWidget(self.phone_input)
        
        btn_layout = QHBoxLayout()
        btn_layout.addWidget(self.add_btn)
        btn_layout.addWidget(self.update_btn)
        btn_layout.addWidget(self.delete_btn)
        btn_layout.addWidget(self.clear_btn)
        
        # Tabla
        self.table = QTableWidget()
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels(["ID", "Nombre", "Email", "Celular"])
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        
        layout.addLayout(form_layout)
        layout.addLayout(btn_layout)
        layout.addWidget(self.table)
        
        self.setLayout(layout)

    def get_form_data(self):
        return {
            "nombre": self.name_input.text().strip(),
            "email": self.email_input.text().strip(),
            "celular": self.phone_input.text().strip()
        }

    def set_form_data(self, nombre, email, celular):
        self.name_input.setText(nombre)
        self.email_input.setText(email)
        self.phone_input.setText(celular)

    def clear_form(self):
        self.name_input.clear()
        self.email_input.clear()
        self.phone_input.clear()
        self.update_btn.setEnabled(False)
        self.delete_btn.setEnabled(False)
        self.add_btn.setEnabled(True)

    def show_error(self, message):
        QMessageBox.critical(self, "Error", message)

    def show_info(self, message):
        QMessageBox.information(self, "Información", message)