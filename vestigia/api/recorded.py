"""A stand-in for phosh_toolkit.http.Client that answers with the
recorded answers of a real Dawarich server (tests/data/dawarich/,
docs/dev-environment.md). Used by the tests and by demo mode; it never
makes up an answer: an unknown request is an error. No GTK."""
import json
from pathlib import Path
from urllib.parse import parse_qsl, urlsplit

from phosh_toolkit.http import AUTH, NETWORK, SERVER, HttpError, Response

DATA = Path(__file__).resolve().parents[2] / "tests" / "data" / "dawarich"
KEY = "recorded-api-key"
PASSWORD = "vestigia-demo-password"
OTP = "123456"
# The day the recordings hold data for (docs/dawarich-api.md).
DAY = "2024-04-21"


class RecordedHttp:
    def __init__(self, data=DATA, key=KEY, two_factor=False):
        self.data = Path(data)
        self.key = key
        self.two_factor = two_factor
        self.offline = False
        self.requests = []

    def answer(self, name):
        return json.loads((self.data / f"{name}.json").read_text(encoding="utf-8"))

    def choose(self, method, path, query, body):
        """The recording that answers a request, or None."""
        day = query.get("start_at", "")[:10]
        if (method, path) == ("POST", "/api/v1/auth/login"):
            if body.get("password") != PASSWORD:
                return "auth_login_wrong_password"
            return "auth_login_2fa" if self.two_factor else "auth_login"
        if (method, path) == ("POST", "/api/v1/auth/otp_challenge"):
            ok = body.get("otp_code") == OTP
            return "auth_otp_challenge" if ok else "auth_otp_challenge_wrong"
        if (method, path) == ("GET", "/api/v1/tracks"):
            return "tracks" if day == DAY else "tracks_before_recalculation"
        if (method, path) == ("GET", "/api/v1/points"):
            if day != DAY:
                return "points_empty_day"
            return {"1": "points_page1", "3": "points_page3"}.get(
                query.get("page", "1"), "points_page2")
        if (method, path) == ("GET", "/api/v1/timeline"):
            return "timeline_with_visit" if day == DAY else "timeline_empty_day"
        return {
            ("GET", "/api/v1/health"): "health",
            ("GET", "/api/v1/users/me"): "users_me",
            ("GET", "/api/v1/settings/mobile"): "settings_mobile_get",
            ("PATCH", "/api/v1/settings/mobile"): "settings_mobile_patch",
            ("POST", "/api/v1/overland/batches"): "overland_batch",
            ("POST", "/api/v1/owntracks/points"): "owntracks_point",
            ("GET", "/api/v1/visits"): "visits",
            ("GET", "/api/v1/stats"): "stats",
            ("GET", "/api/v1/points/tracked_months"): "tracked_months",
            ("GET", "/api/v1/countries/visited"): "countries_visited",
            ("GET", "/api/v1/countries/visited_cities"): "visited_cities",
        }.get((method, path)) or self._visit(method, path, body)

    @staticmethod
    def _visit(method, path, body):
        if not path.startswith("/api/v1/visits/"):
            return None
        if path.endswith("/possible_places"):
            return "visit_possible_places"
        if method == "PATCH":
            visit = body.get("visit") or {}
            if "place_id" in visit:
                return "visit_choose_place"
            return {"confirmed": "visit_confirm", "declined": "visit_decline",
                    "suggested": "visit_unconfirm",
                    None: "visit_rename"}.get(visit.get("status"))
        return None

    def request(self, method, url, headers=None, body=None,
                content_type="application/json", timeout=None):
        headers = headers or {}
        parts = urlsplit(url)
        query = dict(parse_qsl(parts.query))
        payload = json.loads(body) if body else {}
        self.requests.append((method, parts.path, query, payload))
        if self.offline:
            raise HttpError(NETWORK, "Network is unreachable")
        auth = headers.get("Authorization")
        if auth is not None and auth != f"Bearer {self.key}":
            raise HttpError(AUTH, "Signed out by the server", 401)
        name = self.choose(method, parts.path, query, payload)
        if name is None or not (self.data / f"{name}.json").is_file():
            raise HttpError(SERVER, f"No recorded answer for {method} "
                            f"{parts.path}", 404)
        recorded = self.answer(name)
        status = recorded["status"]
        if status == 401:
            raise HttpError(AUTH, "Signed out by the server", 401)
        if status >= 400:
            raise HttpError(SERVER, f"Server error {status}", status)
        text = json.dumps(recorded["body"]).replace("REDACTED", self.key)
        return Response(status, dict(recorded["headers"]), text.encode())
