from presenters.clients_presenter import ClientsPresenter
from presenters.quotes_presenter import QuotesPresenter
from presenters.settings_presenter import SettingsPresenter
from presenters.estimator_presenter import EstimatorPresenter
from presenters.business_context import BusinessContext
from models.client_model import ClientModel
from models.quote_model import QuoteModel
from models.role_model import RoleModel
from models.estimate_model import EstimateModel
from models.template_model import TemplateModel
from models.business_model import BusinessModel
from models.annex_model import AnnexModel


class MainPresenter:
    def __init__(self, view, db):
        self.view = view
        self.db = db

        self.client_model = ClientModel(db)
        self.quote_model = QuoteModel(db)
        self.role_model = RoleModel(db)
        self.estimate_model = EstimateModel(db)
        self.template_model = TemplateModel(db)
        self.business_model = BusinessModel(db)
        self.annex_model = AnnexModel(db)

        # Negocio activo compartido por todas las pestañas
        self.context = BusinessContext()
        self.load_business_selector()

        self.clients_presenter = ClientsPresenter(self.view.clients_view, self.client_model, self.context)
        self.quotes_presenter = QuotesPresenter(
            self.view.quotes_view, self.quote_model, self.client_model, self.business_model, self.context,
            self.annex_model,
        )
        self.settings_presenter = SettingsPresenter(
            self.view.settings_view, self.db, self.business_model, self.context, self.annex_model
        )
        self.estimator_presenter = EstimatorPresenter(
            self.view.estimator_view, self.estimate_model, self.role_model,
            self.template_model, self.quote_model, self.client_model,
            self.business_model, self.context
        )

        # Conectar señales para actualizar clientes en cotizaciones cuando hay cambios
        self.clients_presenter.client_changed_signal.connect(self.quotes_presenter.load_clients)
        self.clients_presenter.client_changed_signal.connect(self.estimator_presenter.load_clients)
        self.estimator_presenter.quote_generated_signal.connect(self.on_quote_generated)
        # Si cambian nombre/prefijo del negocio, refrescar selector y listados
        self.settings_presenter.business_changed_signal.connect(self.on_business_data_changed)

        self.view.business_combo.currentIndexChanged.connect(self.on_business_selected)

    def load_business_selector(self):
        self.view.set_businesses(self.business_model.get_all(), self.context.current)
        self.view.apply_business(self.context.current, self.view.business_combo.currentText())

    def on_quote_generated(self, quote_id, open_now):
        self.quotes_presenter.load_quotes()
        if open_now:
            self.view.navigate(0)
            self.quotes_presenter.select_quote(quote_id)

    def on_business_selected(self, _index):
        clave = self.view.business_combo.currentData()
        if clave:
            self.context.set_current(clave)
            self.view.apply_business(clave, self.view.business_combo.currentText())

    def on_business_data_changed(self):
        self.load_business_selector()
        self.quotes_presenter.load_quotes()
        self.estimator_presenter.load_estimates()
