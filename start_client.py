import sys

from PyQt5.QtWidgets import QApplication
from src.client import MainWindow, LoginDialog

app = QApplication(sys.argv)
login_dialog = LoginDialog()
window = MainWindow()
window.show()
api_client = login_dialog.exec()
window.api_client = api_client
sys.exit(app.exec())
