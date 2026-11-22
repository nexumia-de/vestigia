"""Tracking without a window (docs/decisions/background-tracking.md):
hold the application while the tracker runs, inhibit suspend if the
user wants that, and ask the Background portal for autostart."""
import logging

from gi.repository import Gtk

log = logging.getLogger("vestigia.tracking")
REASON = "Recording your location"


class Keeper:
    """Follows the tracker's `changed` signal; `app` is the
    Gtk.Application."""

    def __init__(self, app, tracker):
        self.app = app
        self.tracker = tracker
        self.held = False
        self.cookie = 0
        tracker.connect("changed", lambda *_: self.update())

    def update(self):
        running = self.tracker.running
        if running and not self.held:
            self.app.hold()
            self.held = True
        elif not running and self.held:
            self.app.release()
            self.held = False
        awake = running and self.tracker.settings.keep_awake
        if awake and not self.cookie:
            self.cookie = self.app.inhibit(self.app.get_active_window(),
                                           Gtk.ApplicationInhibitFlags.SUSPEND, REASON)
            if not self.cookie:
                log.info("suspend could not be inhibited")
        elif not awake and self.cookie:
            self.app.uninhibit(self.cookie)
            self.cookie = 0


def request_autostart(window, enable, done=None):
    """Ask the Background portal to start `vestigia --background` at
    login (or no longer); done(ok, message)."""
    import gi
    gi.require_version("Xdp", "1.0")
    gi.require_version("XdpGtk4", "1.0")
    from gi.repository import GLib, Xdp, XdpGtk4
    try:
        portal = Xdp.Portal.initable_new()
    except GLib.Error as error:
        if done:
            done(False, error.message)
        return
    flags = Xdp.BackgroundFlags.AUTOSTART if enable else Xdp.BackgroundFlags.NONE
    parent = XdpGtk4.parent_new_gtk(window) if window else None

    def finished(portal, result):
        try:
            ok = portal.request_background_finish(result)
            message = "" if ok else "The request was refused"
        except GLib.Error as error:
            ok, message = False, error.message
        if done:
            done(ok, message)

    portal.request_background(parent, REASON, ["vestigia", "--background"], flags,
                              None, finished)
