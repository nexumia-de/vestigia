"""Days with data in a month, for the calendar marks: months from
/api/v1/points/tracked_months, then the month's timeline for its days
(docs/decisions/range-view.md). Blocking, for a worker. No GTK."""
from datetime import date

from vestigia.day import model
from vestigia.day import period as periods


def has_month(months, year, month):
    name = date(year, month, 1).strftime("%b")
    return any(m.get("year") == year and name in (m.get("months") or [])
               for m in months or [])


def days_with_data(client, months, year, month):
    """(tracked months, day numbers with data); `months` is reused when
    known, else fetched."""
    if months is None:
        months = client.tracked_months()
    if not has_month(months, year, month):
        return months, []
    span = periods.of(date(year, month, 1), periods.MONTH)
    start, _ = model.day_range(span.start)
    _, end = model.day_range(span.end)
    return months, [int(d["date"][8:10]) for d in client.timeline(start, end)
                    if d.get("entries")]
