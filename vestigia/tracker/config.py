"""The tracking settings on disk ($XDG_CONFIG_HOME/vestigia/tracking.json).
Secrets of a custom upload target are in the keyring. No GTK."""
from dataclasses import dataclass

from phosh_toolkit.settings import JsonStore, app_dir

from vestigia.tracker.target import BEARER, OVERLAND, Target

VERSION = 1
# Where points go.
TARGET_ACCOUNT = "account"      # the Dawarich account in the app
TARGET_CUSTOM = "custom"        # any Overland or OwnTracks receiver
TARGET_NONE = "none"            # only kept for GPX export


@dataclass
class TrackingSettings:
    mode: str = "precise"       # or "significant"
    distance: int = 10          # metres between points
    interval: int = 30          # seconds between points when not moving
    max_accuracy: int = 50      # metres; worse fixes are dropped
    batch_size: int = 50
    upload_automatically: bool = True
    keep_days: int = 30
    # With a Dawarich account: the same settings on every device.
    sync_with_server: bool = True
    target_kind: str = TARGET_ACCOUNT
    target_protocol: str = OVERLAND
    target_url: str = ""
    target_auth: str = BEARER
    target_user: str = ""
    tracker_id: str = "vg"
    # Tracking was on when the app last ran (resumed after a restart).
    tracking: bool = False
    # Inhibit suspend while tracking (docs/decisions/background-tracking.md).
    keep_awake: bool = True
    # Start `vestigia --background` at login (Background portal).
    autostart: bool = False

    def custom_target(self):
        if not self.target_url:
            return None
        return Target(self.target_protocol, self.target_url, self.target_auth,
                      self.target_user, self.tracker_id or "vg")


class Store(JsonStore):
    def __init__(self, path=None):
        super().__init__(path or app_dir("config", "vestigia") / "tracking.json",
                         TrackingSettings, VERSION)
