"""The window: one navigation view (swipe back everywhere) whose root
page is a placeholder until the account setup of M1 exists."""
from gi.repository import Adw, Gio, Gtk

from vestigia import APP_ID, NAME


class Window(Adw.ApplicationWindow):
    def __init__(self, app, settings_store):
        super().__init__(application=app, default_width=1000,
                         default_height=700, title=NAME)
        # Breakpoints need a minimum size (phosh-toolkit adaptive rules).
        self.set_size_request(360, 294)
        self.settings_store = settings_store
        self.settings = settings_store.load()
        self.nav = Adw.NavigationView()
        self.toasts = Adw.ToastOverlay(child=self.nav)
        self.set_content(self.toasts)
        self.nav.replace([self._start_page()])

    def menu_model(self):
        menu = Gio.Menu()
        menu.append("Preferences", "app.preferences")
        menu.append(f"About {NAME}", "app.about")
        return menu

    def _start_page(self):
        page = Adw.NavigationPage(title=NAME, tag="start")
        toolbar = Adw.ToolbarView()
        header = Adw.HeaderBar()
        menu = Gtk.MenuButton(icon_name="open-menu-symbolic", tooltip_text="Main Menu",
                              primary=True, menu_model=self.menu_model())
        menu.update_property([Gtk.AccessibleProperty.LABEL], ["Main Menu"])
        header.pack_end(menu)
        toolbar.add_top_bar(header)
        self.status = Adw.StatusPage(
            icon_name=f"{APP_ID}-symbolic", title="Nothing Here Yet",
            description="Your location history from your own Dawarich server "
                        "will show here. Connecting to a server comes in a "
                        "later version.")
        toolbar.set_content(self.status)
        page.set_child(toolbar)
        return page

    def save_settings(self):
        self.settings_store.save(self.settings)
