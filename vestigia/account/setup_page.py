"""First-run page: server address, then log in with e-mail and password
(two-factor code on a pushed page) or paste the API key. The form
scrolls for the on-screen keyboard; no field is focused when it opens."""
from gi.repository import Adw, GLib, Gtk
from phosh_toolkit import tasks
from vestigia.account.errors import describe
from vestigia.account.otp_page import OtpPage
from vestigia.api.client import normalize_url


class SetupPage(Adw.NavigationPage):
    def __init__(self, window, message=""):
        super().__init__(title="Connect to Dawarich", tag="setup")
        self.window = window
        self.account = window.account
        toolbar = Adw.ToolbarView()
        header = Adw.HeaderBar()
        header.pack_end(window.menu_button())
        toolbar.add_top_bar(header)
        self.banner = Adw.Banner(title=message, revealed=bool(message))
        toolbar.add_top_bar(self.banner)

        page = Adw.PreferencesPage(
            description="Travel Log shows the location history from your own "
                        "Dawarich server. It is not affiliated with Dawarich.")
        server = Adw.PreferencesGroup(title="Server")
        self.url_row = Adw.EntryRow(title="Server Address",
                                    text=self.account.server_url)
        self.url_row.set_input_purpose(Gtk.InputPurpose.URL)
        server.add(self.url_row)
        page.add(server)

        login = Adw.PreferencesGroup(
            title="Log In", description="With the e-mail address and password "
                                        "of your Dawarich account.")
        self.email_row = Adw.EntryRow(title="E-mail")
        self.email_row.set_input_purpose(Gtk.InputPurpose.EMAIL)
        self.password_row = Adw.PasswordEntryRow(title="Password")
        self.password_row.connect("entry-activated", self._on_login)
        login.add(self.email_row)
        login.add(self.password_row)
        self.login_button = self._button("Log In", self._on_login, True)
        login.add(self.login_button)
        page.add(login)

        key = Adw.PreferencesGroup(
            title="Or Use an API Key",
            description="Copy it from the account page of your Dawarich "
                        "server. It is kept in the keyring.")
        self.key_row = Adw.PasswordEntryRow(title="API Key")
        self.key_row.connect("entry-activated", self._on_key)
        key.add(self.key_row)
        self.key_button = self._button("Use Key", self._on_key, False)
        key.add(self.key_button)
        page.add(key)

        toolbar.set_content(page)
        self.set_child(toolbar)
        # No field focused when the page opens: the on-screen keyboard
        # would cover half of it (phosh-toolkit adaptive rules).
        self.connect("shown", lambda *_: GLib.idle_add(self._unfocus))

    def _unfocus(self):
        self.window.set_focus(None)
        return GLib.SOURCE_REMOVE

    @staticmethod
    def _button(label, callback, suggested):
        button = Gtk.Button(label=label, halign=Gtk.Align.CENTER,
                            margin_top=12)
        button.add_css_class("pill")
        if suggested:
            button.add_css_class("suggested-action")
        button.connect("clicked", callback)
        return button

    def _server(self):
        try:
            return normalize_url(self.url_row.get_text())
        except ValueError as error:
            self.show_error(str(error))
            return None

    def busy(self, busy):
        for widget in (self.login_button, self.key_button, self.url_row,
                       self.email_row, self.password_row, self.key_row):
            widget.set_sensitive(not busy)

    def show_error(self, message):
        self.banner.set_title(message)
        self.banner.set_revealed(True)

    def _on_login(self, *_):
        server = self._server()
        email = self.email_row.get_text().strip()
        password = self.password_row.get_text()
        if not server:
            return
        if not email or not password:
            self.show_error("Enter your e-mail address and password")
            return
        client = self.account.client(server, api_key="")

        def work():
            client.health()
            return client.login(email, password)

        self.busy(True)
        tasks.run(work, lambda login, error: self._logged_in(server, login, error))

    def _logged_in(self, server, login, error):
        self.busy(False)
        if error is not None:
            self.show_error(describe(error))
        elif login.challenge:
            self.window.nav.push(OtpPage(self, server, login.challenge))
        else:
            self.verify(server, login.api_key)

    def _on_key(self, *_):
        server = self._server()
        key = self.key_row.get_text().strip()
        if not server:
            return
        if not key:
            self.show_error("Paste the API key from your account page")
            return
        self.verify(server, key, check_version=True)

    def verify(self, server, key, check_version=False):
        """Check the key with users/me, then save the account."""
        client = self.account.client(server, api_key=key)

        def work():
            if check_version:
                client.health()
            return client.me()

        def done(user, error):
            self.busy(False)
            if error is not None:
                self.show_error(describe(error))
                return
            self.password_row.set_text("")
            self.key_row.set_text("")
            persistent = self.account.save(server, key, user.get("email", ""))
            self.window.connected(persistent)

        self.busy(True)
        tasks.run(work, done)

