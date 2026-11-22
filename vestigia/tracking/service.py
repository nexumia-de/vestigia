"""The tracker while the app runs: location source → filter → store →
scheduled uploads, with the settings from tracking.json. Owned by the
application, so it outlives a window (issue 19)."""
import time

from gi.repository import GLib, GObject

from vestigia.api.upload_target import dawarich_target
from vestigia.tracker import config
from vestigia.tracker.filter import Filter
from vestigia.tracker.scheduler import Scheduler
from vestigia.tracker.source import Source
from vestigia.tracker.store import Store, default_path
from vestigia.tracker.uploader import Uploader

# Upload what waits at least this often while tracking (seconds).
UPLOAD_EVERY = 300


class Tracker(GObject.Object):
    """`changed` on every state change; `point(Fix)` for every stored
    point."""
    __gsignals__ = {
        "changed": (GObject.SignalFlags.RUN_FIRST, None, ()),
        "point": (GObject.SignalFlags.RUN_FIRST, None, (object,)),
    }

    def __init__(self, account, settings_store, store_path=None, monitor=None,
                 clock=time.time):
        super().__init__()
        self.account = account
        self.settings_store = settings_store
        self.store_path = store_path or default_path()
        self.clock = clock
        self.store = Store(self.store_path, clock)
        self.settings = settings_store.load()
        self.filter = self._filter()
        self.source = None
        self.window = None
        self.error = ""
        self._timer = 0
        self.scheduler = Scheduler(self._make_uploader, monitor)
        self.scheduler.connect("changed", lambda *_: self.emit("changed"))

    @property
    def running(self):
        return self.source is not None

    def _filter(self):
        s = self.settings
        return Filter(s.distance, s.interval, s.max_accuracy)

    # Where points go

    def target(self):
        """(Target, secret) or (None, None) when points stay here."""
        s = self.settings
        if s.target_kind == config.TARGET_ACCOUNT and self.account.configured:
            return dawarich_target(self.account.server_url), self.account.secrets.api_key()
        if s.target_kind == config.TARGET_CUSTOM:
            target = s.custom_target()
            if target is not None:
                return target, self.account.secrets.target_secret()
        return None, None

    def _make_uploader(self):
        """Runs in the worker: its own database connection."""
        target, secret = self.target()
        return Uploader(Store(self.store_path, self.clock), target, self.account.http,
                        secret, self.settings.batch_size)

    # Start and stop

    def start(self, window):
        if self.running:
            return
        self.window = window
        self.settings = self.settings_store.load()
        self.filter = self._filter()
        self.error = ""
        self.source = Source(self.settings.mode, self.settings.distance, self.clock)
        self.source.connect("fix", self._on_fix)
        self.source.connect("failed", self._on_failed)
        self.source.start(window)
        self._remember(True)
        self._timer = GLib.timeout_add_seconds(UPLOAD_EVERY, self._on_timer)
        target, _secret = self.target()
        self.store.prune(self.settings.keep_days, target.key if target else None)
        self.emit("changed")

    def stop(self):
        if not self.running:
            return
        self.source.stop()
        self.source = None
        if self._timer:
            GLib.source_remove(self._timer)
            self._timer = 0
        self._remember(False)
        self.upload()
        self.emit("changed")

    def _remember(self, tracking):
        settings = self.settings_store.load()
        settings.tracking = tracking
        self.settings_store.save(settings)

    def reload(self):
        """Settings changed: new filter, and a new source if the mode or
        distance changed."""
        old = self.settings
        self.settings = self.settings_store.load()
        self.filter = self._filter()
        if self.running and (old.mode, old.distance) != (self.settings.mode,
                                                         self.settings.distance):
            self.source.stop()
            self.source = None
            if self._timer:
                GLib.source_remove(self._timer)
                self._timer = 0
            self.start(self.window)
        self.emit("changed")

    # Points

    def _on_fix(self, source, fix):
        if not self.filter.accept(fix):
            return
        self.store.add(fix)
        self.emit("point", fix)
        target, _secret = self.target()
        if (target is not None and self.settings.upload_automatically and
                self.store.count_pending(target.key) >= self.settings.batch_size):
            self.upload()
        self.emit("changed")

    def _on_failed(self, source, message):
        self.error = message
        self.source = None
        if self._timer:
            GLib.source_remove(self._timer)
            self._timer = 0
        self._remember(False)
        self.emit("changed")

    def _on_timer(self):
        if self.settings.upload_automatically:
            self.upload()
        return GLib.SOURCE_CONTINUE

    def upload(self):
        target, _secret = self.target()
        if target is not None and self.store.count_pending(target.key):
            self.scheduler.kick()

    # Status

    def pending(self):
        target, _secret = self.target()
        return self.store.count_pending(target.key) if target else 0

    def last_upload(self):
        target, _secret = self.target()
        return self.store.last_upload(target.key) if target else None

    def today(self, start, end):
        return [(f.lat, f.lon) for f in self.store.between(start, end)]
