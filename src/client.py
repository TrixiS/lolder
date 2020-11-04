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


# TODO: класс для взаимодействия с сервером


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
            QRegExp("[a-zA-Z]*", False)
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

    def exec(self, *args, **kwargs):
        super().exec(*args, **kwargs)
        return ApiClient(self.login_edit.text(), self.password_edit.text())

    def rejected_event(self):
        sys.exit()

    def accepted_event(self):
        self.close()

    def login_clicked(self):
        self.accept()

    def register_clicked(self):
        self.accept()


class MainWindow(QMainWindow):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        uic.loadUi(str(get_dir(__file__) / "ui/main_window.ui"), self)
        self.api_client = None