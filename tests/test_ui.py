"""The window, preferences and About dialog through the real widgets.
Needs a display (CI runs pytest under xvfb-run)."""
import os

import pytest

if not (os.environ.get("DISPLAY") or os.environ.get("WAYLAND_DISPLAY")):
    pytest.skip("needs a display", allow_module_level=True)

import gi  # noqa: E402

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
from gi.repository import Adw, GLib, Gtk  # noqa: E402

from phosh_toolkit.testing import run_until  # noqa: E402

from vestigia import secrets, settings  # noqa: E402
from vestigia.account import Account  # noqa: E402
from vestigia.api import recorded  # noqa: E402


@pytest.fixture(autouse=True)
def memory_keyring(monkeypatch):
    monkeypatch.setenv(secrets.MEMORY_ENV, "memory")


def new_account(configured=False, **kwargs):
    account = Account(settings.Store(), secrets.Secrets(),
                      recorded.RecordedHttp(**kwargs))
    if configured:
        account.save("https://dawarich.example.org", recorded.KEY)
    return account


@pytest.fixture(scope="module")
def app():
    """One application for all tests: a second one with the same id can't
    register on the session bus."""
    from vestigia.main import Application
    application = Application()
    application.register(None)
    Adw.init()
    # Under Xvfb the frame clock of an animation (a spinner) is always
    # ready and starves the idle callbacks that deliver worker results
    # (phosh_toolkit.tasks); the real compositor paces frames.
    Gtk.Settings.get_default().props.gtk_enable_animations = False
    yield application


def iterate(times=20):
    ctx = GLib.MainContext.default()
    for _ in range(times):
        while ctx.pending():
            ctx.iteration(False)


def test_setup_page_without_account(app):
    from vestigia.window import Window
    window = Window(app, new_account())
    window.present()
    iterate()
    page = window.nav.get_visible_page()
    assert page.get_tag() == "setup" and page.get_title() == "Connect to Dawarich"
    window.destroy()


def visible_tag(window):
    page = window.nav.get_visible_page()
    return page.get_tag() if page else None


def test_log_in_with_password(app):
    from vestigia.window import Window
    window = Window(app, new_account())
    window.present()
    page = window.nav.get_visible_page()
    page.url_row.set_text("dawarich.example.org")
    page.email_row.set_text("demo@vestigia.test")
    page.password_row.set_text(recorded.PASSWORD)
    page.login_button.emit("clicked")
    run_until(lambda: visible_tag(window) == "history")
    assert window.account.server_url == "https://dawarich.example.org"
    assert window.account.secrets.api_key() == recorded.KEY
    assert window.account.email == "demo@vestigia.test"
    assert "password" not in settings.Store().path.read_text()
    window.destroy()


def test_log_in_with_two_factor(app):
    from vestigia.window import Window
    window = Window(app, new_account(two_factor=True))
    window.present()
    page = window.nav.get_visible_page()
    page.url_row.set_text("https://dawarich.example.org")
    page.email_row.set_text("demo@vestigia.test")
    page.password_row.set_text(recorded.PASSWORD)
    page.login_button.emit("clicked")
    run_until(lambda: visible_tag(window) == "otp")
    otp = window.nav.get_visible_page()
    otp.code_row.set_text("000000")
    otp.button.emit("clicked")
    run_until(lambda: otp.banner.get_revealed())
    otp.code_row.set_text(recorded.OTP)
    otp.button.emit("clicked")
    run_until(lambda: visible_tag(window) == "history")
    window.destroy()


def test_wrong_key_is_shown(app):
    from vestigia.window import Window
    window = Window(app, new_account())
    window.present()
    page = window.nav.get_visible_page()
    page.url_row.set_text("https://dawarich.example.org")
    page.key_row.set_text("not-the-key")
    page.key_button.emit("clicked")
    run_until(lambda: page.banner.get_revealed())
    assert "rejected" in page.banner.get_title()
    assert window.account.secrets.api_key() is None
    window.destroy()


