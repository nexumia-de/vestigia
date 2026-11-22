"""A stand-in HTTP client for upload tests that answers with recorded
answers (tests/data/), chosen per request, and raises like
phosh_toolkit.http.Client."""
import json
from pathlib import Path

from phosh_toolkit.http import AUTH, NETWORK, SERVER, HttpError, Response

DATA = Path(__file__).parent / "data"


def recording(name):
    return json.loads((DATA / f"{name}.json").read_text(encoding="utf-8"))


class Replay:
    def __init__(self, choose):
        """choose(url, headers, body) -> recording name like
        "dawarich/overland_batch", or None for a network error."""
        self.choose = choose
        self.requests = []

    def request(self, method, url, headers=None, body=None, **kwargs):
        self.requests.append((method, url, dict(headers or {}), json.loads(body)))
        name = self.choose(url, headers or {}, json.loads(body))
        if name is None:
            raise HttpError(NETWORK, "Network is unreachable")
        answer = recording(name)
        status = answer["status"]
        if status == 401:
            raise HttpError(AUTH, "Signed out by the server", 401)
        if status >= 400:
            raise HttpError(SERVER, f"Server error {status}", status)
        return Response(status, answer["headers"], json.dumps(answer["body"]).encode())
