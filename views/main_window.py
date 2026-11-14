from PyQt6.QtCore import Qt
from PyQt6.QtGui import QIcon, QKeySequence, QShortcut, QAction
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QComboBox, QFrame, QPushButton,
    QStackedWidget, QButtonGroup, QToolButton, QMenu, QApplication,
)

from views.clients_view import ClientsView
from views.quotes_view import QuotesView
from views.settings_view import SettingsView
from views.estimator_view import EstimatorView
from utils.resource_path import resource_path
from utils.icons import icon
from utils import theme

APP_TITLE = "Sistema de Cotizaciones - Ing. Jose Luis Munoz"
SIDEBAR_WIDTH = 220
SIDEBAR_COLLAPSED_WIDTH = 64
AUTO_COLLAPSE_BELOW = 1100  # ancho de ventana en px
NAV_ICON_COLOR = "#E2E8F0"

PAGES = [
    ("Cotizaciones", "quotes"),
    ("Estimador", "calculator"),
    ("Clientes", "users"),
    ("Configuración", "settings"),
]


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle(APP_TITLE)
        self.setWindowIcon(QIcon(resource_path("assets/app_icon.png")))
        self.setMinimumSize(900, 580)
        self._collapsed = False
        self._manual_collapse = None  # None = automático según el ancho

        central = QWidget()
        root = QHBoxLayout(central)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        root.addWidget(self._build_sidebar())

        self.pages = QStackedWidget()
        self.quotes_view = QuotesView()
        self.estimator_view = EstimatorView()
        self.clients_view = ClientsView()
        self.settings_view = SettingsView()
        for page in (self.quotes_view, self.estimator_view, self.clients_view, self.settings_view):
            self.pages.addWidget(page)
        root.addWidget(self.pages, 1)
        self.setCentralWidget(central)

        self.statusBar().showMessage("Listo")
        self._build_shortcuts()
        self.navigate(0)

    # ------------------------------------------------------------ barra lateral
    def _build_sidebar(self):
        self.sidebar = QFrame()
        self.sidebar.setObjectName("sidebar")
        self.sidebar.setFixedWidth(SIDEBAR_WIDTH)
        lay = QVBoxLayout(self.sidebar)
        lay.setContentsMargins(10, 12, 10, 12)
        lay.setSpacing(4)

        top = QHBoxLayout()
        self.toggle_btn = QToolButton()
        self.toggle_btn.setIcon(icon("menu", NAV_ICON_COLOR, 20))
        self.toggle_btn.setToolTip("Contraer / expandir menú")
        self.toggle_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.toggle_btn.clicked.connect(self._on_toggle_clicked)
        top.addWidget(self.toggle_btn)
        self.app_title = QLabel("Cotizaciones")
        self.app_title.setObjectName("appTitle")
        top.addWidget(self.app_title, 1)
        lay.addLayout(top)
        lay.addSpacing(14)

        self.business_label = QLabel("NEGOCIO")
        self.business_label.setObjectName("sectionLabel")
        lay.addWidget(self.business_label)
        self.business_combo = QComboBox()
        self.business_combo.setCursor(Qt.CursorShape.PointingHandCursor)
        lay.addWidget(self.business_combo)
        # Versión contraída: botón con iniciales y menú de negocios
        self.business_badge = QToolButton()
        self.business_badge.setObjectName("businessBadge")
        self.business_badge.setPopupMode(QToolButton.ToolButtonPopupMode.InstantPopup)
        self.business_badge.setFixedSize(44, 36)
        self.business_badge.setMenu(QMenu(self.business_badge))
        self.business_badge.hide()
        lay.addWidget(self.business_badge, 0, Qt.AlignmentFlag.AlignHCenter)
        lay.addSpacing(18)

        self.menu_label = QLabel("MENÚ")
        self.menu_label.setObjectName("sectionLabel")
        lay.addWidget(self.menu_label)

        self.nav_group = QButtonGroup(self)
        self.nav_group.setExclusive(True)
        self.nav_buttons = []
        for i, (text, icon_name) in enumerate(PAGES):
            btn = QPushButton(f"  {text}")
            btn.setIcon(icon(icon_name, NAV_ICON_COLOR, 20))
            btn.setCheckable(True)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.setToolTip(f"{text}  (Ctrl+{i + 1})")
            btn.clicked.connect(lambda _c, idx=i: self.navigate(idx))
            self.nav_group.addButton(btn, i)
            self.nav_buttons.append((btn, text))
            if text == "Configuración":
                lay.addStretch()
            lay.addWidget(btn)
        return self.sidebar

    def set_businesses(self, businesses, current):
        """businesses: [(clave, nombre)]. Llena el combo y el menú de la versión contraída."""
        self.business_combo.blockSignals(True)
        self.business_combo.clear()
        menu = self.business_badge.menu()
        menu.clear()
        for clave, nombre in businesses:
            self.business_combo.addItem(nombre, userData=clave)
            action = QAction(nombre, menu)
            action.triggered.connect(lambda _c, k=clave: self.business_combo.setCurrentIndex(
                self.business_combo.findData(k)))
            menu.addAction(action)
        self.business_combo.setCurrentIndex(max(self.business_combo.findData(current), 0))
        self.business_combo.blockSignals(False)

    def apply_business(self, clave, nombre):
        theme.apply_theme(QApplication.instance(), clave)
        initials = "".join(w[0] for w in nombre.split() if w[:1].isupper())[:2] or nombre[:2].upper()
        self.business_badge.setText(initials)
        self.business_badge.setToolTip(f"Negocio: {nombre}")
        self.setWindowTitle(f"{APP_TITLE}  —  {nombre}")
        self.statusBar().showMessage(f"Trabajando en: {nombre}", 4000)

    def navigate(self, index):
        self.pages.setCurrentIndex(index)
        btn = self.nav_group.button(index)
        if btn:
            btn.setChecked(True)

    # ------------------------------------------------------------- responsive
    def _on_toggle_clicked(self):
        self._manual_collapse = not self._collapsed
        self.set_sidebar_collapsed(self._manual_collapse)

    def set_sidebar_collapsed(self, collapsed):
        if collapsed == self._collapsed:
            return
        self._collapsed = collapsed
        self.sidebar.setFixedWidth(SIDEBAR_COLLAPSED_WIDTH if collapsed else SIDEBAR_WIDTH)
        for w in (self.app_title, self.business_label, self.menu_label, self.business_combo):
            w.setVisible(not collapsed)
        self.business_badge.setVisible(collapsed)
        for btn, text in self.nav_buttons:
            btn.setText("" if collapsed else f"  {text}")

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if self._manual_collapse is None:
            self.set_sidebar_collapsed(self.width() < AUTO_COLLAPSE_BELOW)

    # -------------------------------------------------------------- atajos
    def _build_shortcuts(self):
        for i in range(len(PAGES)):
            QShortcut(QKeySequence(f"Ctrl+{i + 1}"), self, activated=lambda idx=i: self.navigate(idx))
        QShortcut(QKeySequence("Ctrl+N"), self, activated=lambda: self._trigger("new"))
        QShortcut(QKeySequence("Ctrl+S"), self, activated=lambda: self._trigger("save"))
        QShortcut(QKeySequence("Ctrl+F"), self, activated=lambda: self._trigger("search"))

    def _trigger(self, action):
        page = self.pages.currentWidget()
        targets = page.shortcut_targets() if hasattr(page, "shortcut_targets") else {}
        target = targets.get(action)
        if target is None or not target.isEnabled() or not target.isVisible():
            return
        if action == "search":
            target.setFocus()
            target.selectAll()
        else:
            target.click()
