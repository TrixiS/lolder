import flask
import logging
import uuid
import functools

from werkzeug import exceptions as http_exceptions
from pymongo import MongoClient
from io import BytesIO

from utils.authorization import CredentialsResolver, AuthorizationContext


def is_authorized(authorize_methods):
    """
    Декоратор для валидации запросов, принимает список методов,
    которые нужно проверять.
    Если проверки прошли и запрос авторизован, то декоратор
    вызовет коллбек обработки правила с аргументами:
        self - объект App
        ctx - AuthorizationContext
    Если метода нет в списке, декоратор пропустит его без проверки.
    """

    def is_authorized_wrapper(f):

        @functools.wraps(f)
        def wrapper(self, *args, **kwargs):
            if flask.request.method not in authorize_methods:
                return f(self, None, *args, **kwargs)

            headers = flask.request.headers

            try:
                credentials = str(headers["authorization"])
                login, password, *_ = credentials.lower().split()

                if not login or not password:
                    raise ValueError

                user_doc = self.db.users.find_one({"login": login})
                password_hash = user_doc["password"]
            except (KeyError, ValueError, TypeError) as e:
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
            self.config.get("MONGODB_HOST", "localhost"),
            self.config.get("MONGODB_PORT", 27017)
        )
        self.db = self.mongo_client[self.config.get("MONGODB_NAME", "flask_app_db")]
        self.credentials_resolver = CredentialsResolver()
        self.add_url_rule(
            "/file_storage/", "file_storage",
            self._file_storage_handler,
            methods=["GET", "POST"]
        )
        self.add_url_rule(
            "/file_storage/all/", "file_storage/all",
            self._file_storage_all_handler,
            methods=["GET"]
        )
        self.add_url_rule(
            "/register/", "register",
            self._register_handler,
            methods=["POST"]
        )
        self.add_url_rule(
            "/register/check/", "register/check",
            self._register_check_handler,
            methods=["GET"]
        )

    def error_response(self, error_cls):
        return flask.make_response(
            flask.jsonify({"error": error_cls.description, "code": error_cls.code}),
            getattr(error_cls, "http_error_code", error_cls.code)
        )

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

    def _register_handler(self):
        json = flask.request.get_json()

        try:
            creds = json["credentials"]
            login = str(creds["login"])
            password = str(creds["password"])

            if any(s.isspace() for s in password):
                raise ValueError()
        except Exception as e:
            return self.error_response(http_exceptions.BadRequest)

        login_doc = self.db.users.find_one({"login": login})

        if login_doc is not None:
            return self.error_response(http_exceptions.BadRequest)

        self.db.users.insert_one({
            "login": login,
            "password": self.credentials_resolver.encode(password)
        })

        return "Success"

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

        return self.error_response(http_exceptions.InternalServerError)

    @is_authorized(["GET"])
    def _file_storage_all_handler(self, ctx):
        file_docs = self.db.files.find(
            {"owner_login": ctx.login},
            {"filename": 1, "_id": 1}
        )

        files = [{
            "filename": doc["filename"],
            "file_guid": doc["_id"]
        } for doc in file_docs]

        return flask.jsonify({
            "files": files
        })

    @is_authorized(["GET"])
    def _register_check_handler(self, ctx):
        return "Success"
