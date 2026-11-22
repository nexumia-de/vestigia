"""The point store: order, marks per target, parking, pruning, restart."""
from gpx_fixes import fixes

from vestigia.tracker.store import Store

A = "overland https://a.example.org/api/v1/overland/batches"
B = "owntracks https://b.example.org/pub"


def store(tmp_path, clock=lambda: 1713700000.0):
    return Store(tmp_path / "points.sqlite", clock)


def test_order_and_limit(tmp_path):
    s = store(tmp_path)
    items = fixes()
    for fix in reversed(items):
        s.add(fix)
    pending = s.pending(A)
    assert [fix for _id, fix in pending] == sorted(items, key=lambda f: f.timestamp)
    assert len(s.pending(A, limit=5)) == 5


def test_marks_per_target(tmp_path):
    s = store(tmp_path)
    ids = [s.add(fix) for fix in fixes()[:10]]
    s.mark_uploaded(A, ids[:4])
    s.mark_uploaded(A, ids[:4])          # twice is harmless
    assert s.count_pending(A) == 6 and s.count_pending(B) == 10
    assert s.last_upload(A) == 1713700000.0 and s.last_upload(B) is None
    s.park(A, ids[5], "422")
    assert s.count_pending(A) == 5 and s.parked(A) == [(ids[5], "422")]


def test_survives_restart(tmp_path):
    s = store(tmp_path)
    first = s.add(fixes()[0])
    s.close()                            # as after a crash: nothing else kept
    again = store(tmp_path)
    assert again.pending(A)[0] == (first, fixes()[0])
    assert (tmp_path / "points.sqlite").stat().st_mode & 0o777 == 0o600


def test_between(tmp_path):
    s = store(tmp_path)
    items = fixes()
    for fix in items:
        s.add(fix)
    start, end = items[16].timestamp, items[29].timestamp
    assert s.between(start, end) == items[16:29]
    assert s.days() == (items[0].timestamp, items[-1].timestamp)


def test_prune_keeps_what_waits(tmp_path):
    items = fixes()
    now = items[-1].timestamp + 31 * 86400
    s = store(tmp_path, clock=lambda: now)
    ids = [s.add(fix) for fix in items]
    s.mark_uploaded(A, ids[:20])
    assert s.prune(30, A) == 20
    assert s.count_pending(A) == 23
    assert s.prune(30) == 23              # GPX only: by age
    assert s.days() is None
