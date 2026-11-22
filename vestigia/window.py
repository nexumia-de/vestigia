"""The window: one navigation view (swipe back everywhere). Its root is
the account setup until an account is saved, then the history."""
from gi.repository import Adw, Gio, Gtk

from vestigia import NAME


class Window(Adw.ApplicationWindow):
    def __init__(self, app, account, day=None, tracker=None):
        super().__init__(application=app, default_width=1000,
                         default_height=700, title=NAME)
        # Breakpoints need a minimum size (phosh-toolkit adaptive rules).
        self.set_size_request(360, 294)
        self.account = account
        self.settings_store = account.settings_store
        self.settings = self.settings_store.load()
        if tracker is None:
            from vestigia.tracker import config
            from vestigia.tracking.service import Tracker
            tracker = Tracker(account, config.Store())
        self.tracker = tracker
        self.tracking_store = tracker.settings_store
        self.nav = Adw.NavigationView(vexpand=True)
        # The keyring is locked or missing: the key lives only in memory.
        self.keyring_banner = Adw.Banner(
            title="The API key is kept only until Travel Log closes: "
                  "the keyring is locked or missing")
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        box.append(self.keyring_banner)
        box.append(self.nav)
        self.toasts = Adw.ToastOverlay(child=box)
        self.set_content(self.toasts)
        self.history = None
        if account.configured:
            self.show_history(day)
        else:
            self.show_setup()

    def menu_model(self):
        menu = Gio.Menu()
        menu.append("Statistics", "app.statistics")
        menu.append("Export Day as GPX…", "app.export-gpx")
        menu.append("Preferences", "app.preferences")
        menu.append(f"About {NAME}", "app.about")
        return menu

    def menu_button(self):
        button = Gtk.MenuButton(icon_name="open-menu-symbolic",
                                tooltip_text="Main Menu", primary=True,
                                menu_model=self.menu_model())
        button.update_property([Gtk.AccessibleProperty.LABEL], ["Main Menu"])
        return button

    def show_setup(self, message=""):
        from vestigia.account.setup_page import SetupPage
        self.nav.replace([SetupPage(self, message)])

    def show_history(self, day=None):
        from phosh_toolkit import tasks

        from vestigia.day.page import DayPage
        self.history = DayPage(self, day)
        self.nav.replace([self.history])
        client = self.account.client()
        tasks.run(client.health, self._on_health)
        if not self.account.email:
            tasks.run(client.me, self._on_me)

    def _on_health(self, version, error):
        from vestigia.api.client import TOO_OLD
        if getattr(error, "kind", "") == TOO_OLD:
            self.history.server_banner.set_title(str(error))
            self.history.server_banner.set_revealed(True)

    def _on_me(self, user, error):
        if error is None:
            self.account.email = user.get("email", "")
        elif getattr(error, "kind", "") == "auth":
            self.key_rejected()

    def key_rejected(self):
        """The server no longer accepts the key (deleted or renewed):
        forget it and ask again; the address stays."""
        if self.nav.get_visible_page() and \
                self.nav.get_visible_page().get_tag() == "setup":
            return
        self.account.secrets.clear()
        self.show_setup("The server rejected the API key. Log in again.")

    def connected(self, persistent):
        self.show_keyring_state(persistent)
        self.show_history()

    def log_out(self):
        """Forget the key at once; the toast offers Undo."""
        saved = self.account.log_out()
        self.show_setup()
        toast = Adw.Toast(title="Logged out", button_label="Undo")
        toast.connect("button-clicked", lambda *_: self._undo_log_out(saved))
        self.toasts.add_toast(toast)

    def _undo_log_out(self, saved):
        self.account.restore(saved)
        self.show_history()

    def show_keyring_state(self, persistent):
        self.keyring_banner.set_revealed(not persistent)

    def tracking_settings_changed(self):
        """The tracking settings were edited; a running tracker takes
        them over."""
        self.tracker.reload()

    def show_statistics(self):
        if not self.account.configured:
            return
        from vestigia.stats.page import StatsPage
        self.nav.push(StatsPage(self))

    def export_gpx(self):
        from datetime import date

        from vestigia.tracking.export import export_day
        day = self.history.day if self.history is not None else date.today()
        export_day(self, day)

    def toast(self, title):
        self.toasts.add_toast(Adw.Toast(title=title))

    def toast_with_undo(self, title, undo=None, on_dismissed=None):
        """A toast; with `undo`, an Undo button. `on_dismissed` runs when
        it closes, whether or not Undo was pressed."""
        toast = Adw.Toast(title=title)
        if undo is not None:
            toast.set_button_label("Undo")
            toast.connect("button-clicked", lambda *_: undo())
        if on_dismissed is not None:
            toast.connect("dismissed", lambda *_: on_dismissed())
        self.toasts.add_toast(toast)
        return toast

    def save_settings(self):
        self.settings_store.save(self.settings)
