"""Preferences → Tracking: how points are recorded, where they go and
how long they stay on the phone; optionally the same settings as on the
user's other devices through the Dawarich account."""
from gi.repository import Adw, GLib, Gtk

from vestigia.tracker import config
from vestigia.tracker.target import BASIC, BEARER, NONE, OVERLAND, OWNTRACKS
from vestigia.tracking import sync

MODES = [("precise", "Precise"), ("significant", "Significant Moves")]
TARGETS = [(config.TARGET_ACCOUNT, "Dawarich Account"),
           (config.TARGET_CUSTOM, "Other Server"),
           (config.TARGET_NONE, "Keep on This Phone")]
PROTOCOLS = [(OVERLAND, "Overland"), (OWNTRACKS, "OwnTracks HTTP")]
AUTHS = [(BEARER, "Token"), (BASIC, "User Name and Password"), (NONE, "None")]


def combo(title, choices, value, subtitle=""):
    row = Adw.ComboRow(title=title, subtitle=subtitle,
                       model=Gtk.StringList.new([label for _v, label in choices]))
    keys = [v for v, _label in choices]
    row.set_selected(keys.index(value) if value in keys else 0)
    return row, keys


def spin(title, subtitle, value, low, high, step):
    row = Adw.SpinRow.new_with_range(low, high, step)
    row.set_title(title)
    row.set_subtitle(subtitle)
    row.set_value(value)
    return row


