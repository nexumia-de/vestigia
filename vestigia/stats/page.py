"""Statistics, pushed from the main menu: totals, distance per month of
a year as level bars with the numbers beside them (no chart that is only
colour), and the countries and cities of that year."""
import calendar

from gi.repository import Adw, Gtk
from phosh_toolkit import tasks, widgets

from vestigia.account.errors import describe
from vestigia.stats import model


def property_row(title, value=""):
    row = Adw.ActionRow(title=title)
    label = Gtk.Label(label=value, css_classes=["numeric", "dim-label"])
    row.add_suffix(label)
    row.value = label
    return row


class StatsPage(Adw.NavigationPage):
    def __init__(self, window):
        super().__init__(title="Statistics", tag="statistics")
        self.window = window
        self.years = []
        toolbar = Adw.ToolbarView()
        toolbar.add_top_bar(Adw.HeaderBar())
        self.stack = Gtk.Stack()
        self.stack.add_named(widgets.loading_page(), "loading")
        self.page = Adw.PreferencesPage()
        self.stack.add_named(self.page, "stats")
        self.error = Adw.StatusPage(icon_name="dialog-warning-symbolic",
                                    title="Statistics Not Loaded")
        self.stack.add_named(self.error, "error")
        toolbar.set_content(self.stack)
        self.set_child(toolbar)

        self.totals = Adw.PreferencesGroup(title="All Time")
        self.total_rows = {key: property_row(title) for key, title in (
            ("distance", "Distance"), ("points", "Points"),
            ("countries", "Countries"), ("cities", "Cities"))}
        for row in self.total_rows.values():
            self.totals.add(row)
        self.page.add(self.totals)
        self.year_group = Adw.PreferencesGroup()
        self.year_row = Adw.ComboRow(title="Year")
        self.year_row.connect("notify::selected", self._on_year)
        self.year_group.add(self.year_row)
        self.page.add(self.year_group)
        self.months = Adw.PreferencesGroup(title="Distance per Month")
        self.month_rows = []
        self.page.add(self.months)
        self.places = Adw.PreferencesGroup(title="Countries and Cities")
        self.place_rows = []
        self.page.add(self.places)
        tasks.run(window.account.client().stats, self._on_stats)

    def _on_stats(self, stats, error):
        if error is not None:
            self.error.set_description(describe(error))
            self.stack.set_visible_child_name("error")
            return
        totals = model.totals(stats)
        self.total_rows["distance"].value.set_label(f"{totals['distance']} km")
        for key in ("points", "countries", "cities"):
            self.total_rows[key].value.set_label(f"{totals[key]:,}")
        self.years = model.years(stats)
        self.year_row.set_model(Gtk.StringList.new([str(y) for y, _k, _m in self.years]))
        self.year_group.set_visible(bool(self.years))
        self.stack.set_visible_child_name("stats")
        self._on_year()

    def _on_year(self, *_):
        for row in self.month_rows:
            self.months.remove(row)
        self.month_rows = []
        index = self.year_row.get_selected()
        if not self.years or index >= len(self.years):
            self.months.set_description("No distance recorded yet.")
            return
        year, total, months = self.years[index]
        self.months.set_description(f"{total} km in {year}")
        longest = max((km for _m, km in months), default=0) or 1
        for month, km in months:
            row = property_row(calendar.month_name[month], f"{km} km")
            bar = Gtk.LevelBar(min_value=0, max_value=longest, value=km,
                               valign=Gtk.Align.CENTER, hexpand=True)
            bar.set_size_request(60, -1)
            row.add_suffix(bar)
            row.update_property([Gtk.AccessibleProperty.LABEL],
                                [f"{calendar.month_name[month]}: {km} km"])
            self.months.add(row)
            self.month_rows.append(row)
        client = self.window.account.client()
        start, end = f"{year}-01-01", f"{year}-12-31"
        tasks.run(lambda: (client.countries(start, end), client.cities(start, end)),
                  lambda result, error: self._on_places(year, result, error))

    def _on_places(self, year, result, error):
        for row in self.place_rows:
            self.places.remove(row)
        self.place_rows = []
        if error is not None:
            self.places.set_description(describe(error))
            return
        countries, cities = result
        by_country = dict(model.cities(cities))
        names = model.countries(countries) or sorted(by_country)
        if not names:
            self.places.set_description(
                f"None for {year}. Dawarich names countries and cities only "
                "with reverse geocoding turned on.")
            return
        self.places.set_description("")
        for name in names:
            row = Adw.ActionRow(title=name, subtitle=", ".join(by_country.get(name, [])))
            self.places.add(row)
            self.place_rows.append(row)
