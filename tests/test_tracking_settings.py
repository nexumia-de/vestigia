"""Tracking settings: on disk, and shared with Dawarich's mobile
settings through the recorded answers."""
from phosh_toolkit.testing import run_until

from vestigia import secrets, settings
from vestigia.account import Account
from vestigia.api import mobile_settings, recorded
from vestigia.tracker import config
from vestigia.tracking import sync


def test_round_trip():
    store = config.Store()
    s = store.load()
    assert s.mode == "precise" and s.target_kind == config.TARGET_ACCOUNT
    s.distance = 25
    store.save(s)
    assert config.Store().load().distance == 25


def test_mapping_clamps():
    s = config.TrackingSettings(distance=50000, interval=0, batch_size=5000)
    assert mobile_settings.to_server(s) == {
        "tracking_mode": "precise", "distance_filter": 10000, "time_filter": 1,
        "batch_size": 1000, "upload_automatically": True}


def test_apply_recorded_server_settings():
    server = recorded.RecordedHttp().answer("settings_mobile_get")["body"]["settings"]
    s = config.TrackingSettings()
    assert mobile_settings.apply(server, s)
    assert (s.distance, s.interval, s.batch_size) == (10000, 30, 50)
    assert not mobile_settings.apply(server, s)
    # A new account's empty settings change nothing.
    assert not mobile_settings.apply({}, config.TrackingSettings())


def test_pull(monkeypatch):
    monkeypatch.setenv(secrets.MEMORY_ENV, "memory")
    account = Account(settings.Store(), secrets.Secrets(), recorded.RecordedHttp())
    account.save("https://dawarich.example.org", recorded.KEY)
    store = config.Store()
    results = []
    sync.pull(account, store, lambda changed, error: results.append((changed, error)))
    run_until(lambda: results)
    assert results == [(True, None)] and store.load().distance == 10000


def test_no_pull_when_off(monkeypatch):
    monkeypatch.setenv(secrets.MEMORY_ENV, "memory")
    account = Account(settings.Store(), secrets.Secrets(), recorded.RecordedHttp())
    account.save("https://dawarich.example.org", recorded.KEY)
    store = config.Store()
    store.save(config.TrackingSettings(sync_with_server=False))
    sync.pull(account, store, lambda *_: None)
    assert account.http.requests == []
