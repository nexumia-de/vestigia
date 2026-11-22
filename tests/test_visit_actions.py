"""Visit changes and their undo, against the recorded answers."""
from datetime import date

from phosh_toolkit.testing import run_until

from vestigia import secrets, settings
from vestigia.account import Account
from vestigia.api import recorded
from vestigia.day import model
from vestigia.visits.actions import VisitActions


class Window:
    def __init__(self, account):
        self.account = account
        self.toasts = []

    def toast(self, title):
        self.toasts.append((title, None, None))

    def toast_with_undo(self, title, undo=None, on_dismissed=None):
        self.toasts.append((title, undo, on_dismissed))


class Page:
    def __init__(self, day):
        self.day = day
        self.current = None
        self.loads = 0
        self.hidden = []

    def load(self):
        self.loads += 1

    def hide_visit(self, visit):
        self.hidden.append(visit)

    def show_day(self, day):
        self.hidden = []


def prepare(monkeypatch):
    monkeypatch.setenv(secrets.MEMORY_ENV, "memory")
    account = Account(settings.Store(), secrets.Secrets(), recorded.RecordedHttp())
    account.save("https://dawarich.example.org", recorded.KEY)
    day = date.fromisoformat(recorded.DAY)
    visit = model.load(account.client(), day).visits[0]
    window, page = Window(account), Page(day)
    return account, visit, window, page, VisitActions(window, page)


def patches(account):
    return [body["visit"] for method, _p, _q, body in account.http.requests
            if method == "PATCH"]


def test_confirm_then_undo(monkeypatch):
    account, visit, window, page, actions = prepare(monkeypatch)
    assert visit.status == "confirmed" and visit.place_id == 1
    actions.update(visit, "Visit confirmed", {"status": "suggested"}, status="confirmed")
    run_until(lambda: window.toasts)
    title, undo, _ = window.toasts[0]
    assert title == "Visit confirmed" and page.loads == 1
    undo()
    run_until(lambda: len(patches(account)) == 2)
    assert patches(account) == [{"status": "confirmed"}, {"status": "suggested"}]


def test_decline_waits_for_the_toast(monkeypatch):
    account, visit, window, page, actions = prepare(monkeypatch)
    actions.decline(visit)
    assert page.hidden == [visit] and patches(account) == []
    title, undo, dismissed = window.toasts[0]
    undo()
    dismissed()
    assert patches(account) == [] and page.hidden == []
    actions.decline(visit)
    window.toasts[-1][2]()
    run_until(lambda: patches(account))
    assert patches(account) == [{"status": "declined"}]


def test_choose_place(monkeypatch):
    account, visit, window, page, actions = prepare(monkeypatch)
    places = []
    actions.places(visit, lambda result, error: places.extend(result))
    run_until(lambda: places)
    actions.choose_place(visit, places[0]["id"])
    run_until(lambda: patches(account))
    assert patches(account) == [{"place_id": 1, "status": "confirmed"}]
