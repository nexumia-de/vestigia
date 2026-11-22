"""The tracker in the app: fixes in, points stored, uploads to the
account's Overland endpoint (recorded answers), status text."""
import pytest
from gi.repository import GObject
from gpx_fixes import fixes
from phosh_toolkit.testing import run_until

from vestigia import secrets, settings
from vestigia.account import Account
from vestigia.api import recorded
from vestigia.tracker import config
from vestigia.tracking import service, status


class FakeSource(GObject.Object):
    __gsignals__ = {
        "fix": (GObject.SignalFlags.RUN_FIRST, None, (object,)),
        "failed": (GObject.SignalFlags.RUN_FIRST, None, (str,)),
    }
    last = None

    def __init__(self, mode, distance, clock):
        super().__init__()
        self.started = False
        FakeSource.last = self

    def start(self, window):
        self.started = True

    def stop(self):
        self.started = False


class Monitor(GObject.Object):
    __gsignals__ = {"network-changed": (GObject.SignalFlags.RUN_FIRST, None, (bool,))}

    def get_network_available(self):
        return True


@pytest.fixture
def tracker(monkeypatch, tmp_path):
    monkeypatch.setenv(secrets.MEMORY_ENV, "memory")
    monkeypatch.setattr(service, "Source", FakeSource)
    account = Account(settings.Store(), secrets.Secrets(), recorded.RecordedHttp())
    account.save("https://dawarich.example.org", recorded.KEY)
    store = config.Store()
    store.save(config.TrackingSettings(distance=10, interval=30, batch_size=5))
    clock = lambda: fixes()[-1].timestamp + 60  # noqa: E731
    return service.Tracker(account, store, tmp_path / "points.sqlite", Monitor(), clock)


def test_record_and_upload(tracker):
    tracker.start(None)
    assert tracker.running and FakeSource.last.started
    assert config.Store().load().tracking
    for fix in fixes():
        FakeSource.last.emit("fix", fix)
    stored = len(tracker.store.between(0, 2e9))
    assert 10 < stored < 43                     # the filter thinned the stop
    run_until(lambda: tracker.scheduler.last_result is not None and
              not tracker.scheduler.running)
    tracker.stop()
    run_until(lambda: tracker.pending() == 0)
    assert not config.Store().load().tracking
    posts = [r for r in tracker.account.http.requests
             if r[1] == "/api/v1/overland/batches"]
    assert sum(len(body["locations"]) for _m, _p, _q, body in posts) == stored
    assert "uploaded" in status.text(tracker)


def test_points_stay_without_target(tracker):
    s = tracker.settings_store.load()
    s.target_kind = config.TARGET_NONE
    tracker.settings_store.save(s)
    tracker.start(None)
    FakeSource.last.emit("fix", fixes()[0])
    assert tracker.target() == (None, None)
    assert status.text(tracker) == "Recording · points stay on this phone"
    tracker.stop()
    assert tracker.account.http.requests == []


def test_portal_refusal_stops(tracker):
    tracker.start(None)
    FakeSource.last.emit("failed", "Location access denied")
    assert not tracker.running
    assert status.text(tracker) == "Tracking stopped: Location access denied"


def test_reload_restarts_source(tracker):
    tracker.start(None)
    first = FakeSource.last
    s = tracker.settings_store.load()
    s.mode = "significant"
    tracker.settings_store.save(s)
    tracker.reload()
    assert FakeSource.last is not first and FakeSource.last.started
    assert not first.started
    tracker.stop()
