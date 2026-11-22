"""Demo mode answers from the recordings and leaves the real settings
and keyring alone."""
from vestigia import demo, settings
from vestigia.api import recorded


def test_demo_account(monkeypatch):
    monkeypatch.setenv(demo.ENV, str(recorded.DATA))
    monkeypatch.delenv("VESTIGIA_KEYRING", raising=False)
    account, day = demo.account()
    assert account.configured and day.isoformat() == recorded.DAY
    assert account.client().me()["email"] == "demo@vestigia.test"
    # The real settings file is untouched.
    assert not settings.Store().path.exists()
    assert "demo" in str(account.settings_store.path)
