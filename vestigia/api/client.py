"""Blocking calls to a Dawarich server, for worker threads
(phosh_toolkit.tasks). The key is sent only as `Authorization: Bearer`,
never in a URL. Errors are phosh_toolkit.http.HttpError; `kind` says
what went wrong. No GTK."""
import json
from dataclasses import dataclass
from urllib.parse import urlencode, urlsplit

from phosh_toolkit.http import AUTH, SERVER, HttpError

from vestigia.api import version

TOO_OLD = "too-old"
# Tracks and points come in pages; a day rarely has more than a few.
PER_PAGE = 500
MAX_PAGES = 50


def normalize_url(text):
    """The base URL of a server as typed: scheme added, path kept,
    trailing slash removed. ValueError if there is no host."""
    text = (text or "").strip()
    if text and "://" not in text:
        text = "https://" + text
    parts = urlsplit(text)
    if parts.scheme not in ("http", "https") or not parts.hostname:
        raise ValueError("Enter the address of your Dawarich server")
    return text.rstrip("/")


def header(headers, name):
    for key, value in headers.items():
        if key.lower() == name.lower():
            return value
    return ""


@dataclass
class Login:
    """The answer of a login: the key, or a challenge for the 2FA code."""
    api_key: str = ""
    challenge: str = ""
    email: str = ""


class Dawarich:
    def __init__(self, http, server_url, api_key=None):
        self.http = http
        self.server_url = server_url.rstrip("/")
        self.api_key = api_key

    def call(self, method, path, query=None, body=None, auth=True):
        """The Response of one request; HttpError for errors."""
        url = self.server_url + path
        if query:
            url += "?" + urlencode(query)
        headers = {"Accept": "application/json"}
        if auth:
            if not self.api_key:
                raise HttpError(AUTH, "Not logged in", 401)
            headers["Authorization"] = f"Bearer {self.api_key}"
        data = json.dumps(body).encode() if body is not None else None
        return self.http.request(method, url, headers=headers, body=data)

    def json(self, *args, **kwargs):
        response = self.call(*args, **kwargs)
        try:
            return json.loads(response.body or b"null")
        except ValueError:
            raise HttpError(SERVER, "The server sent an answer that is not "
                            "JSON", response.status) from None

    # Account

    def health(self):
        """The server's version; HttpError(TOO_OLD) below the minimum."""
        response = self.call("GET", "/api/v1/health", auth=False)
        found = header(response.headers, "X-Dawarich-Version")
        if not version.supported(found):
            raise HttpError(TOO_OLD, f"Dawarich {found or 'of unknown version'}"
                            f" is too old; Travel Log needs "
                            f"{version.shown()} or newer")
        return found

    def login(self, email, password):
        try:
            answer = self.json("POST", "/api/v1/auth/login", auth=False,
                               body={"email": email, "password": password})
        except HttpError as error:
            if error.kind == AUTH:
                raise HttpError(AUTH, "Wrong e-mail or password", 401) from None
            raise
        return self._login(answer)

    def otp(self, challenge, code):
        try:
            answer = self.json("POST", "/api/v1/auth/otp_challenge", auth=False,
                               body={"challenge_token": challenge,
                                     "otp_code": code.strip()})
        except HttpError as error:
            if error.kind == AUTH:
                raise HttpError(AUTH, "Wrong or expired code", 401) from None
            raise
        return self._login(answer)

    @staticmethod
    def _login(answer):
        answer = answer or {}
        if answer.get("two_factor_required"):
            return Login(challenge=answer.get("challenge_token", ""))
        if not answer.get("api_key"):
            raise HttpError(SERVER, "The server sent no API key")
        return Login(api_key=answer["api_key"], email=answer.get("email", ""))

    def me(self):
        return (self.json("GET", "/api/v1/users/me") or {}).get("user", {})

    # History

    def _pages(self, path, query, items):
        out = []
        for page in range(1, MAX_PAGES + 1):
            response = self.call("GET", path, dict(query, page=page,
                                                   per_page=PER_PAGE))
            out.extend(items(json.loads(response.body or b"null")))
            total = header(response.headers, "X-Total-Pages")
            if not total.isdigit() or page >= int(total):
                break
        return out

    def tracks(self, start, end):
        """GeoJSON features (LineStrings) between two ISO times."""
        return self._pages("/api/v1/tracks", {"start_at": start, "end_at": end},
                           lambda body: (body or {}).get("features") or [])

    def points(self, start, end):
        return self._pages("/api/v1/points", {"start_at": start, "end_at": end,
                                              "order": "asc"},
                           lambda body: body or [])

    def timeline(self, start, end):
        days = (self.json("GET", "/api/v1/timeline",
                          {"start_at": start, "end_at": end}) or {}).get("days")
        return days or []

    # Tracking settings of the mobile apps

    def mobile_settings(self):
        return (self.json("GET", "/api/v1/settings/mobile") or {}).get("settings") or {}

    def update_mobile_settings(self, values):
        answer = self.json("PATCH", "/api/v1/settings/mobile",
                           body={"settings": values}) or {}
        return answer.get("settings") or {}

    # Visits

    def visits(self, start, end):
        return self.json("GET", "/api/v1/visits",
                         {"start_at": start, "end_at": end}) or []

    def possible_places(self, visit_id):
        return self.json("GET", f"/api/v1/visits/{int(visit_id)}/possible_places") or []

    def update_visit(self, visit_id, **fields):
        """PATCH name, status ("suggested", "confirmed", "declined") or
        place_id. Dawarich confirms a suggested visit on any edit unless
        a status is sent (docs/dawarich-api.md)."""
        return self.json("PATCH", f"/api/v1/visits/{int(visit_id)}",
                         body={"visit": fields}) or {}

    # Statistics

    def stats(self):
        return self.json("GET", "/api/v1/stats") or {}

    def countries(self, start, end):
        return self.json("GET", "/api/v1/countries/visited",
                         {"start_at": start, "end_at": end}) or {}

    def cities(self, start, end):
        return self.json("GET", "/api/v1/countries/visited_cities",
                         {"start_at": start, "end_at": end}) or {}

    def tracked_months(self):
        return self.json("GET", "/api/v1/points/tracked_months") or []
