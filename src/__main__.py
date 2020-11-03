import os
from server import App

app = App(__name__)
app.run(
    os.environ.get("app_host", "127.0.0.1"),
    int(os.environ.get("app_port", 8000))
)
