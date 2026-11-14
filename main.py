import sys
from PyQt6.QtWidgets import QApplication
from models.database import Database
from views.main_window import MainWindow
from presenters.main_presenter import MainPresenter
from utils.theme import apply_theme


def fit_to_screen(window, app):
    """Abre la ventana a un tamaño cómodo según la pantalla disponible
    (maximizada en pantallas pequeñas, como laptops de 1366x768)."""
    screen = app.primaryScreen()
    if screen is None:
        window.resize(1280, 800)
        window.show()
        return
    avail = screen.availableGeometry()
    if avail.width() < 1440 or avail.height() < 860:
        window.showMaximized()
        return
    width = min(1500, int(avail.width() * 0.85))
    height = min(950, int(avail.height() * 0.88))
    window.resize(width, height)
    window.move(avail.x() + (avail.width() - width) // 2, avail.y() + (avail.height() - height) // 2)
    window.show()


def main():
    app = QApplication(sys.argv)
    apply_theme(app)

    db = Database()

    view = MainWindow()
    _presenter = MainPresenter(view, db)  # noqa: F841 — kept alive to prevent GC

    fit_to_screen(view, app)
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
