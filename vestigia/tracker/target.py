"""Where points go: a URL, a protocol and how to authenticate
(docs/decisions/upload-protocols.md). The secret itself lives in the
keyring. No GTK."""
from dataclasses import dataclass

from phosh_toolkit.http import basic_auth

OVERLAND = "overland"
OWNTRACKS = "owntracks"
PROTOCOLS = (OVERLAND, OWNTRACKS)
BEARER = "bearer"
BASIC = "basic"
NONE = "none"


@dataclass(frozen=True)
class Target:
    protocol: str
    url: str
    auth: str = BEARER
    # User name for HTTP basic auth.
    user: str = ""
    # OwnTracks tracker id (two characters shown on maps).
    tracker_id: str = "vg"

    @property
    def key(self):
        """Names the target in the point store's marks."""
        return f"{self.protocol} {self.url}"

    @property
    def batch_size_limit(self):
        """OwnTracks HTTP takes one location per request."""
        return 1 if self.protocol == OWNTRACKS else None

    def headers(self, secret):
        headers = {"Accept": "application/json"}
        if self.auth == BEARER and secret:
            headers["Authorization"] = f"Bearer {secret}"
        elif self.auth == BASIC:
            headers["Authorization"] = basic_auth(self.user, secret or "")
        if self.protocol == OWNTRACKS and self.user:
            # The OwnTracks Recorder files points under user and device.
            headers["X-Limit-U"] = self.user
            headers["X-Limit-D"] = self.tracker_id
        return headers
