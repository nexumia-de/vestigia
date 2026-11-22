"""Day, week and month periods."""
from datetime import date

from vestigia.day import period as p

SUNDAY = date(2024, 4, 21)


def test_of():
    assert p.of(SUNDAY) == p.Period(SUNDAY, SUNDAY, p.DAY)
    assert p.of(SUNDAY, p.WEEK) == p.Period(date(2024, 4, 15), SUNDAY, p.WEEK)
    assert p.of(SUNDAY, p.MONTH) == p.Period(date(2024, 4, 1), date(2024, 4, 30), p.MONTH)
    assert p.of(date(2024, 2, 10), p.MONTH).end == date(2024, 2, 29)


def test_step():
    assert p.step(p.of(SUNDAY), -1).start == date(2024, 4, 20)
    assert p.step(p.of(SUNDAY, p.WEEK), 1).start == date(2024, 4, 22)
    assert p.step(p.of(date(2024, 12, 5), p.MONTH), 1).start == date(2025, 1, 1)
    assert p.step(p.of(date(2024, 1, 5), p.MONTH), -1).start == date(2023, 12, 1)


def test_labels():
    today = date(2026, 11, 22)
    assert p.label(p.of(today), today) == "Today"
    assert p.label(p.of(SUNDAY), today) == "Sun, 21 Apr 2024"
    assert p.label(p.of(SUNDAY, p.WEEK), today) == "15 – 21 Apr 2024"
    assert p.label(p.of(date(2024, 4, 30), p.WEEK), today) == "29 Apr – 5 May 2024"
    assert p.label(p.of(SUNDAY, p.MONTH), today) == "April 2024"
