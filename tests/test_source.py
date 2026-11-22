"""Fixes from the location wrapper (no portal in tests: its signal is
emitted by hand, as the toolkit's own tests do)."""
from vestigia.tracker.source import PRECISE, SIGNIFICANT, Source


def test_fix_with_arrival_time():
    source = Source(PRECISE, clock=lambda: 1713690451.0)
    fixes = []
    source.connect("fix", lambda _s, fix: fixes.append(fix))
    source.location.emit("changed", 37.1685682, -3.596212, 5.0)
    assert fixes[0].lat == 37.1685682 and fixes[0].accuracy == 5.0
    assert fixes[0].timestamp == 1713690451.0


def test_modes():
    from gi.repository import Xdp
    assert Source(PRECISE).location.accuracy == Xdp.LocationAccuracy.EXACT
    significant = Source(SIGNIFICANT, distance=10).location
    assert significant.accuracy == Xdp.LocationAccuracy.STREET
    assert significant.distance_m == 100


def test_failure_is_passed_on():
    source = Source()
    messages = []
    source.connect("failed", lambda _s, m: messages.append(m))
    source.location.emit("failed", "denied")
    assert messages == ["denied"]
