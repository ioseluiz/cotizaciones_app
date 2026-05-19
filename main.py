import sys
from PyQt6.QtWidgets import QApplication
from models.database import Database
from views.main_window import MainWindow
from presenters.main_presenter import MainPresenter

def main():
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    
    db = Database()
    
    view = MainWindow()
    _presenter = MainPresenter(view, db)  # noqa: F841 — kept alive to prevent GC
    
    view.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()