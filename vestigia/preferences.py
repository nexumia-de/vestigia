"""Preferences: the account (who is connected, log out), the style
(Follow System, Light, Dark) and the tracking settings."""
from gi.repository import Adw, Gtk
from phosh_toolkit.style import style_row


class PreferencesDialog(Adw.PreferencesDialog):
    def __init__(self, window):
        super().__init__(title="Preferences")
        self.window = window
        page = Adw.PreferencesPage(title="General",
                                   icon_name="preferences-system-symbolic")
        page.add(self._account_group())
        appearance = Adw.PreferencesGroup(title="Appearance")
        self.style_row = style_row(window.settings.style, self._on_style)
        appearance.add(self.style_row)
        page.add(appearance)
        self.add(page)
        from vestigia.tracking.settings_page import TrackingPage
        self.tracking_page = TrackingPage(window, window.tracking_store)
        self.add(self.tracking_page)

    def _account_group(self):
        account = self.window.account
        group = Adw.PreferencesGroup(title="Account")
        if not account.configured:
            group.set_description("Not connected to a Dawarich server.")
            return group
        self.account_row = Adw.ActionRow(
            title=account.email or "Dawarich account",
            subtitle=account.server_url)
        self.account_row.add_css_class("property")
        group.add(self.account_row)
        # Destructive, so at the end of the row; Undo comes as a toast.
        self.log_out_button = Gtk.Button(label="Log Out",
                                         valign=Gtk.Align.CENTER)
        self.log_out_button.add_css_class("destructive-action")
        self.log_out_button.connect("clicked", self._on_log_out)
        self.account_row.add_suffix(self.log_out_button)
        return group

    def _on_log_out(self, *_):
        self.close()
        self.window.log_out()

    def _on_style(self, style):
        self.window.settings.style = style
        self.window.save_settings()
