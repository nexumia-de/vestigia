import logging
import os
from pathlib import Path

import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
from gi.repository import Adw, Gdk, Gio, GLib, Gtk  # noqa: E402

from vestigia import (APP_ID, NAME, NIGHTLY, REPO_URL,  # noqa: E402
                      SUPPORT_URL, VERSION_LABEL)

log = logging.getLogger("vestigia")


class Application(Adw.Application):
    def __init__(self):
        super().__init__(application_id=APP_ID,
                         flags=Gio.ApplicationFlags.HANDLES_COMMAND_LINE)
        self.add_main_option("background", 0, GLib.OptionFlags.NONE,
                             GLib.OptionArg.NONE,
                             "Start without a window and resume tracking", None)
        self.settings_store = None
        self.account = None
        self.tracker = None
        # The day the window opens with (demo data: the recorded day).
        self.first_day = None
        for name, callback in (("about", self._on_about),
                               ("preferences", self._on_preferences),
                               ("show-summary", self._on_show_summary),
                               ("toggle-tracking", self._on_toggle_tracking),
                               ("export-gpx", self._on_export_gpx),
                               ("quit", self._on_quit)):
            action = Gio.SimpleAction.new(name, None)
            action.connect("activate", callback)
            self.add_action(action)
        self.set_accels_for_action("app.quit", ["<Control>q"])
        self.set_accels_for_action("app.preferences", ["<Control>comma"])
        self.set_accels_for_action("app.show-summary", ["F9"])
        self.set_accels_for_action("app.toggle-tracking", ["<Control>r"])

    def do_startup(self):
        Adw.Application.do_startup(self)
        display = Gdk.Display.get_default()
        css = Gtk.CssProvider()
        css.load_from_path(str(Path(__file__).with_name("style.css")))
        Gtk.StyleContext.add_provider_for_display(
            display, css, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)
        # The app's symbolic icon, also when run from the source tree.
        icons = Path(__file__).resolve().parent.parent / "data" / "icons"
        if icons.is_dir():
            Gtk.IconTheme.get_for_display(display).add_search_path(str(icons))
        from phosh_toolkit import style

        from vestigia import demo, secrets, settings
        from vestigia.account import Account
        if demo.enabled():
            self.account, self.first_day = demo.account()
            self.settings_store = self.account.settings_store
        else:
            self.settings_store = settings.Store()
            self.account = Account(self.settings_store, secrets.Secrets())
        style.apply(self.settings_store.load().style)
        from vestigia.tracker import config
        from vestigia.tracking.service import Tracker
        self.tracker = Tracker(self.account, config.Store())
        from vestigia.tracking.background import Keeper
        self.keeper = Keeper(self, self.tracker)

    def do_command_line(self, command_line):
        if command_line.get_options_dict().contains("background"):
            # At login: no window; resume tracking if it was on.
            self.resume_tracking(None)
        else:
            self.activate()
        return 0

    def resume_tracking(self, window):
        if self.tracker.settings_store.load().tracking and not self.tracker.running:
            self.tracker.start(window)

    def do_activate(self):
        from vestigia.window import Window
        window = self.props.active_window
        if window is None:
            window = Window(self, self.account, self.first_day, self.tracker)
            if NIGHTLY:
                window.add_css_class("devel")
        window.present()
        self.resume_tracking(window)

    def _window(self):
        return self.props.active_window

    def _on_show_summary(self, *_):
        """Toggle the day's sidebar (F9); an app action so screenshots
        can open it."""
        window = self._window()
        page = getattr(window, "history", None)
        if page is not None and window.nav.get_visible_page() is page:
            page.split.set_show_sidebar(not page.split.get_show_sidebar())

    def _on_toggle_tracking(self, *_):
        """Start or stop tracking (Ctrl+R)."""
        if self.tracker.running:
            self.tracker.stop()
        else:
            self.tracker.start(self._window())

    def _on_export_gpx(self, *_):
        window = self._window()
        if window:
            window.export_gpx()

    def _on_quit(self, *_):
        self.quit()

    def _on_preferences(self, *_):
        window = self._window()
        if window:
            from vestigia.preferences import PreferencesDialog
            PreferencesDialog(window).present(window)

    def _on_about(self, *_):
        dialog = Adw.AboutDialog(
            application_name=NAME,
            application_icon=APP_ID,
            version=VERSION_LABEL,
            developer_name="suitably",
            website=REPO_URL,
            issue_url=f"{REPO_URL}/issues",
            license_type=Gtk.License.AGPL_3_0,
            comments="Your location history from your own Dawarich server. "
                     "Not affiliated with Dawarich.",
        )
        dialog.add_link("Support Development", SUPPORT_URL)
        dialog.present(self._window())


def main(argv):
    # VESTIGIA_DEBUG=1 logs more.
    logging.basicConfig(format="vestigia: %(name)s: %(message)s")
    if os.environ.get("VESTIGIA_DEBUG"):
        logging.getLogger("vestigia").setLevel(logging.DEBUG)
    return Application().run(argv)
