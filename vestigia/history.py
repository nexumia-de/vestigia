"""The history page once an account is saved: the map, until the day
view (issue 7) fills it."""
from gi.repository import Adw
from phosh_toolkit import tasks

from vestigia import NAME
from vestigia.map.view import MapView


class HistoryPage(Adw.NavigationPage):
    def __init__(self, window):
        super().__init__(title=NAME, tag="history")
        self.window = window
        toolbar = Adw.ToolbarView()
        header = Adw.HeaderBar()
        header.pack_end(window.menu_button())
        toolbar.add_top_bar(header)
        self.map = MapView(window)
        toolbar.set_content(self.map)
        self.set_child(toolbar)
        tasks.run(window.account.client().me, self._on_me)

    def _on_me(self, user, error):
        if error is None:
            self.window.account.email = user.get("email", "")
