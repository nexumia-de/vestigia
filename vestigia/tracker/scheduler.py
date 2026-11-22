"""When to upload: on demand (`kick`), after failures with growing
pauses, and as soon as the network is back (GNetworkMonitor). The run
itself happens in a worker (phosh_toolkit.tasks) with an Uploader that
`make_uploader()` builds there, so the worker has its own database
connection."""
import logging

from gi.repository import Gio, GLib, GObject
from phosh_toolkit import tasks

from vestigia.tracker.backoff import Backoff

log = logging.getLogger("vestigia.tracker")


class Scheduler(GObject.Object):
    """`changed` after every run and state change."""
    __gsignals__ = {"changed": (GObject.SignalFlags.RUN_FIRST, None, ())}

    def __init__(self, make_uploader, monitor=None, backoff=None):
        super().__init__()
        self.make_uploader = make_uploader
        self.monitor = monitor or Gio.NetworkMonitor.get_default()
        self.backoff = backoff or Backoff()
        self.running = False
        self.again = False
        self.waiting_for_network = False
        self.retry_source = 0
        self.last_error = ""
        self.rejected = False
        self.last_result = None
        self._handler = self.monitor.connect("network-changed", self._on_network)

    def close(self):
        if self._handler:
            self.monitor.disconnect(self._handler)
            self._handler = 0
        self._cancel_retry()

    def kick(self):
        """Upload what waits, now if possible."""
        if self.running:
            self.again = True
            return
        if not self.monitor.get_network_available():
            self.waiting_for_network = True
            self.emit("changed")
            return
        self.waiting_for_network = False
        self._cancel_retry()
        self.running = True
        self.again = False
        tasks.run(lambda: self.make_uploader().run(), self._done)

    def _done(self, result, error):
        self.running = False
        self.last_result = result
        error = error or (result.error if result else None)
        if error is None:
            self.backoff.reset()
            self.last_error = ""
            self.rejected = False
            if self.again:
                self.kick()
        elif getattr(result, "rejected", False) or getattr(error, "kind", "") == "auth":
            # Wrong credentials: retrying changes nothing until the user
            # changes the target or the key.
            self.rejected = True
            self.last_error = "The upload target rejected the credentials"
        else:
            self.last_error = str(error)
            delay = self.backoff.next()
            log.info("upload failed (%s), next try in %d s", error, delay)
            self.retry_source = GLib.timeout_add_seconds(delay, self._retry)
        self.emit("changed")

    def _retry(self):
        self.retry_source = 0
        self.kick()
        return GLib.SOURCE_REMOVE

    def _cancel_retry(self):
        if self.retry_source:
            GLib.source_remove(self.retry_source)
            self.retry_source = 0

    def _on_network(self, monitor, available):
        if available and (self.waiting_for_network or self.retry_source):
            self.kick()
