"""Preferences: the style (Follow System, Light, Dark)."""
from gi.repository import Adw
from phosh_toolkit.style import style_row


class PreferencesDialog(Adw.PreferencesDialog):
    def __init__(self, window):
        super().__init__(title="Preferences")
        self.window = window
        page = Adw.PreferencesPage(title="General",
                                   icon_name="preferences-system-symbolic")
        appearance = Adw.PreferencesGroup(title="Appearance")
        self.style_row = style_row(window.settings.style, self._on_style)
        appearance.add(self.style_row)
        page.add(appearance)
        self.add(page)

    def _on_style(self, style):
        self.window.settings.style = style
        self.window.save_settings()
