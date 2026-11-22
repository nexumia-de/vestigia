"""Export a day's points recorded on this phone as GPX, saved through
the file chooser portal (Gtk.FileDialog)."""
from datetime import datetime, timedelta

from gi.repository import Gio, GLib, Gtk

from vestigia.tracker import gpx


def day_bytes(store, day):
    """GPX of the points recorded on `day` (local time), or None."""
    start = datetime.combine(day, datetime.min.time())
    end = start + timedelta(days=1)
    fixes = store.between(start.timestamp(), end.timestamp())
    if not fixes:
        return None
    return gpx.write(fixes, f"Travel Log {day.isoformat()}")


def export_day(window, day):
    data = day_bytes(window.tracker.store, day)
    if data is None:
        window.toast("No points were recorded on this phone that day")
        return
    dialog = Gtk.FileDialog(title="Export GPX",
                            initial_name=f"travel-log-{day.isoformat()}.gpx")
    gpx_filter = Gtk.FileFilter(name="GPX Files")
    gpx_filter.add_pattern("*.gpx")
    filters = Gio.ListStore.new(Gtk.FileFilter)
    filters.append(gpx_filter)
    dialog.set_filters(filters)

    def chosen(dialog, result):
        try:
            file = dialog.save_finish(result)
        except GLib.Error:
            return                      # cancelled
        save(window, file, data)

    dialog.save(window, None, chosen)


def save(window, file, data):
    try:
        file.replace_contents(data, None, False,
                              Gio.FileCreateFlags.REPLACE_DESTINATION, None)
    except GLib.Error as error:
        window.toast(f"Not saved: {error.message}")
        return
    window.toast(f"Saved {file.get_basename()}")
