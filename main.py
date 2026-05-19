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
    presenter = MainPresenter(view, db)
    
    view.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()