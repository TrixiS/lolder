import os
import requests

# TODO: метод для проверки регистрации

class ApiClient:

    def __init__(self, login, password):
        self.login = login
        self.password = password
        self.base_url = f"http://{os.environ.get('server_address', '127.0.0.1:8000')}/"

    def req(self, http_method, api_method, **kwargs):
        headers = kwargs.pop("headers", {})
        headers["authorization"] = f"{self.login} {self.password}"

        return requests.request(
            http_method,
            self.base_url + api_method,
            headers=headers, **kwargs
        )
