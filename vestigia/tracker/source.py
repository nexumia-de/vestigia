"""Fixes from the location portal through phosh_toolkit.location, with
the time of arrival. Precise mode asks for EXACT accuracy (GNSS);
significant mode for street level and larger moves, which saves power
(docs/tracking.md)."""
import time

import gi

gi.require_version("Xdp", "1.0")
from gi.repository import GObject, Xdp  # noqa: E402
from phosh_toolkit.location import Location  # noqa: E402

from vestigia.tracker.fix import Fix  # noqa: E402

PRECISE = "precise"
SIGNIFICANT = "significant"
# Significant mode: the portal reports a move only from this distance.
SIGNIFICANT_DISTANCE_M = 100


class Source(GObject.Object):
    """`fix(Fix)` for every position; `failed(message)`."""
    __gsignals__ = {
        "fix": (GObject.SignalFlags.RUN_FIRST, None, (object,)),
        "failed": (GObject.SignalFlags.RUN_FIRST, None, (str,)),
    }

    def __init__(self, mode=PRECISE, distance=10, clock=time.time):
        super().__init__()
        self.clock = clock
        if mode == SIGNIFICANT:
            self.location = Location(max(distance, SIGNIFICANT_DISTANCE_M),
                                     Xdp.LocationAccuracy.STREET)
        else:
            # The portal's own threshold stays below the filter's.
            self.location = Location(0)
        self.location.connect("changed", self._on_changed)
        self.location.connect("failed", lambda _l, m: self.emit("failed", m))

    @property
    def running(self):
        return self.location.running

    def start(self, window):
        self.location.start(window)

    def stop(self):
        self.location.stop()

    def _on_changed(self, location, lat, lon, accuracy):
        self.emit("fix", Fix(lat, lon, accuracy, self.clock()))
