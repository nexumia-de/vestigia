"""The API key goes to the keyring, never into the settings file."""
import json

from phosh_toolkit.keyring import Keyring

from vestigia import secrets, settings


class LockedKeyring(Keyring):
    """A keyring whose daemon refuses every store, like a locked one."""

    def _secret(self):
        class Secret:
            COLLECTION_DEFAULT = None

            @staticmethod
            def password_store_sync(*args):
                raise RuntimeError("Cannot create an item in a locked collection")

            @staticmethod
            def password_lookup_sync(*args):
                return None

            @staticmethod
            def password_clear_sync(*args):
                return True
        self._schema = object()
        return Secret


def test_store_lookup_clear(monkeypatch):
    monkeypatch.setenv(secrets.MEMORY_ENV, "memory")
    store = secrets.Secrets()
    assert store.api_key() is None
    assert store.store_api_key("k" * 64)
    assert store.api_key() == "k" * 64
    store.clear()
    assert store.api_key() is None


def test_locked_keyring_is_reported(monkeypatch):
    monkeypatch.delenv(secrets.MEMORY_ENV, raising=False)
    store = secrets.Secrets(LockedKeyring("test", {}))
    assert store.store_api_key("secret") is False
    assert store.persistent is False
    # Still usable for this session.
    assert store.api_key() == "secret"


def test_settings_file_holds_no_key(tmp_path):
    path = tmp_path / "settings.json"
    store = settings.Store(path)
    store.save(settings.Settings(server_url="https://dawarich.example.org"))
    data = json.loads(path.read_text())
    assert set(data["account"]) == {"style", "server_url"}
