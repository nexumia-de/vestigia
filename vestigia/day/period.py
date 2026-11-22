"""The shown time span: a day, a week (Monday to Sunday) or a month
(docs/decisions/range-view.md). No GTK."""
import calendar
from dataclasses import dataclass
from datetime import date, timedelta

DAY = "day"
WEEK = "week"
MONTH = "month"
SPANS = (DAY, WEEK, MONTH)


@dataclass(frozen=True)
class Period:
    start: date
    end: date            # inclusive
    span: str = DAY

    @property
    def single_day(self):
        return self.start == self.end

    def contains(self, day):
        return self.start <= day <= self.end


def of(day, span=DAY):
    if span == WEEK:
        start = day - timedelta(days=day.weekday())
        return Period(start, start + timedelta(days=6), WEEK)
    if span == MONTH:
        last = calendar.monthrange(day.year, day.month)[1]
        return Period(day.replace(day=1), day.replace(day=last), MONTH)
    return Period(day, day, DAY)


def step(period, n):
    """The period n spans later (negative: earlier)."""
    if period.span == WEEK:
        return of(period.start + timedelta(weeks=n), WEEK)
    if period.span == MONTH:
        month = period.start.month - 1 + n
        return of(date(period.start.year + month // 12, month % 12 + 1, 1), MONTH)
    return of(period.start + timedelta(days=n), DAY)


def label(period, today=None):
    today = today or date.today()
    if period.span == DAY:
        day = period.start
        if day == today:
            return "Today"
        if day == today - timedelta(days=1):
            return "Yesterday"
        return day.strftime("%a, %-d %b %Y")
    if period.span == WEEK:
        a, b = period.start, period.end
        if a.month == b.month:
            return f"{a.day} – {b.strftime('%-d %b %Y')}"
        if a.year == b.year:
            return f"{a.strftime('%-d %b')} – {b.strftime('%-d %b %Y')}"
        return f"{a.strftime('%-d %b %Y')} – {b.strftime('%-d %b %Y')}"
    return period.start.strftime("%B %Y")
