from presenters.clients_presenter import ClientsPresenter
from presenters.quotes_presenter import QuotesPresenter
from presenters.settings_presenter import SettingsPresenter
from models.client_model import ClientModel
from models.quote_model import QuoteModel

class MainPresenter:
    def __init__(self, view, db):
        self.view = view
        self.db = db
        
        self.client_model = ClientModel(db)
        self.quote_model = QuoteModel(db)
        
        self.clients_presenter = ClientsPresenter(self.view.clients_view, self.client_model)
        self.quotes_presenter = QuotesPresenter(self.view.quotes_view, self.quote_model, self.client_model)
        self.settings_presenter = SettingsPresenter(self.view.settings_view, self.db)
        
        # Conectar señales para actualizar clientes en cotizaciones cuando hay cambios
        self.clients_presenter.client_changed_signal.connect(self.quotes_presenter.load_clients)