"""The history page: one day's tracks on the map, the summary and visits
in a sidebar that overlays the map on the phone. Previous/next day and
the date picker sit in a bottom bar within thumb reach (phosh-toolkit
adaptive rule 10); the header keeps title, sidebar toggle and menu. One
navigation view per window, so the sidebar is an AdwOverlaySplitView,
not a nested navigation split view (rule 9)."""
from datetime import date, datetime, timedelta

from gi.repository import Adw, GLib, GObject, Gtk
from phosh_toolkit import tasks, widgets

from vestigia import NAME
from vestigia.day import cache, model
from vestigia.day.sidebar import Sidebar
from vestigia.day.states import StateStack
from vestigia.map.view import MapView
from vestigia.tracking import status


def day_label(day):
    today = date.today()
    if day == today:
        return "Today"
    if day == today - timedelta(days=1):
        return "Yesterday"
    return day.strftime("%a, %-d %b %Y")


class DayPage(Adw.NavigationPage):
    def __init__(self, window, day=None):
        super().__init__(title=NAME, tag="history")
        self.window = window
        self.day = day or date.today()
        self.current = None
        self._loading = 0

        self.toolbar = Adw.ToolbarView()
        header = Adw.HeaderBar()
        self.title = Adw.WindowTitle(title=NAME)
        header.set_title_widget(self.title)
        header.pack_end(window.menu_button())
        self.sidebar_button = Gtk.ToggleButton(icon_name="sidebar-show-symbolic",
                                               tooltip_text="Day Summary")
        self.sidebar_button.update_property([Gtk.AccessibleProperty.LABEL],
                                            ["Day Summary"])
        header.pack_start(self.sidebar_button)
        self.record_button = Gtk.ToggleButton(icon_name="media-record-symbolic")
        self.record_button.connect("toggled", self._on_record)
        header.pack_end(self.record_button)
        self.header = header
        self.toolbar.add_top_bar(header)
        # A saved copy is shown because the server cannot be reached.
        self.offline_banner = Adw.Banner(button_label="Retry")
        self.offline_banner.connect("button-clicked", lambda *_: self.load())
        self.toolbar.add_top_bar(self.offline_banner)
        # What the tracker does, with Stop, while it records.
        self.tracking_banner = Adw.Banner(button_label="Stop")
        self.tracking_banner.connect("button-clicked",
                                     lambda *_: window.tracker.stop())
        self.toolbar.add_top_bar(self.tracking_banner)
        # A server problem that stays (too old for Travel Log).
        self.server_banner = Adw.Banner()
        self.toolbar.add_top_bar(self.server_banner)

        self.map = MapView(window)
        self.overlay = Gtk.Overlay(child=self.map)
        self.spinner = widgets.spinner()
        self.spinner.set_halign(Gtk.Align.CENTER)
        self.spinner.set_valign(Gtk.Align.START)
        self.spinner.set_margin_top(12)
        self.spinner.set_visible(False)
        self.overlay.add_overlay(self.spinner)
        self.states = StateStack(self.overlay)
        self.states.connect("retry", lambda *_: self.load())
        self.toolbar.set_content(self.states)
        self.toolbar.add_bottom_bar(self._day_bar())

        self.sidebar = Sidebar()
        self.sidebar.connect("visit-activated", self._on_visit)
        self.split = Adw.OverlaySplitView(sidebar=self.sidebar,
                                          content=self.toolbar,
                                          show_sidebar=True)
        self.split.bind_property("show-sidebar", self.sidebar_button, "active",
                                 GObject.BindingFlags.BIDIRECTIONAL |
                                 GObject.BindingFlags.SYNC_CREATE)
        # Phone width: the sidebar overlays the map and starts hidden. The
        # bin's minimum stays below the window's 360×294, which includes
        # the window frame.
        self.bin = Adw.BreakpointBin(child=self.split, width_request=300,
                                     height_request=200)
        breakpoint = Adw.Breakpoint.new(Adw.BreakpointCondition.parse(
            "max-width: 600sp"))
        breakpoint.add_setter(self.split, "collapsed", True)
        breakpoint.add_setter(self.split, "show-sidebar", False)
        self.bin.add_breakpoint(breakpoint)
        self.set_child(self.bin)
        tracker = window.tracker
        self._handlers = [tracker.connect("changed", self._on_tracker),
                          tracker.connect("point", self._on_point)]
        self.connect("destroy", self._disconnect)
        self._on_tracker(tracker)
        self.connect("shown", lambda *_: self._fit())
        self.load()

    def _day_bar(self):
        bar = Gtk.CenterBox(margin_start=6, margin_end=6, margin_top=6,
                            margin_bottom=6)
        self.prev_button = self._icon_button("go-previous-symbolic",
                                             "Previous Day", -1)
        self.next_button = self._icon_button("go-next-symbolic", "Next Day", 1)
        self.calendar = Gtk.Calendar()
        self.calendar.connect("day-selected", self._on_calendar)
        popover = Gtk.Popover(child=self.calendar)
        self.date_button = Gtk.MenuButton(popover=popover,
                                          tooltip_text="Choose a Day")
        self.date_button.add_css_class("flat")
        bar.set_start_widget(self.prev_button)
        bar.set_center_widget(self.date_button)
        bar.set_end_widget(self.next_button)
        return bar

    def _icon_button(self, icon, label, step):
        button = Gtk.Button(icon_name=icon, tooltip_text=label)
        button.update_property([Gtk.AccessibleProperty.LABEL], [label])
        button.set_size_request(48, 48)
        button.add_css_class("flat")
        button.connect("clicked", lambda *_: self.go(self.day + timedelta(days=step)))
        return button

    def _on_calendar(self, calendar):
        value = calendar.get_date()
        picked = date(value.get_year(), value.get_month(), value.get_day_of_month())
        self.date_button.get_popover().popdown()
        if picked != self.day:
            self.go(picked)

    def go(self, day):
        self.day = day
        self.load()

    def load(self):
        """Fetch the day in a worker; late answers for another day are
        dropped."""
        day = self.day
        self.date_button.set_label(day_label(day))
        self.title.set_subtitle(day_label(day))
        self.next_button.set_sensitive(day < date.today())
        self.calendar.select_day(GLib.DateTime.new_local(day.year, day.month,
                                                         day.day, 0, 0, 0))
        server = self.window.account.server_url
        saved = cache.load(server, day)
        if saved is not None:
            self.show_day(saved)
            if cache.final(day):
                self.offline_banner.set_revealed(False)
                return
        self._loading += 1
        self.spinner.set_visible(True)
        client = self.window.account.client()
        tasks.run(model.load, lambda result, error: self._loaded(
            day, server, saved, result, error), client, day)

    def _loaded(self, day, server, saved, result, error):
        self._loading -= 1
        if day != self.day:
            return
        self.spinner.set_visible(False)
        if error is not None:
            if getattr(error, "kind", "") == "auth":
                self.window.key_rejected()
            elif saved is not None and getattr(error, "kind", "") == "network":
                self.offline_banner.set_title("Offline: showing the saved copy")
                self.offline_banner.set_revealed(True)
            elif saved is None:
                self.map.clear()
                self.sidebar.show_day(model.Day(day=day))
                self.states.show_error(error)
            else:
                self.show_error(error)
            return
        self.offline_banner.set_revealed(False)
        cache.save(server, result)
        self.show_day(result)

    def show_day(self, result):
        self.current = result
        self.map.clear()
        for track in result.tracks:
            self.map.add_track(track)
        for visit in result.visits:
            self.map.add_marker(visit.lat, visit.lon, "mark-location-symbolic",
                                visit.name)
        self.sidebar.show_day(result)
        if result.empty:
            when = day_label(result.day)
            self.states.show_empty(when.lower() if when in ("Today", "Yesterday")
                                   else f"on {when}")
        else:
            self.states.show_content()
        self._show_live()
        self._fit()

    def _disconnect(self, *_):
        for handler in self._handlers:
            self.window.tracker.disconnect(handler)
        self._handlers = []

    def _on_record(self, button):
        tracker = self.window.tracker
        if button.get_active() and not tracker.running:
            tracker.start(self.window)
        elif not button.get_active() and tracker.running:
            tracker.stop()

    def _on_tracker(self, tracker):
        running = tracker.running
        label = "Stop Tracking" if running else "Start Tracking"
        self.record_button.set_tooltip_text(label)
        self.record_button.update_property([Gtk.AccessibleProperty.LABEL], [label])
        if self.record_button.get_active() != running:
            self.record_button.set_active(running)
        if running:
            self.record_button.add_css_class("vestigia-recording")
        else:
            self.record_button.remove_css_class("vestigia-recording")
        line = status.text(tracker)
        self.tracking_banner.set_title(line)
        self.tracking_banner.set_button_label("Stop" if running else None)
        self.tracking_banner.set_revealed(bool(line) and (running or bool(tracker.error)))
        if self.current is not None:
            self._show_live()

    def _on_point(self, tracker, fix):
        if self.day == date.today():
            self._show_live()

    def _show_live(self):
        if self.day != date.today():
            self.map.set_live([])
            return
        start = datetime.combine(self.day, datetime.min.time()).timestamp()
        live = self.window.tracker.today(start, start + 86400)
        self.map.set_live(live)
        if live and self.current is not None and self.current.empty and \
                not self.map._touched:
            # Nothing from the server yet: follow what this phone records.
            self.map.show(live)
        if self.states.state == "empty" and (self.map.live or
                                             self.window.tracker.running):
            # Recording today: the map, where the live track will grow.
            self.states.show_content()

    def _on_visit(self, sidebar, visit):
        if self.split.get_collapsed():
            self.split.set_show_sidebar(False)
        self.map.center(visit.lat, visit.lon, max(self.map.viewport.get_zoom_level(), 16))

    def show_error(self, error):
        from vestigia.account.errors import describe
        self.window.toast(describe(error))

    def _fit_later(self):
        self._fit()
        return GLib.SOURCE_REMOVE

    def _fit(self):
        if self.current is None:
            return
        box = self.current.bounds
        positions = self.current.positions()
        if box is not None:
            positions = [(box[0], box[1]), (box[2], box[3])]
        if not positions:
            return
        if self.map.get_width() == 0:
            # Not allocated yet: fit once it is.
            GLib.timeout_add(50, self._fit_later)
            return
        self.map.show(positions)
