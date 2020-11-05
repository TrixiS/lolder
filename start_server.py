import os
import logging

from src.server import App
from src.utils.paths import get_dir

logging.basicConfig(
    filename=str(get_dir(__file__) / "logs.log"),
    level=logging.ERROR
)

app = App(__name__)
app.run(
    os.environ.get("app_host", "127.0.0.1"),
    int(os.environ.get("app_port", 8000))
)
