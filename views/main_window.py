from PyQt6.QtWidgets import QMainWindow, QTabWidget

from views.clients_view import ClientsView
from views.quotes_view import QuotesView
from views.settings_view import SettingsView

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Sistema de Cotizaciones - Ing. Jose Luis Munoz")
        self.resize(1100, 800)
        
        self.tabs = QTabWidget()
        self.setCentralWidget(self.tabs)
        
        self.quotes_view = QuotesView()
        self.clients_view = ClientsView()
        self.settings_view = SettingsView()
        
        self.tabs.addTab(self.quotes_view, "Cotizaciones")
        self.tabs.addTab(self.clients_view, "Clientes")
        self.tabs.addTab(self.settings_view, "Configuración")