"""Upload scheduling: waits for the network, backs off, stops on 401."""
from gi.repository import GObject
from phosh_toolkit.http import AUTH, NETWORK, HttpError
from phosh_toolkit.testing import run_until

from vestigia.tracker.scheduler import Scheduler
from vestigia.tracker.uploader import Result


class Monitor(GObject.Object):
    __gsignals__ = {"network-changed": (GObject.SignalFlags.RUN_FIRST, None, (bool,))}

    def __init__(self, available):
        super().__init__()
        self.available = available

    def get_network_available(self):
        return self.available

    def set(self, available):
        self.available = available
        self.emit("network-changed", available)


class Runs:
    def __init__(self, *results):
        self.results = list(results)
        self.count = 0

    def __call__(self):
        runs = self

        class U:
            def run(self):
                runs.count += 1
                return runs.results.pop(0)
        return U()


def test_waits_for_network():
    runs = Runs(Result(sent=3))
    monitor = Monitor(False)
    s = Scheduler(runs, monitor)
    s.kick()
    assert s.waiting_for_network and runs.count == 0
    monitor.set(True)
    run_until(lambda: s.last_result is not None)
    assert runs.count == 1 and s.last_error == ""


def test_backs_off_then_succeeds():
    runs = Runs(Result(error=HttpError(NETWORK, "timeout")), Result(sent=1))
    s = Scheduler(runs, Monitor(True))
    s.kick()
    run_until(lambda: s.last_result is not None)
    assert s.retry_source and s.last_error == "timeout"
    assert s.backoff.failures == 1
    s.kick()                     # e.g. the next point: tries at once
    run_until(lambda: runs.count == 2 and not s.running)
    assert s.last_error == "" and s.backoff.failures == 0 and not s.retry_source


def test_rejected_stops_retrying():
    runs = Runs(Result(error=HttpError(AUTH, "401", 401)))
    s = Scheduler(runs, Monitor(True))
    s.kick()
    run_until(lambda: s.last_result is not None)
    assert s.rejected and not s.retry_source
