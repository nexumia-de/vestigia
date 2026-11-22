"""Demo data: with VESTIGIA_DEMO_DATA=<directory of recorded answers>
(tests/data/dawarich/) the app talks to vestigia.api.recorded instead of
a server and opens the recorded day. For store screenshots
(release.toml) and trying the app; never touches the real settings or
keyring. No GTK."""
import os
from datetime import date

from vestigia import secrets, settings
from vestigia.account import Account
from vestigia.api import recorded

ENV = "VESTIGIA_DEMO_DATA"
SERVER = "https://demo.invalid"


def enabled():
    return bool(os.environ.get(ENV))


def account():
    """(Account, first day) for demo mode."""
    os.environ[secrets.MEMORY_ENV] = "memory"
    store = settings.Store(settings.app_dir("cache", "vestigia") / "demo" /
                           "settings.json")
    http = recorded.RecordedHttp(os.environ[ENV])
    result = Account(store, secrets.Secrets(), http)
    result.save(SERVER, recorded.KEY, "demo@vestigia.test")
    return result, date.fromisoformat(recorded.DAY)