def test_log_out_and_undo(app):
    from vestigia.window import Window
    window = Window(app, new_account(configured=True))
    window.present()
    iterate()
    assert visible_tag(window) == "history"
    window.log_out()
    assert visible_tag(window) == "setup" and not window.account.configured
    window._undo_log_out(("https://dawarich.example.org", recorded.KEY, ""))
    assert visible_tag(window) == "history" and window.account.configured
    window.destroy()


def test_keyring_banner(app):
    from vestigia.window import Window
    window = Window(app, new_account())
    assert not window.keyring_banner.get_revealed()
    window.show_keyring_state(False)
    assert window.keyring_banner.get_revealed()
    window.destroy()


def test_preferences_keep_style(app):
    from vestigia.preferences import PreferencesDialog
    from vestigia.window import Window
    window = Window(app, new_account(configured=True))
    window.present()
    dialog = PreferencesDialog(window)
    dialog.present(window)
    iterate()
    dialog.style_row.set_selected(2)
    iterate()
    assert settings.Store().load().style == "dark"
    dialog.style_row.set_selected(0)
    dialog.close()
    window.destroy()


def test_actions(app):
    for name in ("about", "preferences", "quit", "toggle-tracking",
                 "stop-tracking", "export-gpx", "show-summary"):
        assert app.lookup_action(name) is not None


def test_map_with_location_button(app):
    from vestigia.window import Window
    window = Window(app, new_account(configured=True))
    window.present()
    iterate()
    view = window.nav.get_visible_page().map
    run_until(lambda: window.nav.get_visible_page().current is not None)
    view.clear()
    button = view.locate_button
    assert button.get_tooltip_text() == "Show My Location"
    # A fix from the portal (none in tests) shows the own marker.
    view._follow = True
    view._on_location(view.location, 37.1686, -3.5962, 5.0)
    assert view.me is not None
    assert abs(view.me.get_latitude() - 37.1686) < 1e-6
    view.add_track([(37.17, -3.56), (37.171, -3.55)])
    assert len(view.tracks) == 2
    view.clear()
    assert view.tracks == []
    window.destroy()


def test_day_view(app):
    from datetime import date, timedelta

    from vestigia.window import Window
    window = Window(app, new_account(configured=True))
    window.present()
    page = window.nav.get_visible_page()
    run_until(lambda: page.current is not None)
    # Today has no recorded data; the next day is not offered.
    assert page.current.empty and not page.next_button.get_sensitive()
    page.go(date.fromisoformat(recorded.DAY))
    run_until(lambda: page.current.day == date.fromisoformat(recorded.DAY))
    assert len(page.map.tracks) == 4          # two tracks, casing and line
    assert page.next_button.get_sensitive()
    page.prev_button.emit("clicked")
    run_until(lambda: page.current.day == date.fromisoformat(recorded.DAY)
              - timedelta(days=1))
    assert page.map.tracks == []
    assert page.date_button.get_label() == "Sat, 20 Apr 2024"
    window.destroy()


def test_sidebar_summary_and_visit(app):
    from datetime import date

    from vestigia.window import Window
    window = Window(app, new_account(configured=True))
    window.set_default_size(360, 720)
    window.present()
    page = window.nav.get_visible_page()
    page.go(date.fromisoformat(recorded.DAY))
    run_until(lambda: page.current and page.current.day == date.fromisoformat(recorded.DAY))
    assert page.sidebar.distance_row.get_subtitle() == "2.1 km"
    assert page.sidebar.moving_row.get_subtitle() == "37 min"
    assert [r.get_title() for r in page.sidebar.visit_rows] == ["Morning stop"]
    page.split.set_show_sidebar(True)
    page.sidebar.visit_rows[0].emit("activated")
    run_until(lambda: visible_tag(window) == "visit")
    # "Show on Map" goes back and centres the map on the visit.
    window.nav.get_visible_page()._on_map()
    assert visible_tag(window) == "history"
    viewport = page.map.viewport
    assert abs(viewport.get_latitude() - 37.168572) < 1e-4
    window.destroy()


