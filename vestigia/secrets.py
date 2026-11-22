"""The Dawarich API key in the keyring (libsecret; in the Flatpak the
Secret portal), never in a settings file or a log line. No GTK.

phosh_toolkit.keyring keeps a secret in memory when the keyring is
locked or missing; `persistent` tells the UI so it can say the key is
lost when the app closes."""
import os

from phosh_toolkit.keyring import Keyring

from vestigia import APP_ID

API_KEY = "api-key"
# Token or password of a custom upload target.
TARGET_SECRET = "target-secret"
# "memory" keeps everything in memory (tests, screenshots, demo data).
MEMORY_ENV = "VESTIGIA_KEYRING"


class Secrets:
    def __init__(self, keyring=None):
        self.keyring = keyring or Keyring(
            APP_ID, {API_KEY: "Travel Log: Dawarich API key",
                     TARGET_SECRET: "Travel Log: upload target password"},
            MEMORY_ENV)

    def api_key(self):
        return self.keyring.lookup(API_KEY)

    def store_api_key(self, key):
        """Store the key; False if it could only be kept in memory."""
        self.keyring.store(API_KEY, key)
        return self.persistent

    def clear(self):
        self.keyring.clear(API_KEY)

    def target_secret(self):
        return self.keyring.lookup(TARGET_SECRET)

    def store_target_secret(self, value):
        if value:
            self.keyring.store(TARGET_SECRET, value)
        else:
            self.keyring.clear(TARGET_SECRET)

    @property
    def persistent(self):
        """True unless the last store fell back to memory because the
        keyring is locked or missing. The toolkit has no public accessor
        for its memory fallback yet (owner checks)."""
        if os.environ.get(MEMORY_ENV) == "memory":
            return True
        return API_KEY not in self.keyring._memory
