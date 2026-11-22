"""Statistics from the recorded answer, countries and cities from the
API's documented examples (no reverse geocoding on the dev server)."""
import json
from pathlib import Path

from vestigia.api import recorded
from vestigia.stats import model

DOCUMENTED = Path(__file__).parent / "data" / "documented"


def documented(name):
    data = json.loads((DOCUMENTED / f"{name}.json").read_text())
    assert data["documented"]["recorded"] is False
    return data["body"]


def test_recorded_stats():
    stats = recorded.RecordedHttp().answer("stats")["body"]
    assert model.totals(stats) == {"distance": 2, "points": 43, "countries": 0,
                                   "cities": 0}
    (year, km, months), = model.years(stats)
    assert (year, km) == (2024, 2) and months[3] == (4, 2) and len(months) == 12


def test_empty_places_recorded():
    http = recorded.RecordedHttp()
    assert model.countries(http.answer("countries_visited")["body"]) == []
    assert model.cities(http.answer("visited_cities")["body"]) == []


def test_documented_places():
    assert model.countries(documented("countries_visited")) == ["Germany"]
    assert model.cities(documented("visited_cities")) == [
        ("France", ["Paris"]), ("Germany", ["Berlin", "Munich"])]
