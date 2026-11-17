"""Vestigia's own preferences on disk. For now only the style; the
account and tracking settings come with M1 and M2. No GTK."""
from dataclasses import dataclass

from phosh_toolkit.settings import JsonStore, app_dir

VERSION = 1


@dataclass
class Settings:
    style: str = "system"


def config_dir():
    return app_dir("config", "vestigia")


class Store(JsonStore):
    def __init__(self, path=None):
        super().__init__(path or config_dir() / "settings.json", Settings, VERSION)
