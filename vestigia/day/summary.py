"""Text for the day summary and visit times. No GTK."""
from datetime import datetime


def distance(summary):
    value = summary.get("total_distance")
    if value is None:
        return ""
    unit = summary.get("distance_unit") or "km"
    return f"{value:.1f} {unit}" if isinstance(value, float) else f"{value} {unit}"


def minutes(value):
    if value is None:
        return ""
    value = int(value)
    if value < 60:
        return f"{value} min"
    hours, rest = divmod(value, 60)
    return f"{hours} h {rest} min" if rest else f"{hours} h"


def clock(iso):
    """HH:MM of an ISO time in the phone's time zone."""
    try:
        return datetime.fromisoformat(iso).astimezone().strftime("%H:%M")
    except (TypeError, ValueError):
        return ""


def span(start, end):
    a, b = clock(start), clock(end)
    return f"{a} – {b}" if a and b else a or b
