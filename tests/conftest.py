import os
import sys

# Permite importar los paquetes de la app (models, utils...) desde los tests
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
