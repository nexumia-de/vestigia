"""The map, or a status page instead of it: a day without data, a server
that cannot be reached, another error (phosh-toolkit design guide:
AdwStatusPage for empty and error states)."""
from gi.repository import Adw, GObject, Gtk

from vestigia.account.errors import describe

EMPTY = "empty"
UNREACHABLE = "unreachable"
ERROR = "error"


class StateStack(Gtk.Stack):
    __gsignals__ = {"retry": (GObject.SignalFlags.RUN_FIRST, None, ())}

    def __init__(self, content):
        super().__init__(transition_type=Gtk.StackTransitionType.CROSSFADE)
        self.add_named(content, "content")
        self.status = Adw.StatusPage(vexpand=True)
        self.retry_button = Gtk.Button(label="Retry", halign=Gtk.Align.CENTER)
        self.retry_button.add_css_class("pill")
        self.retry_button.connect("clicked", lambda *_: self.emit("retry"))
        self.status.set_child(self.retry_button)
        self.add_named(self.status, "status")
        self.state = None

    def show_content(self):
        self.state = None
        self.set_visible_child_name("content")

    def show_empty(self, day_text):
        title = "No Data on This Day" if not day_text.startswith("in ") \
            else "No Data in This Period"
        self._show(EMPTY, "find-location-symbolic", title,
                   f"Nothing was recorded {day_text}.", retry=False)

    def show_error(self, error):
        if getattr(error, "kind", "") == "network":
            self._show(UNREACHABLE, "network-offline-symbolic",
                       "Server Unreachable",
                       "Check the network. Days you have opened before are "
                       "shown without it.", retry=True)
        else:
            self._show(ERROR, "dialog-warning-symbolic", "Day Not Loaded",
                       describe(error), retry=True)

    def _show(self, state, icon, title, description, retry):
        self.state = state
        self.status.set_icon_name(icon)
        self.status.set_title(title)
        self.status.set_description(description)
        self.retry_button.set_visible(retry)
        self.set_visible_child_name("status")
