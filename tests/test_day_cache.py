"""Saved days: per server, final days only from disk, cleared on log out."""
from datetime import date, timedelta

from vestigia import secrets, settings
from vestigia.account import Account
from vestigia.api import recorded
from vestigia.api.client import Dawarich
from vestigia.day import cache, model

DAY = date.fromisoformat(recorded.DAY)
A = "https://a.example.org"
B = "https://b.example.org"


def recorded_day():
    client = Dawarich(recorded.RecordedHttp(), A, recorded.KEY)
    return model.load(client, DAY)


def test_round_trip_per_server():
    day = recorded_day()
    cache.save(A, day)
    assert cache.load(A, DAY) == day
    assert cache.load(B, DAY) is None
    assert cache.load(A, DAY + timedelta(days=1)) is None


def test_final_days():
    today = date(2026, 11, 22)
    assert not cache.final(today, today)
    assert not cache.final(today - timedelta(days=1), today)
    assert cache.final(today - timedelta(days=2), today)


def test_files_are_private():
    cache.save(A, recorded_day())
    path = next(cache.root().rglob("*.json"))
    assert path.stat().st_mode & 0o777 == 0o600
    assert A not in str(path)


def test_log_out_clears(monkeypatch):
    monkeypatch.setenv(secrets.MEMORY_ENV, "memory")
    account = Account(settings.Store(), secrets.Secrets(), recorded.RecordedHttp())
    account.save(A, recorded.KEY)
    cache.save(A, recorded_day())
    account.log_out()
    assert cache.load(A, DAY) is None
