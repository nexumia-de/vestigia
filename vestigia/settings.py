"""Vestigia's own preferences on disk: the style and the server address.
The API key is never stored here (vestigia/secrets.py). No GTK."""
from dataclasses import dataclass

from phosh_toolkit.settings import JsonStore, app_dir

VERSION = 1


@dataclass
class Settings:
    style: str = "system"
    # Base URL of the Dawarich server, e.g. "https://dawarich.example.org";
    # empty until the account is set up.
    server_url: str = ""


def config_dir():
    return app_dir("config", "vestigia")


class Store(JsonStore):
    def __init__(self, path=None):
        super().__init__(path or config_dir() / "settings.json", Settings, VERSION)
