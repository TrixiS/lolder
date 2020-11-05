import sys
import clipboard

from PyQt5 import uic
from qtwidgets import PasswordEdit
from PyQt5.QtWidgets import (
    QMainWindow, QDialog,
    QLineEdit, QPushButton,
    QLabel, QAbstractItemView,
    QTableWidgetItem, QFileDialog
)

from PyQt5.QtGui import QRegExpValidator
from PyQt5.QtCore import QRegExp, Qt
from pathlib import Path

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
        self.status_label = QLabel(self)
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
        self.setWindowTitle(constants.MAIN_WINDOW_TITLE)
        self.api_client = None
        self.table_widget.setColumnCount(2)
        self.table_widget.setHorizontalHeaderLabels([constants.FILE_NAME, constants.FILE_GUID])
        self.table_widget.horizontalHeaderItem(0).setTextAlignment(Qt.AlignCenter)
        self.table_widget.horizontalHeaderItem(1).setTextAlignment(Qt.AlignCenter)
        self.table_widget.horizontalHeader().setStretchLastSection(True)
        self.table_widget.setEditTriggers(QAbstractItemView.NoEditTriggers)

        self.download_button.clicked.connect(self.download_clicked)
        self.copy_link_button.clicked.connect(self.copy_link_clicked)
        self.upload_button.clicked.connect(self.upload_clicked)
        self.delete_button.clicked.connect(self.delete_clicked)

    def load_files(self):
        all_files_json = self.api_client.req("GET", "file_storage/all").json()

        for i, file in enumerate(all_files_json["files"]):
            self.table_widget.insertRow(i)
            self.table_widget.setItem(i, 0, QTableWidgetItem(file["filename"]))
            self.table_widget.setItem(i, 1, QTableWidgetItem(file["file_guid"]))

    def get_selected_row(self):
        selected_items = self.table_widget.selectedItems()

        if not selected_items:
            return

        return self.table_widget.row(selected_items[0])

    def get_selected_file(self):
        file_row = self.get_selected_row()

        if file_row is None:
            return None, None

        filename_item = self.table_widget.item(file_row, 0)
        file_guid_item = self.table_widget.item(file_row, 1)
        filename = filename_item.text()
        file_guid = file_guid_item.text()

        return filename, file_guid

    def download_clicked(self):
        filename, file_guid = self.get_selected_file()

        if not (filename and file_guid):
            self.statusBar.showMessage(constants.SELECT_FILE)
            return

        downloads_path = get_dir(__file__) / "../downloads"
        file_path = downloads_path / filename
        request_params = {"file_guid": file_guid}

        try:
            response = self.api_client.req("GET", "file_storage", params=request_params)

            if not downloads_path.exists():
                downloads_path.mkdir()

            with open(file_path.resolve(), "wb") as f:
                f.write(response.content)
        except Exception:
            self.statusBar.showMessage(constants.DOWNLOAD_ERROR)
            return

        self.statusBar.showMessage(constants.DOWNLOAD_SUCCESS.format(
            file_path.name,
            str(file_path.parent.resolve())
        ))

    def copy_link_clicked(self):
        _, file_guid = self.get_selected_file()

        if file_guid is None:
            self.statusBar.showMessage(constants.SELECT_FILE)
            return

        clipboard.copy(self.api_client.base_url + "file_storage" + "?file_guid={}".format(
            file_guid
        ))

        self.statusBar.showMessage(constants.LINK_SAVED)

    def upload_clicked(self):
        filepath, _ = QFileDialog.getOpenFileName(
            self,
            constants.UPLOAD_FILE,
            filter=f"{constants.ALL_FILES} (*.*)"
        )

        if not filepath:
            self.statusBar.showMessage(constants.SELECT_FILE)
            return

        file_path = Path(filepath)

        try:
            file_content = file_path.read_bytes()
            request_files = {"file": (file_path.name, file_content)}
            response = self.api_client.req("POST", "file_storage", files=request_files)

            if not response.ok:
                raise ValueError()

            file_guid = response.json()["file_guid"]
        except Exception:
            self.statusBar.showMessage(constants.UPLOAD_ERROR)
            return

        row_count = self.table_widget.rowCount()
        self.table_widget.insertRow(row_count)
        self.table_widget.setItem(row_count, 0, QTableWidgetItem(file_path.name))
        self.table_widget.setItem(row_count, 1, QTableWidgetItem(file_guid))
        self.statusBar.showMessage(constants.UPLOAD_SUCCESS.format(file_path.name))

    def delete_clicked(self):
        filename, file_guid = self.get_selected_file()

        if not file_guid:
            self.statusBar.showMessage(constants.SELECT_FILE)
            return

        request_json = {"files": [file_guid]}

        try:
            if not self.api_client.req("DELETE", "file_storage", json=request_json).ok:
                raise ValueError()
        except Exception:
            self.statusBar.showMessage(constants.DELETE_ERROR)
            return

        selected_row = self.get_selected_row()
        self.table_widget.removeRow(selected_row)
        self.statusBar.showMessage(constants.DELETE_SUCCESS.format(filename))
