from PyQt5.QtWidgets import QMainWindow, QDialog
from PyQt5 import uic

from utils.paths import get_dir


class LoginDialog(QDialog):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)


class MainWindow(QMainWindow):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        uic.loadUi(str(get_dir(__file__) / "ui/main_window.ui"), self)
        self.dialog = LoginDialog(self)
        self.dialog.exec()
