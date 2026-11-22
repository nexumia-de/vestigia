"""The account: server address (settings), API key (keyring) and the
HTTP client every request goes through. No GTK."""
from phosh_toolkit.http import Client

from vestigia import USER_AGENT
from vestigia.api.client import Dawarich


class Account:
    def __init__(self, settings_store, secrets, http=None):
        self.settings_store = settings_store
        self.secrets = secrets
        self.http = http or Client(USER_AGENT)
        self.email = ""

    @property
    def server_url(self):
        return self.settings_store.load().server_url

    @property
    def configured(self):
        return bool(self.server_url and self.secrets.api_key())

    def client(self, server_url=None, api_key=None):
        """A client for the saved account, or for the given values while
        the account is being set up."""
        return Dawarich(self.http, server_url or self.server_url,
                        api_key if api_key is not None else self.secrets.api_key())

    def save(self, server_url, api_key, email=""):
        """Store the account; False if the key could only be kept in
        memory (vestigia/secrets.py)."""
        settings = self.settings_store.load()
        settings.server_url = server_url
        self.settings_store.save(settings)
        self.email = email
        return self.secrets.store_api_key(api_key)

    def log_out(self):
        """Forget the key and the saved days; returns what restore()
        needs for Undo."""
        from vestigia.day import cache
        saved = (self.server_url, self.secrets.api_key(), self.email)
        self.secrets.clear()
        cache.clear()
        self.email = ""
        return saved

    def restore(self, saved):
        server_url, api_key, email = saved
        if server_url and api_key:
            self.save(server_url, api_key, email)
