"""The history page once an account is saved. Shows who is connected
until the day view (issue 7) takes its place."""
from gi.repository import Adw
from phosh_toolkit import tasks

from vestigia import APP_ID, NAME


class HistoryPage(Adw.NavigationPage):
    def __init__(self, window):
        super().__init__(title=NAME, tag="history")
        self.window = window
        toolbar = Adw.ToolbarView()
        header = Adw.HeaderBar()
        header.pack_end(window.menu_button())
        toolbar.add_top_bar(header)
        self.status = Adw.StatusPage(icon_name=f"{APP_ID}-symbolic",
                                     title="Connected")
        toolbar.set_content(self.status)
        self.set_child(toolbar)
        tasks.run(window.account.client().me, self._on_me)

    def _on_me(self, user, error):
        if error is None:
            self.window.account.email = user.get("email", "")
            self.status.set_description(self.window.account.email)
