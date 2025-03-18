import sys
from PySide6.QtWidgets import QApplication
from gui.main_window import MainWindow
from config.languages import get_text
from gui.controller import Controller

if __name__ == "__main__":
    app = QApplication([])
    window = MainWindow(get_text)
    controller = Controller(window)
    window.show()
    app.exec()