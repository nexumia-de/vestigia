"""Summary texts."""
from vestigia.day import summary


def test_distance_and_minutes():
    assert summary.distance({"total_distance": 2.1, "distance_unit": "km"}) == "2.1 km"
    assert summary.distance({"total_distance": 3, "distance_unit": "mi"}) == "3 mi"
    assert summary.distance({}) == ""
    assert summary.minutes(37) == "37 min"
    assert summary.minutes(60) == "1 h"
    assert summary.minutes(125) == "2 h 5 min"


def test_span_in_local_time(monkeypatch):
    monkeypatch.setenv("TZ", "Europe/Berlin")
    import time
    time.tzset()
    try:
        assert summary.span("2024-04-21T11:07:31+02:00",
                            "2024-04-21T11:08:55+02:00") == "11:07 – 11:08"
    finally:
        monkeypatch.delenv("TZ")
        time.tzset()
