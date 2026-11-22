"""Account: the address in the settings, the key in the keyring, log out
with undo."""
from vestigia import secrets, settings
from vestigia.account import Account
from vestigia.api import recorded


def account(monkeypatch):
    monkeypatch.setenv(secrets.MEMORY_ENV, "memory")
    return Account(settings.Store(), secrets.Secrets(), recorded.RecordedHttp())


def test_save_and_log_out(monkeypatch):
    a = account(monkeypatch)
    assert not a.configured
    assert a.save("https://dawarich.example.org", recorded.KEY, "demo@vestigia.test")
    assert a.configured and a.client().me()["email"] == "demo@vestigia.test"
    saved = a.log_out()
    assert not a.configured and a.secrets.api_key() is None
    # The address stays for the next login.
    assert a.server_url == "https://dawarich.example.org"
    a.restore(saved)
    assert a.configured
