import os
import flask
import logging
import uuid
import functools

from werkzeug import exceptions as http_exceptions
from pymongo import MongoClient
from io import BytesIO

from authorization import CredentialsResolver, AuthorizationContext


def is_authorized(authorize_methods):
    """
    Декоратор для валидации запросов, принимает список методов,
    которые нужно проверять.
    Если проверки прошли и запрос авторизован, то декоратор
    вызовет коллбек обработки правила с аргументами:
        self - объект App
        ctx - AuthorizationContext
        *args, **kwargs - иные аргументы
    Если метода нет в списке, декоратор пропустит его без проверки.
    """

    def is_authorized_wrapper(f):

        @functools.wraps(f)
        def wrapper(self, *args, **kwargs):
            if flask.request.method not in authorize_methods:
                return f(self, None, *args, **kwargs)

            headers = flask.request.headers

            try:
                credentials = headers["authorization"]
                login, password = credentials.split()

                if not login or not password:
                    raise ValueError

                password_hash_doc = self.db.users.find_one({"login": login})
                password_hash = password_hash_doc["password"]
            except (KeyError, ValueError, TypeError):
                return self.error_response(http_exceptions.Unauthorized)
            except Exception as e:
                logging.error(f"Client registration error\n{str(e)}")
                return self.error_response(http_exceptions.InternalServerError)

            if self.credentials_resolver.match(password_hash, password):
                ctx = AuthorizationContext(flask.request, login, password_hash)
                return f(self, ctx, *args, **kwargs)

            return self.error_response(http_exceptions.Unauthorized)

        return wrapper

    return is_authorized_wrapper


class App(flask.Flask):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.mongo_client = MongoClient(
            os.environ.get("mongodb_host", "localhost"),
            int(os.environ.get("mongodb_port", 27017))
        )
        self.db = self.mongo_client[os.environ.get("mongodb_name", "flask_app_db")]
        self.credentials_resolver = CredentialsResolver()
        self.add_url_rule(
            "/file_storage", "file_storage",
            self._file_storage_handler,
            methods=["GET", "POST"]
        )
        self.add_url_rule(
            "/file_storage/all", "file_storage/all",
            self._file_storage_all_handler,
            methods=["GET"]
        )
        self.add_url_rule(
            "/register",
            "register",
            self._register_handler, methods=["POST"]
        )

    def error_response(self, error_cls):
        return flask.make_response(
            flask.jsonify({"error": error_cls.description, "code": error_cls.code}),
            getattr(error_cls, "http_error_code", error_cls.code)
        )

    def _register_handler(self):
        json = flask.request.get_json()

        try:
            creds = json["credentials"]
            login = creds["login"]
            password = creds["password"]
        except Exception:
            return self.error_response(http_exceptions.BadRequest)

        login_doc = self.db.users.find_one({"login": login})

        if login_doc is not None:
            return self.error_response(http_exceptions.BadRequest)

        self.db.users.insert_one({
            "login": login,
            "password": self.credentials_resolver.encode(password)
        })

        return "Success"

    def get_file_from_storage(self, file_guid, public=True):
        return self.db.files.find_one({
            "_id": file_guid,
            "public": public
        })

    def save_file_into_storage(self, owner_login, filename, file_bytes):
        file_guid = str(uuid.uuid1())

        self.db.files.insert_one({
            "_id": file_guid,
            "owner_login": owner_login,
            "filename": filename,
            "file_bytes": file_bytes,
            "public": True
        })

        return file_guid

    @is_authorized(["POST"])
    def _file_storage_handler(self, ctx):
        if flask.request.method == "GET":
            file_guid = flask.request.args.get("file_guid")

            if file_guid is None:
                return self.error_response(http_exceptions.BadRequest)

            file_doc = self.get_file_from_storage(file_guid)

            if file_doc is None:
                return self.error_response(http_exceptions.BadRequest)

            buffer = BytesIO()
            buffer.write(file_doc["file_bytes"])
            buffer.seek(0)

            return flask.send_file(
                buffer,
                as_attachment=True,
                attachment_filename=file_doc["filename"],
                mimetype="text/csv"
            )
        elif flask.request.method == "POST":
            if "file" not in flask.request.files:
                return self.error_response(http_exceptions.BadRequest)

            file = flask.request.files["file"]
            buffer = BytesIO()
            file.save(buffer)
            buffer.seek(0)
            return flask.jsonify({
                "file_guid": self.save_file_into_storage(ctx.login, file.filename, buffer.read())
            })

    @is_authorized(["GET"])
    def _file_storage_all_handler(self, ctx):
        pass
