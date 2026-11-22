"""The bottom bar of the history page: previous, the period with a
popover (day / week / month and a calendar marking days with data),
next. Within thumb reach (phosh-toolkit adaptive rule 10)."""
from datetime import date

from gi.repository import Adw, GLib, GObject, Gtk

from vestigia.day import period as periods

NAMES = {periods.DAY: ("Day", "Previous Day", "Next Day"),
         periods.WEEK: ("Week", "Previous Week", "Next Week"),
         periods.MONTH: ("Month", "Previous Month", "Next Month")}


class DayBar(Adw.Bin):
    """`step(n)`, `picked(date)`, `span(name)`; `month-shown(year,
    month)` asks the page for the calendar's marks."""
    __gsignals__ = {
        "step": (GObject.SignalFlags.RUN_FIRST, None, (int,)),
        "picked": (GObject.SignalFlags.RUN_FIRST, None, (object,)),
        "span": (GObject.SignalFlags.RUN_FIRST, None, (str,)),
        "month-shown": (GObject.SignalFlags.RUN_FIRST, None, (int, int)),
    }

    def __init__(self):
        super().__init__()
        box = Gtk.CenterBox(margin_start=6, margin_end=6, margin_top=6,
                            margin_bottom=6)
        self.prev_button = self._icon_button("go-previous-symbolic", -1)
        self.next_button = self._icon_button("go-next-symbolic", 1)

        content = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        spans = Gtk.Box(css_classes=["linked"], halign=Gtk.Align.CENTER)
        self.span_buttons = {}
        group = None
        for span in periods.SPANS:
            button = Gtk.ToggleButton(label=NAMES[span][0], group=group)
            group = group or button
            button.connect("toggled", self._on_span, span)
            spans.append(button)
            self.span_buttons[span] = button
        content.append(spans)
        self.calendar = Gtk.Calendar()
        self._selecting = False
        self.calendar.connect("day-selected", self._on_calendar)
        for signal in ("next-month", "prev-month", "next-year", "prev-year"):
            self.calendar.connect(signal, lambda *_: self._month_shown())
        content.append(self.calendar)
        popover = Gtk.Popover(child=content)
        popover.connect("show", lambda *_: self._month_shown())
        self.date_button = Gtk.MenuButton(popover=popover,
                                          tooltip_text="Choose a Day")
        self.date_button.add_css_class("flat")
        box.set_start_widget(self.prev_button)
        box.set_center_widget(self.date_button)
        box.set_end_widget(self.next_button)
        self.set_child(box)

    def _icon_button(self, icon, step):
        button = Gtk.Button(icon_name=icon)
        button.set_size_request(48, 48)
        button.add_css_class("flat")
        button.connect("clicked", lambda *_: self.emit("step", step))
        return button

    def show_period(self, period, today=None):
        today = today or date.today()
        text = periods.label(period, today)
        self.date_button.set_label(text)
        self.next_button.set_sensitive(period.end < today)
        _name, previous, following = NAMES[period.span]
        for button, label in ((self.prev_button, previous), (self.next_button, following)):
            button.set_tooltip_text(label)
            button.update_property([Gtk.AccessibleProperty.LABEL], [label])
        self._selecting = True
        self.span_buttons[period.span].set_active(True)
        day = period.start
        self.calendar.select_day(GLib.DateTime.new_local(day.year, day.month,
                                                         day.day, 0, 0, 0))
        self._selecting = False
        return text

    def mark(self, year, month, days):
        """Mark `days` if the calendar still shows that month."""
        if (self.calendar.props.year, self.calendar.props.month + 1) != (year, month):
            return
        self.calendar.clear_marks()
        for day in days:
            self.calendar.mark_day(day)

    def _month_shown(self):
        self.calendar.clear_marks()
        self.emit("month-shown", self.calendar.props.year,
                  self.calendar.props.month + 1)

    def _on_span(self, button, span):
        if button.get_active() and not self._selecting:
            self.emit("span", span)

    def _on_calendar(self, calendar):
        if self._selecting:
            return
        value = calendar.get_date()
        self.date_button.get_popover().popdown()
        self.emit("picked", date(value.get_year(), value.get_month(),
                                 value.get_day_of_month()))
