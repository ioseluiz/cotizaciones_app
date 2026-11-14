from PyQt6.QtCore import QObject, pyqtSignal

from models.database import get_config_value, set_config_value
from models.seed_data import TIPO_ESTRUCTURAL, TIPOS_ESTIMADO

CONFIG_KEY = "negocio_activo"


class BusinessContext(QObject):
    """Negocio activo (ESTRUCTURAL / SOFTWARE) compartido por todas las pestañas.
    Se recuerda entre sesiones en config.json."""

    changed = pyqtSignal(str)

    def __init__(self):
        super().__init__()
        saved = get_config_value(CONFIG_KEY, TIPO_ESTRUCTURAL)
        self._current = saved if saved in TIPOS_ESTIMADO else TIPO_ESTRUCTURAL

    @property
    def current(self):
        return self._current

    def set_current(self, clave):
        if clave == self._current or clave not in TIPOS_ESTIMADO:
            return
        self._current = clave
        try:
            set_config_value(CONFIG_KEY, clave)
        except Exception:
            pass
        self.changed.emit(clave)
