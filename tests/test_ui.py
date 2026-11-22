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
    for name in ("about", "preferences", "quit"):
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
