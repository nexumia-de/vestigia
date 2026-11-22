"""Uploads against recorded answers of Dawarich (Overland, OwnTracks) and
of the OwnTracks Recorder."""
from gpx_fixes import fixes
from replay import Replay

from vestigia.api.upload_target import dawarich_target
from vestigia.tracker.backoff import Backoff
from vestigia.tracker.store import Store
from vestigia.tracker.target import BASIC, NONE, OWNTRACKS, Target
from vestigia.tracker.uploader import Uploader

DAWARICH = dawarich_target("https://dawarich.example.org/")
RECORDER = Target(OWNTRACKS, "https://owntracks.example.org/pub", NONE, user="demo")


def filled(tmp_path, count=43):
    store = Store(tmp_path / "points.sqlite")
    for fix in fixes()[:count]:
        store.add(fix)
    return store


def test_dawarich_target():
    assert DAWARICH.url == "https://dawarich.example.org/api/v1/overland/batches"
    assert DAWARICH.headers("key")["Authorization"] == "Bearer key"


def test_overland_batches(tmp_path):
    store = filled(tmp_path)
    http = Replay(lambda *_: "dawarich/overland_batch")
    result = Uploader(store, DAWARICH, http, "key", batch_size=20).run()
    assert result.sent == 43 and result.error is None
    assert [len(body["locations"]) for _m, _u, _h, body in http.requests] == [20, 20, 3]
    first = http.requests[0][3]["locations"][0]
    assert first["geometry"]["coordinates"] == [-3.596212, 37.1685682]
    assert first["properties"]["timestamp"] == "2024-04-21T09:07:31Z"
    assert http.requests[0][2]["Authorization"] == "Bearer key"
    assert "key" not in http.requests[0][1]
    assert store.count_pending(DAWARICH.key) == 0


def test_bad_point_is_parked(tmp_path):
    store = filled(tmp_path, 10)
    bad = fixes()[6]

    def choose(url, headers, body):
        stamps = [f["properties"]["timestamp"] for f in body["locations"]]
        from vestigia.tracker.protocols import iso
        return ("dawarich/overland_batch_bad_timestamp" if iso(bad.timestamp) in stamps
                else "dawarich/overland_batch")
    result = Uploader(store, DAWARICH, Replay(choose), "key", batch_size=10).run()
    assert result.sent == 9 and result.parked == 1 and result.error is None
    assert store.parked(DAWARICH.key)[0][1] == "422"


def test_rejected_key_stops(tmp_path):
    store = filled(tmp_path, 5)
    result = Uploader(store, DAWARICH, Replay(lambda *_: "dawarich/overland_batch_bad_key"),
                      "wrong").run()
    assert result.rejected and result.sent == 0
    assert store.count_pending(DAWARICH.key) == 5


def test_network_error_keeps_points(tmp_path):
    store = filled(tmp_path, 5)
    result = Uploader(store, DAWARICH, Replay(lambda *_: None), "key").run()
    assert result.error is not None and not result.rejected
    assert store.count_pending(DAWARICH.key) == 5


def test_unconfirmed_batch_is_not_marked(tmp_path):
    store = filled(tmp_path, 5)
    # A 2xx without {"result": "ok"}: the OwnTracks answer "[]".
    result = Uploader(store, DAWARICH, Replay(lambda *_: "owntracks/pub_location"),
                      "key").run()
    assert result.error is not None and store.count_pending(DAWARICH.key) == 5


def test_owntracks_recorder(tmp_path):
    store = filled(tmp_path, 3)
    http = Replay(lambda *_: "owntracks/pub_location")
    result = Uploader(store, RECORDER, http, None).run()
    assert result.sent == 3 and len(http.requests) == 3
    method, url, headers, body = http.requests[0]
    assert body["_type"] == "location" and body["tst"] == 1713690451
    assert headers["X-Limit-U"] == "demo" and "Authorization" not in headers


def test_owntracks_to_dawarich_with_bearer(tmp_path):
    store = filled(tmp_path, 2)
    target = Target(OWNTRACKS, "https://dawarich.example.org/api/v1/owntracks/points")
    http = Replay(lambda *_: "dawarich/owntracks_point")
    assert Uploader(store, target, http, "key").run().sent == 2
    assert http.requests[0][2]["Authorization"] == "Bearer key"


def test_basic_auth_header():
    target = Target(OWNTRACKS, "https://x.example.org/pub", BASIC, user="robin")
    assert target.headers("pw")["Authorization"].startswith("Basic ")


def test_backoff():
    b = Backoff(30, 3600)
    assert [b.next() for _ in range(9)] == [30, 60, 120, 240, 480, 960, 1920, 3600, 3600]
    b.reset()
    assert b.next() == 30
