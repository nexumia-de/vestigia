"""The window, preferences and About dialog through the real widgets.
Needs a display (CI runs pytest under xvfb-run)."""
import os

import pytest

if not (os.environ.get("DISPLAY") or os.environ.get("WAYLAND_DISPLAY")):
    pytest.skip("needs a display", allow_module_level=True)

import gi  # noqa: E402

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
from gi.repository import Adw, GLib  # noqa: E402

from vestigia import APP_ID, NAME, settings  # noqa: E402


@pytest.fixture(scope="module")
def app():
    """One application for all tests: a second one with the same id can't
    register on the session bus."""
    from vestigia.main import Application
    application = Application()
    application.register(None)
    Adw.init()
    yield application


def iterate(times=20):
    ctx = GLib.MainContext.default()
    for _ in range(times):
        while ctx.pending():
            ctx.iteration(False)


def test_start_page(app):
    from vestigia.window import Window
    window = Window(app, settings.Store())
    window.present()
    iterate()
    page = window.nav.get_visible_page()
    assert page.get_tag() == "start" and page.get_title() == NAME
    assert window.status.get_icon_name() == f"{APP_ID}-symbolic"
    window.destroy()


def test_keyring_banner(app):
    from vestigia.window import Window
    window = Window(app, settings.Store())
    assert not window.keyring_banner.get_revealed()
    window.show_keyring_state(False)
    assert window.keyring_banner.get_revealed()
    window.destroy()


def test_preferences_keep_style(app):
    from vestigia.preferences import PreferencesDialog
    from vestigia.window import Window
    window = Window(app, settings.Store())
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
