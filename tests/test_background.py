"""Hold and suspend inhibition follow the tracker."""
from gi.repository import GObject

from vestigia.tracker.config import TrackingSettings
from vestigia.tracker.source import Location
from vestigia.tracking.background import Keeper


class FakeApp:
    def __init__(self):
        self.holds = 0
        self.inhibited = []

    def hold(self):
        self.holds += 1

    def release(self):
        self.holds -= 1

    def get_active_window(self):
        return None

    def inhibit(self, window, flags, reason):
        self.inhibited.append(reason)
        return 7

    def uninhibit(self, cookie):
        assert cookie == 7
        self.inhibited.pop()


class FakeTracker(GObject.Object):
    __gsignals__ = {"changed": (GObject.SignalFlags.RUN_FIRST, None, ())}

    def __init__(self, keep_awake=True):
        super().__init__()
        self.running = False
        self.settings = TrackingSettings(keep_awake=keep_awake)

    def set(self, running):
        self.running = running
        self.emit("changed")


def test_hold_and_inhibit_while_tracking():
    app, tracker = FakeApp(), FakeTracker()
    Keeper(app, tracker)
    tracker.set(True)
    tracker.emit("changed")              # repeated changes hold once
    assert app.holds == 1 and app.inhibited == ["Recording your location"]
    tracker.set(False)
    assert app.holds == 0 and app.inhibited == []


def test_no_inhibit_when_off():
    app, tracker = FakeApp(), FakeTracker(keep_awake=False)
    Keeper(app, tracker)
    tracker.set(True)
    assert app.holds == 1 and app.inhibited == []


def test_location_without_window():
    assert Location(0)._parent(None) is None
