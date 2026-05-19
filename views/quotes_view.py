from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QTableWidget,
    QTableWidgetItem,
    QPushButton,
    QLineEdit,
    QLabel,
    QMessageBox,
    QComboBox,
    QDateEdit,
    QTextEdit,
    QGroupBox,
    QHeaderView,
    QSplitter,
)
from PyQt6.QtCore import Qt, QDate


class QuotesView(QWidget):
    def __init__(self):
        super().__init__()
        self.init_ui()

    def init_ui(self):
        main_layout = QVBoxLayout()
        splitter = QSplitter(Qt.Orientation.Horizontal)

        # Panel Izquierdo (Formulario)
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)

        # Grupo General
        general_group = QGroupBox("Datos Generales")
        glayout = QVBoxLayout()

        h_layout1 = QHBoxLayout()
        h_layout1.addWidget(QLabel("Cliente:"))
        self.client_combo = QComboBox()
        h_layout1.addWidget(self.client_combo)

        h_layout1.addWidget(QLabel("Fecha:"))
        self.date_edit = QDateEdit()
        self.date_edit.setCalendarPopup(True)
        self.date_edit.setDate(QDate.currentDate())
        h_layout1.addWidget(self.date_edit)
        glayout.addLayout(h_layout1)

        h_layout2 = QHBoxLayout()
        h_layout2.addWidget(QLabel("Tipo:"))
        self.type_combo = QComboBox()
        self.type_combo.addItems(["INGENIERO CIVIL", "DESARROLLADOR DE SOFTWARE"])
        h_layout2.addWidget(self.type_combo)

        h_layout2.addWidget(QLabel("Proyecto:"))
        self.project_input = QLineEdit()
        h_layout2.addWidget(self.project_input)
        glayout.addLayout(h_layout2)

        general_group.setLayout(glayout)
        left_layout.addWidget(general_group)

        # Grupo Items
        items_group = QGroupBox("Detalle de Servicios")
        ilayout = QVBoxLayout()

        self.items_table = QTableWidget(0, 3)
        self.items_table.setHorizontalHeaderLabels(
            ["Servicio", "Descripción", "Precio Total"]
        )
        self.items_table.horizontalHeader().setSectionResizeMode(
            1, QHeaderView.ResizeMode.Stretch
        )
        ilayout.addWidget(self.items_table)

        btn_items_layout = QHBoxLayout()
        self.add_item_btn = QPushButton("Añadir Item")
        self.remove_item_btn = QPushButton("Remover Item")
        btn_items_layout.addWidget(self.add_item_btn)
        btn_items_layout.addWidget(self.remove_item_btn)
        ilayout.addLayout(btn_items_layout)

        self.total_label = QLabel("Gran Total: $0.00")
        self.total_label.setAlignment(Qt.AlignmentFlag.AlignRight)
        self.total_label.setStyleSheet("font-weight: bold; font-size: 14px;")
        ilayout.addWidget(self.total_label)

        items_group.setLayout(ilayout)
        left_layout.addWidget(items_group)

        # Grupo Observaciones
        obs_group = QGroupBox("Observaciones")
        olayout = QVBoxLayout()
        self.observations_edit = QTextEdit()
        self.observations_edit.setAcceptRichText(True)
        self.observations_edit.setPlaceholderText(
            "Ingrese observaciones (soporta viñetas y formato múltiple)"
        )
        olayout.addWidget(self.observations_edit)
        obs_group.setLayout(olayout)
        left_layout.addWidget(obs_group)

        # Botones Principales
        main_btns = QHBoxLayout()
        self.save_btn = QPushButton("Guardar Cotización")
        self.clear_btn = QPushButton("Limpiar")
        self.generate_pdf_btn = QPushButton("Enviar por Correo")
        self.generate_pdf_btn.setEnabled(False)
        self.whatsapp_btn = QPushButton("Enviar por WhatsApp")
        self.whatsapp_btn.setEnabled(False)
        
        main_btns.addWidget(self.save_btn)
        main_btns.addWidget(self.clear_btn)
        main_btns.addWidget(self.generate_pdf_btn)
        main_btns.addWidget(self.whatsapp_btn)
        left_layout.addLayout(main_btns)

        # Panel Derecho (Listado de Cotizaciones)
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)

        self.quotes_table = QTableWidget(0, 5)
        self.quotes_table.setHorizontalHeaderLabels(
            ["ID", "Fecha", "Cliente", "Proyecto", "Tipo"]
        )
        self.quotes_table.horizontalHeader().setSectionResizeMode(
            2, QHeaderView.ResizeMode.Stretch
        )
        self.quotes_table.horizontalHeader().setSectionResizeMode(
            3, QHeaderView.ResizeMode.Stretch
        )
        self.quotes_table.setSelectionBehavior(
            QTableWidget.SelectionBehavior.SelectRows
        )
        self.quotes_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        right_layout.addWidget(self.quotes_table)

        self.delete_quote_btn = QPushButton("Eliminar Cotización Seleccionada")
        self.delete_quote_btn.setEnabled(False)
        right_layout.addWidget(self.delete_quote_btn)

        splitter.addWidget(left_panel)
        splitter.addWidget(right_panel)
        splitter.setSizes([600, 400])

        main_layout.addWidget(splitter)
        self.setLayout(main_layout)

    def show_error(self, message):
        QMessageBox.critical(self, "Error", message)

    def show_info(self, message):
        QMessageBox.information(self, "Información", message)
