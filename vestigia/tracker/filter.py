"""Which fixes become points: not worse than the accuracy limit, not at
(0, 0), and either far enough or long enough after the last kept point
(docs/tracking.md, step 2). No GTK."""
from vestigia.tracker.fix import distance_m


class Filter:
    def __init__(self, distance=10, interval=30, max_accuracy=50):
        """distance in metres, interval in seconds, max_accuracy in
        metres (0: no limit)."""
        self.distance = distance
        self.interval = interval
        self.max_accuracy = max_accuracy
        self.last = None

    def accept(self, fix):
        """True if `fix` is kept; it then becomes the reference."""
        if fix.lat == 0 and fix.lon == 0:
            # Every Dawarich ingest path rejects (0, 0); it is never a fix.
            return False
        if not (-90 <= fix.lat <= 90 and -180 <= fix.lon <= 180):
            return False
        if self.max_accuracy and fix.accuracy and fix.accuracy > self.max_accuracy:
            return False
        last = self.last
        if last is not None:
            if fix.timestamp <= last.timestamp:
                return False
            near = distance_m(last, fix) < self.distance
            recent = fix.timestamp - last.timestamp < self.interval
            if near and recent:
                return False
        self.last = fix
        return True

    def reset(self):
        self.last = None