def test_saved_days_offline(app):
    from datetime import date

    from vestigia.day import cache, model
    from vestigia.window import Window
    account = new_account(configured=True)
    window = Window(app, account)
    window.present()
    page = window.nav.get_visible_page()
    day = date.fromisoformat(recorded.DAY)
    page.go(day)
    run_until(lambda: page.current and page.current.day == day)
    assert cache.load(account.server_url, day) is not None
    # A final day comes from disk without a request.
    account.http.offline = True
    count = len(account.http.requests)
    page.go(date.today())
    run_until(lambda: page._loading == 0)
    page.go(day)
    assert page.current.day == day and len(account.http.requests) == count + 1
    # Today is fetched again; offline, the saved copy stays with a banner.
    today = model.Day(day=date.today(), tracks=[[(1.0, 2.0), (1.1, 2.1)]])
    cache.save(account.server_url, today)
    page.go(date.today())
    run_until(lambda: page.offline_banner.get_revealed())
    assert page.current.day == date.today() and len(page.map.tracks) == 2
    window.destroy()


def test_states(app):
    from datetime import date

    from vestigia.day import states
    from vestigia.window import Window
    account = new_account(configured=True)
    window = Window(app, account)
    window.present()
    page = window.nav.get_visible_page()
    run_until(lambda: page.current is not None)
    assert page.states.state == states.EMPTY
    assert "today" in page.states.status.get_description()
    # Unreachable without a saved copy, Retry once the network is back.
    account.http.offline = True
    page.go(date.fromisoformat(recorded.DAY))
    run_until(lambda: page.states.state == states.UNREACHABLE)
    assert page.states.retry_button.get_visible()
    account.http.offline = False
    page.states.retry_button.emit("clicked")
    run_until(lambda: page.states.state is None)
    window.destroy()


def test_rejected_key_asks_again(app):
    from vestigia.window import Window
    account = new_account(configured=True)
    account.secrets.store_api_key("an-old-key")
    window = Window(app, account)
    window.present()
    run_until(lambda: visible_tag(window) == "setup")
    page = window.nav.get_visible_page()
    assert page.banner.get_revealed() and "rejected" in page.banner.get_title()
    assert account.server_url and account.secrets.api_key() is None
    window.destroy()


def test_old_server_banner(app):
    from phosh_toolkit.http import Response

    from vestigia.window import Window
    account = new_account(configured=True)
    real = account.http.request

    def request(method, url, headers=None, body=None, **kwargs):
        if url.endswith("/api/v1/health"):
            return Response(200, {"X-Dawarich-Version": "1.17.0"}, b'{"status":"ok"}')
        return real(method, url, headers, body, **kwargs)
    account.http.request = request
    window = Window(app, account)
    window.present()
    page = window.nav.get_visible_page()
    run_until(lambda: page.server_banner.get_revealed())
    assert "1.17.0" in page.server_banner.get_title()
    window.destroy()


def test_show_summary_action(app):
    from vestigia.window import Window
    window = Window(app, new_account(configured=True))
    window.present()
    iterate()
    page = window.history
    before = page.split.get_show_sidebar()
    app.activate_action("show-summary", None)
    assert page.split.get_show_sidebar() != before
    window.destroy()


def test_tracking_preferences(app):
    from vestigia.preferences import PreferencesDialog
    from vestigia.tracker import config
    from vestigia.window import Window
    account = new_account(configured=True)
    window = Window(app, account)
    window.present()
    dialog = PreferencesDialog(window)
    dialog.present(window)
    page = dialog.tracking_page
    # The account's recorded settings arrive (distance_filter 10000).
    run_until(lambda: page.distance_row.get_value() == 10000)
    assert not page.custom.get_visible()
    page.target_row.set_selected(page.target_keys.index(config.TARGET_CUSTOM))
    assert page.custom.get_visible()
    page.url_row.set_text("https://owntracks.example.org/pub")
    page.secret_row.set_text("s3cret")
    page.interval_row.set_value(60)
    saved = config.Store().load()
    assert saved.target_url == "https://owntracks.example.org/pub"
    assert saved.interval == 60 and "s3cret" not in config.Store().path.read_text()
    assert account.secrets.target_secret() == "s3cret"
    run_until(lambda: any(r[0] == "PATCH" for r in account.http.requests), timeout=5)
    dialog.close()
    window.destroy()


