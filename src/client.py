import sys

from PyQt5 import uic
from qtwidgets import PasswordEdit
from PyQt5.QtWidgets import (
    QMainWindow, QDialog,
    QLineEdit, QPushButton,
    QLabel
)

from PyQt5.QtGui import QRegExpValidator
from PyQt5.QtCore import QRegExp

from .utils.paths import get_dir
from .utils import constants
from .api_client import ApiClient


def offset_y(widget1, *, offset=constants.LOGIN_WIDGET_Y_OFFSET, down=True):
    if down:
        return widget1.pos().y() + widget1.height() + offset
    else:
        return widget1.pos().y() - widget1.height() - offset


def offset_x(widget1, *, offset=constants.LOGIN_WIDGET_X_OFFSET, down=True):
    if down:
        return widget1.pos().x() + widget1.width() + offset
    else:
        return widget1.pos().x() - widget1.width() - offset


class LoginDialog(QDialog):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setWindowTitle(constants.LOGIN_DIALOG_TITLE)
        self.setFixedSize(constants.LOGIN_WINDOW_WIDTH, constants.LOGIN_WINDOW_HEIGHT)

        self.login_label = QLabel(constants.LOGIN_LABEL_TEXT, self)
        self.status_label = QLabel("Тектовый текст многобукв", self)
        self.password_label = QLabel(constants.PASSWORD_LABEL_TEXT, self)
        self.login_edit = QLineEdit(self)
        self.password_edit = PasswordEdit(True, self)
        self.login_button = QPushButton(constants.LOGIN_BUTTON_TEXT, self)
        self.register_button = QPushButton(constants.REGISTER_BUTTON_TEXT, self)

        self.login_label.resize(self.login_label.sizeHint())
        self.password_label.resize(self.password_label.sizeHint())
        self.register_button.resize(self.register_button.sizeHint())
        self.login_button.resize(self.register_button.size())

        self.login_edit.setValidator(QRegExpValidator(
            QRegExp("[a-zA-Z0-9_]*", False)
        ))
        self.password_edit.setValidator(QRegExpValidator(
            QRegExp("[^\s]*", False)
        ))

        self.login_edit.move(
            constants.LOGIN_WIDGET_X_OFFSET,
            constants.LOGIN_WIDGET_Y_OFFSET * 2
        )
        self.password_edit.move(
            constants.LOGIN_WIDGET_X_OFFSET,
            offset_y(self.login_edit)
        )
        self.login_button.move(
            constants.LOGIN_WIDGET_X_OFFSET,
            offset_y(self.password_edit)
        )
        self.register_button.move(
            offset_x(self.login_button),
            offset_y(self.password_edit)
        )
        self.status_label.move(
            constants.LOGIN_WIDGET_X_OFFSET,
            offset_y(self.login_button)
        )

        self.login_edit.resize(
            self.register_button.pos().x() * 2,
            constants.LOGIN_EDITS_HEIGHT
        )
        self.password_edit.resize(
            self.login_edit.width(),
            constants.LOGIN_EDITS_HEIGHT
        )
        self.login_label.move(
            constants.LOGIN_WIDGET_X_OFFSET,
            offset_y(self.login_edit, offset=0, down=False)
        )
        self.password_label.move(
            constants.LOGIN_WIDGET_X_OFFSET,
            offset_y(self.password_edit, offset=0, down=False)
        )

        self.accepted.connect(self.accepted_event)
        self.rejected.connect(self.rejected_event)
        self.login_button.clicked.connect(self.login_clicked)
        self.register_button.clicked.connect(self.register_clicked)

        self.api_client = None

    def exec(self, *args, **kwargs):
        super().exec(*args, **kwargs)
        return self.api_client

    def rejected_event(self):
        sys.exit()

    def accepted_event(self):
        self.close()

    def get_creds(self):
        login = self.login_edit.text()
        password = self.password_edit.text()
        self.api_client = ApiClient(login, password)
        return login, password

    def check_creds(self, login, password):
        if login and password:
            return True

        self.label_error(constants.NO_LOGIN_OR_PASSWORD)
        return False

    def label_error(self, message):
        self.status_label.setStyleSheet("color: red")
        self.status_label.setText(message)
        self.status_label.resize(self.status_label.sizeHint())

    def login_clicked(self):
        if not self.check_creds(*self.get_creds()):
            return

        try:
            if not self.api_client.req("GET", "register/check").ok:
                raise ValueError(constants.INCORRECT_CREDS)
        except ValueError as e:
            self.label_error(str(e))
            return
        except Exception as e:
            self.label_error(constants.SERVER_ERROR)
            return

        self.accept()

    def register_clicked(self):
        login, password = self.get_creds()

        if not self.check_creds(login, password):
            return

        request_json = {
            "credentials": {
                "login": login,
                "password": password
            }
        }

        try:
            if not self.api_client.req("POST", "register", json=request_json).ok:
                raise ValueError(constants.ALREADY_REGISTERED)
        except ValueError as e:
            self.label_error(str(e))
            return
        except Exception:
            self.label_error(constants.SERVER_ERROR)
            return

        self.accept()


class MainWindow(QMainWindow):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        uic.loadUi(str(get_dir(__file__) / "ui/main_window.ui"), self)
        self.api_client = None