"""A visit, pushed from the day's sidebar: show it on the map, rename it,
confirm or decline it, choose its place among the server's suggestions.
Decline sits at the end of the page, away from the thumb."""
from gi.repository import Adw, GLib, Gtk

from vestigia.day import summary as text
from vestigia.visits.actions import VisitActions

STATUS = {"suggested": "Suggested", "confirmed": "Confirmed", "declined": "Declined"}


class VisitPage(Adw.NavigationPage):
    def __init__(self, window, day_page, visit):
        super().__init__(title=visit.name, tag="visit")
        self.window = window
        self.day_page = day_page
        self.visit = visit
        self.actions = VisitActions(window, day_page)
        toolbar = Adw.ToolbarView()
        toolbar.add_top_bar(Adw.HeaderBar())
        page = Adw.PreferencesPage()

        about = Adw.PreferencesGroup()
        self.name_row = Adw.EntryRow(title="Name", text=visit.name,
                                     show_apply_button=True)
        self.name_row.connect("apply", self._on_rename)
        about.add(self.name_row)
        time_row = Adw.ActionRow(title="Time", subtitle=text.span(
            visit.started_at, visit.ended_at))
        time_row.add_css_class("property")
        about.add(time_row)
        self.status_row = Adw.ActionRow(title="Status",
                                        subtitle=STATUS.get(visit.status, visit.status))
        self.status_row.add_css_class("property")
        about.add(self.status_row)
        map_row = Adw.ActionRow(title="Show on Map", activatable=True)
        map_row.add_suffix(Gtk.Image(icon_name="mark-location-symbolic"))
        map_row.connect("activated", self._on_map)
        about.add(map_row)
        page.add(about)

        self.places_group = Adw.PreferencesGroup(
            title="Place", description="Places Dawarich suggests for this visit.")
        self.place_rows = []
        page.add(self.places_group)

        buttons = Adw.PreferencesGroup()
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12,
                      halign=Gtk.Align.CENTER)
        self.confirm_button = Gtk.Button(label="Confirm Visit",
                                         visible=visit.status != "confirmed")
        self.confirm_button.add_css_class("pill")
        self.confirm_button.add_css_class("suggested-action")
        self.confirm_button.connect("clicked", self._on_confirm)
        self.decline_button = Gtk.Button(label="Decline Visit")
        self.decline_button.add_css_class("pill")
        self.decline_button.add_css_class("destructive-action")
        self.decline_button.connect("clicked", self._on_decline)
        box.append(self.confirm_button)
        box.append(self.decline_button)
        buttons.add(box)
        page.add(buttons)

        toolbar.set_content(page)
        self.set_child(toolbar)
        # No field focused when the page opens (on-screen keyboard).
        self.connect("shown", lambda *_: GLib.idle_add(self._unfocus))
        self.actions.places(visit, self._on_places)

    def _unfocus(self):
        self.window.set_focus(None)
        return GLib.SOURCE_REMOVE

    def _on_places(self, places, error):
        if error is not None or not places:
            self.places_group.set_description("No suggestions for this visit.")
            return
        group = None
        for place in places:
            row = Adw.ActionRow(title=place.get("name") or "Place", activatable=True,
                                subtitle=", ".join(p for p in (place.get("city"),
                                                               place.get("country")) if p))
            check = Gtk.CheckButton(group=group, can_target=False,
                                    active=place.get("id") == self.visit.place_id)
            group = group or check
            row.add_prefix(check)
            row.connect("activated", self._on_place, place.get("id"))
            self.places_group.add(row)
            self.place_rows.append(row)

    def _back(self):
        self.window.nav.pop()

    def _on_rename(self, row):
        name = row.get_text().strip()
        if name and name != self.visit.name:
            self.actions.rename(self.visit, name)
            self._back()

    def _on_confirm(self, *_):
        self.actions.confirm(self.visit)
        self._back()

    def _on_decline(self, *_):
        self._back()
        self.actions.decline(self.visit)

    def _on_place(self, row, place_id):
        if place_id and place_id != self.visit.place_id:
            self.actions.choose_place(self.visit, place_id)
            self._back()

    def _on_map(self, *_):
        self._back()
        self.day_page.center_on_visit(self.visit)
