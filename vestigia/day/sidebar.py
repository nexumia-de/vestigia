"""The day's summary and visits beside the map. Tapping a visit centres
the map on it (and closes the sidebar on the phone)."""
from gi.repository import Adw, GObject, Gtk

from vestigia.day import summary as text


class Sidebar(Adw.Bin):
    __gsignals__ = {
        "visit-activated": (GObject.SignalFlags.RUN_FIRST, None, (object,)),
    }

    def __init__(self):
        super().__init__()
        # The sidebar's own header bar, as in libadwaita's split views.
        toolbar = Adw.ToolbarView()
        toolbar.add_top_bar(Adw.HeaderBar(
            title_widget=Adw.WindowTitle(title="Day Summary")))
        self.page = Adw.PreferencesPage()
        toolbar.set_content(self.page)
        self.set_child(toolbar)
        self.summary_group = Adw.PreferencesGroup(title="Summary")
        self.distance_row = self._row("Distance")
        self.moving_row = self._row("Time Moving")
        self.places_row = self._row("Places Visited")
        for row in (self.distance_row, self.moving_row, self.places_row):
            self.summary_group.add(row)
        self.page.add(self.summary_group)
        self.visits_group = Adw.PreferencesGroup(title="Visits")
        self.page.add(self.visits_group)
        self.visit_rows = []

    @staticmethod
    def _row(title):
        row = Adw.ActionRow(title=title)
        row.add_css_class("property")
        return row

    def show_day(self, day):
        s = day.summary or {}
        self.distance_row.set_subtitle(text.distance(s) or "—")
        self.moving_row.set_subtitle(text.minutes(s.get("time_moving_minutes")) or "—")
        places = s.get("places_visited")
        self.places_row.set_subtitle("—" if places is None else str(places))
        for row in self.visit_rows:
            self.visits_group.remove(row)
        self.visit_rows = []
        for visit in day.visits:
            when = text.span(visit.started_at, visit.ended_at)
            if visit.status == "suggested":
                when = f"Suggested · {when}"
            row = Adw.ActionRow(title=visit.name, activatable=True, subtitle=when)
            row.add_suffix(Gtk.Image(icon_name="go-next-symbolic"))
            row.connect("activated", lambda _r, v=visit: self.emit("visit-activated", v))
            self.visits_group.add(row)
            self.visit_rows.append(row)
        self.visits_group.set_description("" if day.visits else "No visits on this day.")
