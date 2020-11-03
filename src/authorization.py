import hashlib


class CredentialsResolver:

    def __init__(self, algo=hashlib.sha256):
        self.algo = algo

    def encode(self, password):
        return self.algo(password.encode()).hexdigest()

    def match(self, pwd_hash, pwd):
        return self.encode(pwd) == pwd_hash


class AuthorizationContext:

    def __init__(self, request, login, password_hash):
        self.request = request
        self.login = login
        self.password_hash = password_hash
