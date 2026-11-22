"""A day from the recorded answers: tracks, the points fallback,
summary and visits."""
from datetime import date, timedelta, timezone

from vestigia.api import recorded
from vestigia.api.client import Dawarich
from vestigia.day import model

DAY = date.fromisoformat(recorded.DAY)


def client():
    return Dawarich(recorded.RecordedHttp(), "https://dawarich.example.org",
                    recorded.KEY)


def test_day_range_in_local_time():
    start, end = model.day_range(DAY, timezone(timedelta(hours=2)))
    assert start == "2024-04-21T00:00:00+02:00"
    assert end == "2024-04-21T23:59:59+02:00"


def test_recorded_day():
    day = model.load(client(), DAY)
    # The walk and the two-minute stop (a 2 m track).
    assert len(day.tracks) == 2 and not day.from_points
    lat, lon = day.tracks[0][0]
    assert 37.1 < lat < 37.2 and -3.6 < lon < -3.5
    assert day.summary["total_distance"] == 2.1
    assert [v.name for v in day.visits] == ["Morning stop"]
    assert day.bounds == (37.168572, -3.596221, 37.17575, -3.54178)
    assert not day.empty


def test_points_when_no_tracks():
    c = client()
    # The answer recorded before the server computed tracks.
    original = c.http.choose

    def choose(method, path, query, body):
        if path == "/api/v1/tracks":
            return "tracks_before_recalculation"
        return original(method, path, query, body)
    c.http.choose = choose
    day = model.load(c, DAY)
    assert day.from_points and len(day.tracks) == 1
    # All three recorded pages, in time order.
    assert len(day.tracks[0]) == 43


def test_empty_day():
    day = model.load(client(), DAY - timedelta(days=1))
    assert day.empty and day.bounds is None and day.positions() == []


def test_multilinestring():
    feature = {"geometry": {"type": "MultiLineString",
                            "coordinates": [[[1, 2], [3, 4]], [[5, 6]]]}}
    assert model.tracks_from_features([feature]) == [[(2.0, 1.0), (4.0, 3.0)]]
