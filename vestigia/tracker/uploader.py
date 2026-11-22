"""Sends waiting points to the upload target, blocking (worker thread,
with its own Store connection). Overland: `batch_size` points per
request, marked only after {"result": "ok"}; a 422 batch is split until
the bad point is found and parked. OwnTracks: one point per request, any
2xx counts. A 401 stops everything (wrong credentials, or a hosted
Dawarich's points limit); network and server errors stop the run for a
retry later. No GTK."""
from dataclasses import dataclass

from phosh_toolkit.http import AUTH, SERVER, HttpError

from vestigia.tracker import protocols
from vestigia.tracker.target import OVERLAND

# Answers that refuse the points themselves, not the request.
REFUSED = (400, 422)


@dataclass
class Result:
    sent: int = 0
    parked: int = 0
    # None, or the HttpError that stopped the run.
    error: Exception = None

    @property
    def rejected(self):
        """The target refuses the credentials: retrying will not help."""
        return getattr(self.error, "kind", "") == AUTH


class Uploader:
    def __init__(self, store, target, http, secret, batch_size=50, device_id=""):
        self.store = store
        self.target = target
        self.http = http
        self.secret = secret
        self.batch_size = max(1, min(int(batch_size), 1000))
        self.device_id = device_id

    def run(self):
        result = Result()
        size = self.target.batch_size_limit or self.batch_size
        while True:
            batch = self.store.pending(self.target.key, size)
            if not batch:
                return result
            try:
                self._send_split(batch, result)
            except HttpError as error:
                result.error = error
                return result

    def _send_split(self, batch, result):
        try:
            self._send(batch)
        except HttpError as error:
            if error.status not in REFUSED:
                raise
            if len(batch) == 1:
                self.store.park(self.target.key, batch[0][0], str(error.status))
                result.parked += 1
                return
            half = len(batch) // 2
            self._send_split(batch[:half], result)
            self._send_split(batch[half:], result)
            return
        self.store.mark_uploaded(self.target.key, [i for i, _fix in batch])
        result.sent += len(batch)

    def _send(self, batch):
        headers = self.target.headers(self.secret)
        if self.target.protocol == OVERLAND:
            body = protocols.overland_body([fix for _i, fix in batch],
                                           self.device_id)
            response = self.http.request("POST", self.target.url, headers=headers,
                                         body=body)
            if not protocols.overland_accepted(response.body):
                raise HttpError(SERVER, "The target did not confirm the points",
                                response.status)
        else:
            (_i, fix), = batch
            self.http.request("POST", self.target.url, headers=headers,
                              body=protocols.owntracks_body(fix, self.target.tracker_id))
