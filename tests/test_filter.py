"""The filter on the fixes of a real recording."""
from dataclasses import replace

from gpx_fixes import fixes

from vestigia.tracker.filter import Filter
from vestigia.tracker.fix import Fix, distance_m


def kept(f, items):
    return [fix for fix in items if f.accept(fix)]


def test_recording_has_fixes():
    items = fixes()
    assert len(items) == 43
    assert all(0 < fix.accuracy < 20 for fix in items)


def test_distance():
    a = Fix(52.5, 13.4, 5, 0)
    b = Fix(52.5009, 13.4, 5, 0)
    assert abs(distance_m(a, b) - 100.1) < 0.5


def test_no_filter_keeps_every_fix():
    assert len(kept(Filter(distance=0, interval=0, max_accuracy=0), fixes())) == 43


def test_stop_is_thinned():
    # The first segment is a two-minute stop, fixes every 6 s within a
    # few metres: with 10 m / 30 s only one fix every 30 s remains.
    stop = fixes()[:16]
    result = kept(Filter(distance=10, interval=30), stop)
    assert 3 <= len(result) <= 4
    for a, b in zip(result, result[1:]):
        assert b.timestamp - a.timestamp >= 30


def test_walk_keeps_moves():
    walk = fixes()[16:]
    result = kept(Filter(distance=10, interval=3600), walk)
    for a, b in zip(result, result[1:]):
        assert distance_m(a, b) >= 10
    assert len(result) >= 10


def test_accuracy_limit():
    items = fixes()
    worst = max(fix.accuracy for fix in items)
    f = Filter(distance=0, interval=0, max_accuracy=worst - 0.1)
    assert len(kept(f, items)) < 43


def test_zero_and_time_going_back():
    f = Filter(distance=0, interval=0)
    first = fixes()[0]
    assert not f.accept(replace(first, lat=0.0, lon=0.0))
    assert f.accept(first)
    assert not f.accept(replace(first, timestamp=first.timestamp - 1))
