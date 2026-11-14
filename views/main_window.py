from PyQt6.QtWidgets import QMainWindow, QTabWidget, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QComboBox
from PyQt6.QtGui import QIcon

from views.clients_view import ClientsView
from views.quotes_view import QuotesView
from views.settings_view import SettingsView
from views.estimator_view import EstimatorView
from utils.resource_path import resource_path

APP_TITLE = "Sistema de Cotizaciones - Ing. Jose Luis Munoz"

# Color de acento por negocio para distinguir visualmente con cuál se trabaja
BUSINESS_COLORS = {
    "ESTRUCTURAL": "#1A365D",
    "SOFTWARE": "#22543D",
}


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle(APP_TITLE)
        self.setWindowIcon(QIcon(resource_path("assets/app_icon.png")))
        self.resize(1250, 850)

        central = QWidget()
        layout = QVBoxLayout(central)

        # Barra superior: selector de negocio activo
        self.business_bar = QWidget()
        self.business_bar.setObjectName("businessBar")
        self.business_bar.setAutoFillBackground(True)
        bar_layout = QHBoxLayout(self.business_bar)
        bar_layout.setContentsMargins(10, 6, 10, 6)
        label = QLabel("Negocio:")
        label.setStyleSheet("color: white; font-weight: bold;")
        bar_layout.addWidget(label)
        self.business_combo = QComboBox()
        self.business_combo.setMinimumWidth(240)
        bar_layout.addWidget(self.business_combo)
        bar_layout.addStretch()
        layout.addWidget(self.business_bar)

        self.tabs = QTabWidget()
        layout.addWidget(self.tabs)
        self.setCentralWidget(central)

        self.quotes_view = QuotesView()
        self.clients_view = ClientsView()
        self.settings_view = SettingsView()
        self.estimator_view = EstimatorView()

        self.tabs.addTab(self.quotes_view, "Cotizaciones")
        self.tabs.addTab(self.estimator_view, "Estimador")
        self.tabs.addTab(self.clients_view, "Clientes")
        self.tabs.addTab(self.settings_view, "Configuración")

    def apply_business(self, clave, nombre):
        color = BUSINESS_COLORS.get(clave, "#2D3748")
        self.business_bar.setStyleSheet(f"#businessBar {{ background-color: {color}; border-radius: 4px; }}")
        self.setWindowTitle(f"{APP_TITLE}  —  {nombre}")