class TrackingPage(Adw.PreferencesPage):
    def __init__(self, window, store):
        super().__init__(title="Tracking", icon_name="find-location-symbolic")
        self.window = window
        self.account = window.account
        self.store = store
        self.settings = store.load()
        self._push_source = 0
        s = self.settings

        recording = Adw.PreferencesGroup(title="Recording")
        self.mode_row, self.mode_keys = combo(
            "Mode", MODES, s.mode,
            "Significant moves use less power and record fewer points")
        self.distance_row = spin("Distance", "Metres between points", s.distance,
                                 1, 10000, 5)
        self.interval_row = spin("Interval", "Seconds between points when not "
                                 "moving", s.interval, 1, 3600, 5)
        self.accuracy_row = spin("Accuracy Limit", "Positions less accurate "
                                 "than this many metres are dropped",
                                 s.max_accuracy, 5, 1000, 5)
        for row in (self.mode_row, self.distance_row, self.interval_row,
                    self.accuracy_row):
            recording.add(row)
        self.add(recording)

        upload = Adw.PreferencesGroup(title="Upload")
        self.target_row, self.target_keys = combo("Send Points To", TARGETS,
                                                  s.target_kind)
        self.auto_row = Adw.SwitchRow(title="Upload Automatically",
                                      subtitle="Otherwise only when tracking stops",
                                      active=s.upload_automatically)
        self.batch_row = spin("Batch Size", "Points per request (Overland)",
                              s.batch_size, 1, 1000, 10)
        for row in (self.target_row, self.auto_row, self.batch_row):
            upload.add(row)
        self.add(upload)

        self.custom = Adw.PreferencesGroup(
            title="Other Server",
            description="Any server that receives Overland or OwnTracks HTTP.")
        self.protocol_row, self.protocol_keys = combo("Protocol", PROTOCOLS,
                                                      s.target_protocol)
        self.url_row = Adw.EntryRow(title="Address", text=s.target_url)
        self.url_row.set_input_purpose(Gtk.InputPurpose.URL)
        self.auth_row, self.auth_keys = combo("Log In With", AUTHS, s.target_auth)
        self.user_row = Adw.EntryRow(title="User Name", text=s.target_user)
        self.secret_row = Adw.PasswordEntryRow(title="Token or Password")
        self.secret_row.set_text(self.account.secrets.target_secret() or "")
        for row in (self.protocol_row, self.url_row, self.auth_row, self.user_row,
                    self.secret_row):
            self.custom.add(row)
        self.add(self.custom)

        background = Adw.PreferencesGroup(title="In the Background")
        self.awake_row = Adw.SwitchRow(
            title="Keep the Phone Awake While Tracking",
            subtitle="Otherwise the phone records nothing while it sleeps; "
                     "uses more power",
            active=s.keep_awake)
        self.autostart_row = Adw.SwitchRow(
            title="Start at Login",
            subtitle="Tracking that was on goes on after a restart",
            active=s.autostart)
        self.autostart_row.connect("notify::active", self._on_autostart)
        background.add(self.awake_row)
        background.add(self.autostart_row)
        self.add(background)

        storage = Adw.PreferencesGroup(title="On This Phone")
        self.keep_row = spin("Keep Points", "Days, also after upload, for GPX "
                             "export", s.keep_days, 1, 3650, 1)
        storage.add(self.keep_row)
        self.sync_row = Adw.SwitchRow(
            title="Same Settings on Every Device",
            subtitle="Mode, distance, interval, batch size and automatic upload "
                     "come from your Dawarich account",
            active=s.sync_with_server, sensitive=self.account.configured)
        storage.add(self.sync_row)
        self.add(storage)

        for row in (self.mode_row, self.target_row, self.protocol_row, self.auth_row):
            row.connect("notify::selected", self._changed)
        for row in (self.distance_row, self.interval_row, self.accuracy_row,
                    self.batch_row, self.keep_row):
            row.connect("notify::value", self._changed)
        for row in (self.auto_row, self.sync_row, self.awake_row):
            row.connect("notify::active", self._changed)
        for row in (self.url_row, self.user_row, self.secret_row):
            row.connect("changed", self._changed)
        self._update_custom()
        sync.pull(self.account, self.store, self._pulled)

    def _on_autostart(self, row, _pspec):
        if self._loading:
            return
        from vestigia.tracking.background import request_autostart
        enable = row.get_active()

        def done(ok, message):
            if not ok and enable:
                self._loading = True
                row.set_active(False)
                self._loading = False
                self.window.toast(f"Start at login is not available: {message}")
                return
            s = self.store.load()
            s.autostart = enable and ok
            self.store.save(s)
            self.settings.autostart = s.autostart

        request_autostart(self.window, enable, done)

    def _update_custom(self):
        custom = self.target_keys[self.target_row.get_selected()] == config.TARGET_CUSTOM
        self.custom.set_visible(custom)
        auth = self.auth_keys[self.auth_row.get_selected()]
        self.user_row.set_visible(auth == BASIC or
                                  self.protocol_keys[self.protocol_row.get_selected()] == OWNTRACKS)
        self.secret_row.set_visible(auth != NONE)

    def _pulled(self, changed, error):
        if changed:
            self.settings = self.store.load()
            s = self.settings
            self._loading = True
            self.mode_row.set_selected(self.mode_keys.index(s.mode))
            self.distance_row.set_value(s.distance)
            self.interval_row.set_value(s.interval)
            self.batch_row.set_value(s.batch_size)
            self.auto_row.set_active(s.upload_automatically)
            self._loading = False

    _loading = False

    def _changed(self, *_):
        if self._loading:
            return
        # Fresh from disk: the tracker writes `tracking` meanwhile.
        s = self.settings = self.store.load()
        s.mode = self.mode_keys[self.mode_row.get_selected()]
        s.distance = int(self.distance_row.get_value())
        s.interval = int(self.interval_row.get_value())
        s.max_accuracy = int(self.accuracy_row.get_value())
        s.batch_size = int(self.batch_row.get_value())
        s.upload_automatically = self.auto_row.get_active()
        s.keep_days = int(self.keep_row.get_value())
        s.sync_with_server = self.sync_row.get_active()
        s.keep_awake = self.awake_row.get_active()
        s.target_kind = self.target_keys[self.target_row.get_selected()]
        s.target_protocol = self.protocol_keys[self.protocol_row.get_selected()]
        s.target_url = self.url_row.get_text().strip()
        s.target_auth = self.auth_keys[self.auth_row.get_selected()]
        s.target_user = self.user_row.get_text().strip()
        self.account.secrets.store_target_secret(self.secret_row.get_text())
        self.store.save(s)
        self._update_custom()
        self.window.tracking_settings_changed()
        # One request after the user stops changing values.
        if self._push_source:
            GLib.source_remove(self._push_source)
        self._push_source = GLib.timeout_add(1000, self._push)

    def _push(self):
        self._push_source = 0
        sync.push(self.account, self.settings)
        return GLib.SOURCE_REMOVE
