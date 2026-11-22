"""Pushed page for the two-factor code after an e-mail login."""
from gi.repository import Adw, Gtk
from phosh_toolkit import tasks

from vestigia.account.errors import describe


class OtpPage(Adw.NavigationPage):
    def __init__(self, setup, server, challenge):
        super().__init__(title="Two-Factor Code", tag="otp")
        self.setup = setup
        self.server = server
        self.challenge = challenge
        toolbar = Adw.ToolbarView()
        toolbar.add_top_bar(Adw.HeaderBar())
        self.banner = Adw.Banner()
        toolbar.add_top_bar(self.banner)
        page = Adw.PreferencesPage()
        group = Adw.PreferencesGroup(
            description="Enter the code from your authenticator app or one of "
                        "your backup codes.")
        self.code_row = Adw.EntryRow(title="Code")
        self.code_row.set_input_purpose(Gtk.InputPurpose.DIGITS)
        self.code_row.connect("entry-activated", self._on_verify)
        group.add(self.code_row)
        self.button = Gtk.Button(label="Verify", halign=Gtk.Align.CENTER,
                                 margin_top=12)
        self.button.add_css_class("pill")
        self.button.add_css_class("suggested-action")
        self.button.connect("clicked", self._on_verify)
        group.add(self.button)
        page.add(group)
        toolbar.set_content(page)
        self.set_child(toolbar)

    def _on_verify(self, *_):
        code = self.code_row.get_text().strip()
        if not code:
            return
        client = self.setup.account.client(self.server, api_key="")
        self.button.set_sensitive(False)
        tasks.run(client.otp, self._done, self.challenge, code)

    def _done(self, login, error):
        self.button.set_sensitive(True)
        if error is not None:
            self.banner.set_title(describe(error))
            self.banner.set_revealed(True)
            return
        self.setup.verify(self.server, login.api_key)