def test_record_button_and_live_track(app, monkeypatch, tmp_path):
    from datetime import date, datetime

    from gi.repository import GObject

    from vestigia.tracker import config
    from vestigia.tracker.fix import Fix
    from vestigia.tracking import service
    from vestigia.window import Window

    class FakeSource(GObject.Object):
        __gsignals__ = {"fix": (GObject.SignalFlags.RUN_FIRST, None, (object,)),
                        "failed": (GObject.SignalFlags.RUN_FIRST, None, (str,))}
        last = None

        def __init__(self, *args):
            super().__init__()
            FakeSource.last = self

        def start(self, window):
            pass

        def stop(self):
            pass

    monkeypatch.setattr(service, "Source", FakeSource)
    account = new_account(configured=True)
    store = config.Store()
    store.save(config.TrackingSettings(target_kind=config.TARGET_NONE))
    tracker = service.Tracker(account, store, tmp_path / "points.sqlite")
    window = Window(app, account, tracker=tracker)
    window.present()
    page = window.nav.get_visible_page()
    run_until(lambda: page.current is not None)
    assert page.record_button.get_tooltip_text() == "Start Tracking"
    page.record_button.set_active(True)
    assert tracker.running and page.tracking_banner.get_revealed()
    assert page.record_button.get_tooltip_text() == "Stop Tracking"
    now = datetime.now().timestamp()
    FakeSource.last.emit("fix", Fix(37.1685, -3.5962, 5, now - 120))
    FakeSource.last.emit("fix", Fix(37.1700, -3.5900, 5, now - 60))
    assert page.day == date.today() and len(page.map.live) == 2
    assert page.states.state is None          # no longer "no data"
    page.tracking_banner.emit("button-clicked")
    assert not tracker.running and not page.record_button.get_active()
    window.destroy()


def test_export_gpx(app, tmp_path):
    from datetime import datetime

    from gi.repository import Gio

    from vestigia.tracker.fix import Fix
    from vestigia.tracking import export
    from vestigia.window import Window
    window = Window(app, new_account(configured=True))
    window.present()
    day = datetime.now().date()
    assert export.day_bytes(window.tracker.store, day) is None
    now = datetime.now().timestamp()
    window.tracker.store.add(Fix(37.1685, -3.5962, 5, now))
    data = export.day_bytes(window.tracker.store, day)
    assert b"<trkpt" in data
    target = Gio.File.new_for_path(str(tmp_path / "day.gpx"))
    export.save(window, target, data)
    assert (tmp_path / "day.gpx").read_bytes() == data
    window.destroy()


def open_recorded_visit(app):
    from datetime import date

    from vestigia.window import Window
    account = new_account(configured=True)
    window = Window(app, account)
    window.present()
    page = window.history
    day = date.fromisoformat(recorded.DAY)
    page.go(day)
    run_until(lambda: page.current and page.current.day == day)
    page.sidebar.visit_rows[0].emit("activated")
    run_until(lambda: visible_tag(window) == "visit")
    return window, account, page, window.nav.get_visible_page()


def patches(account):
    return [body["visit"] for method, path, _q, body in account.http.requests
            if method == "PATCH"]


def test_visit_confirm_and_undo(app):
    window, account, page, visit_page = open_recorded_visit(app)
    run_until(lambda: visit_page.place_rows)
    assert visit_page.place_rows[0].get_title() == "Stop"
    visit_page.confirm_button.emit("clicked")
    assert visible_tag(window) == "history"
    run_until(lambda: patches(account))
    assert patches(account) == [{"status": "confirmed"}]
    window.destroy()


def test_visit_decline_is_sent_after_the_toast(app):
    window, account, page, visit_page = open_recorded_visit(app)
    visit_page.decline_button.emit("clicked")
    # Hidden at once, nothing sent while Undo is possible.
    assert page.sidebar.visit_rows == [] and patches(account) == []
    window.destroy()


def test_visit_rename_keeps_status(app):
    window, account, page, visit_page = open_recorded_visit(app)
    visit_page.name_row.set_text("Café")
    visit_page.name_row.emit("apply")
    run_until(lambda: patches(account))
    assert patches(account) == [{"name": "Café", "status": "confirmed"}]
    window.destroy()
