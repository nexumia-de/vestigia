#!/usr/bin/env python3
"""Record the answers of the local Dawarich server (dev/dawarich/up.sh)
into tests/data/dawarich/, so that tests run without a server.

Usage: python3 dev/dawarich/record.py

Uploads the points of tests/data/source/gpx_track_multiple_segments.gpx
(a real OsmAnd recording from Dawarich's own test fixtures) to the demo
account, asks the server to compute tracks, and stores every answer as
one JSON file. The API key, the 2FA secret and challenge tokens never
reach the files. Python standard library only.
"""
import base64
import hashlib
import hmac
import json
import struct
import sys
import time
import urllib.error
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlencode

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "tests" / "data" / "dawarich"
GPX = ROOT / "tests" / "data" / "source" / "gpx_track_multiple_segments.gpx"
SERVER = "http://127.0.0.1:3000"
EMAIL = "demo@vestigia.test"
PASSWORD = "vestigia-demo-password"
DAY = ("2024-04-21T00:00:00Z", "2024-04-21T23:59:59Z")
# The day before: no data.
EMPTY_DAY = ("2024-04-20T00:00:00Z", "2024-04-20T23:59:59Z")
KEPT_HEADERS = ("content-type", "x-dawarich-version", "x-dawarich-response",
                "x-current-page", "x-total-pages")
# Overridden by dev/owntracks/record.py.
SERVER_NAME = ""
BY = "dev/dawarich/record.py"
USER_AGENT = "Vestigia-recorder (+https://github.com/nexumia-de/vestigia)"
NS = {"g": "http://www.topografix.com/GPX/1/1",
      "osmand": "https://osmand.net"}

secrets = set()


def call(method, path, key=None, query=None, body=None, headers=None):
    url = SERVER + path + ("?" + urlencode(query) if query else "")
    data = json.dumps(body).encode() if body is not None else None
    request = urllib.request.Request(url, data=data, method=method)
    request.add_header("Accept", "application/json")
    request.add_header("User-Agent", USER_AGENT)
    if data is not None:
        request.add_header("Content-Type", "application/json")
    if key:
        request.add_header("Authorization", f"Bearer {key}")
    for name, value in (headers or {}).items():
        request.add_header(name, value)
    try:
        with urllib.request.urlopen(request, timeout=60) as response:
            status, raw, head = response.status, response.read(), response.headers
    except urllib.error.HTTPError as error:
        status, raw, head = error.code, error.read(), error.headers
    try:
        parsed = json.loads(raw) if raw else None
    except ValueError:
        parsed = raw.decode("utf-8", "replace")
    kept = {name: head[name] for name in KEPT_HEADERS if head.get(name)}
    return {"request": {"method": method, "path": path, "query": query or {},
                        "body": body},
            "status": status, "headers": kept, "body": parsed}


def redact(value):
    text = json.dumps(value, ensure_ascii=False)
    for secret in secrets:
        text = text.replace(secret, "REDACTED")
    return json.loads(text)


def save(name, answer, note=""):
    OUT.mkdir(parents=True, exist_ok=True)
    answer = redact(answer)
    answer["recorded"] = {
        "server": SERVER_NAME or
        "Dawarich " + answer["headers"].get("x-dawarich-version", "?"),
        "at": datetime.now(timezone.utc).date().isoformat(),
        "by": BY,
    }
    if note:
        answer["recorded"]["note"] = note
    (OUT / f"{name}.json").write_text(
        json.dumps(answer, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"{name}: {answer['status']}")
    return answer


def gpx_points():
    """(lat, lon, ele, time, hdop, speed) of every track point."""
    tree = ET.fromstring(GPX.read_text(encoding="utf-8").strip())
    points = []
    for p in tree.iterfind(".//g:trkpt", NS):
        def text(tag):
            node = p.find(tag, NS)
            return node.text if node is not None else None
        points.append((float(p.get("lat")), float(p.get("lon")),
                       float(text("g:ele")), text("g:time"),
                       float(text("g:hdop")),
                       float(text("g:extensions/osmand:speed") or 0)))
    return points


def overland(point):
    lat, lon, ele, when, hdop, speed = point
    # OsmAnd writes the fix's accuracy in metres into <hdop>.
    return {"type": "Feature",
            "geometry": {"type": "Point", "coordinates": [lon, lat]},
            "properties": {"timestamp": when, "altitude": ele,
                           "horizontal_accuracy": hdop, "speed": speed}}


def totp(secret_b32, at=None):
    key = base64.b32decode(secret_b32.upper() + "=" * (-len(secret_b32) % 8))
    counter = int((at or time.time()) // 30)
    digest = hmac.new(key, struct.pack(">Q", counter), hashlib.sha1).digest()
    offset = digest[-1] & 15
    code = struct.unpack(">I", digest[offset:offset + 4])[0] & 0x7FFFFFFF
    return f"{code % 1000000:06d}"


def main():
    save("health", call("GET", "/api/v1/health"))
    login = call("POST", "/api/v1/auth/login",
                 body={"email": EMAIL, "password": PASSWORD})
    key = (login["body"] or {}).get("api_key")
    if not key:
        sys.exit(f"login failed: {login['status']} {login['body']}")
    secrets.add(key)
    secrets.add(PASSWORD)
    save("auth_login", login)
    save("auth_login_wrong_password", call(
        "POST", "/api/v1/auth/login",
        body={"email": EMAIL, "password": "not-the-password"}))
    save("users_me", call("GET", "/api/v1/users/me", key))
    save("users_me_bad_key", call("GET", "/api/v1/users/me", "not-a-key"))

    # Tracking settings: empty on a new account, then clamped.
    save("settings_mobile_get_new", call("GET", "/api/v1/settings/mobile", key))
    save("settings_mobile_patch", call(
        "PATCH", "/api/v1/settings/mobile", key,
        body={"settings": {"tracking_mode": "precise", "distance_filter": 50000,
                           "time_filter": 30, "accuracy": 1, "batch_size": 50,
                           "upload_automatically": True}}),
        note="distance_filter 50000 is clamped by the server")
    save("settings_mobile_patch_bad_mode", call(
        "PATCH", "/api/v1/settings/mobile", key,
        body={"settings": {"tracking_mode": "sometimes"}}))
    save("settings_mobile_get", call("GET", "/api/v1/settings/mobile", key))

    # Uploads.
    points = gpx_points()
    batch = {"locations": [overland(p) for p in points]}
    save("overland_batch", call("POST", "/api/v1/overland/batches", key, body=batch))
    save("overland_batch_again", call("POST", "/api/v1/overland/batches", key,
                                      body=batch),
         note="the same batch a second time")
    bad = {"locations": [dict(overland(points[0]),
                              properties={"timestamp": "yesterday"})]}
    save("overland_batch_bad_timestamp",
         call("POST", "/api/v1/overland/batches", key, body=bad))
    save("overland_batch_bad_key",
         call("POST", "/api/v1/overland/batches", "not-a-key", body=batch))
    zero = {"locations": [dict(overland(points[0]), geometry={
        "type": "Point", "coordinates": [0.0, 0.0]})]}
    save("overland_batch_zero", call("POST", "/api/v1/overland/batches", key,
                                     body=zero))
    lat, lon, ele, when, hdop, speed = points[0]
    owntracks = {"_type": "location", "lat": lat, "lon": lon, "alt": round(ele),
                 "acc": round(hdop), "vel": round(speed * 3.6), "tid": "vg",
                 "tst": int(datetime.fromisoformat(when.replace("Z", "+00:00"))
                            .timestamp())}
    save("owntracks_point", call("POST", "/api/v1/owntracks/points", key,
                                 body=owntracks))
    save("owntracks_point_bad_key", call("POST", "/api/v1/owntracks/points",
                                         "not-a-key", body=owntracks))
    basic = "Basic " + base64.b64encode(f"{EMAIL}:{key}".encode()).decode()
    save("owntracks_point_basic_auth", call(
        "POST", "/api/v1/owntracks/points", body=owntracks,
        headers={"Authorization": basic}),
        note="HTTP basic auth with the e-mail and the API key")

    # Reading history.
    time.sleep(5)
    query = {"start_at": DAY[0], "end_at": DAY[1], "per_page": 20, "order": "asc"}
    for page in (1, 2, 3):
        save(f"points_page{page}", call("GET", "/api/v1/points", key,
                                        dict(query, page=page)))
    save("tracks_before_recalculation", call(
        "GET", "/api/v1/tracks", key, {"start_at": DAY[0], "end_at": DAY[1]}))
    save("recalculations", call("POST", "/api/v1/recalculations", key,
                                {"year": 2024}))
    tracks = None
    for _ in range(60):
        time.sleep(5)
        tracks = call("GET", "/api/v1/tracks", key,
                      {"start_at": DAY[0], "end_at": DAY[1]})
        if tracks["body"] and tracks["body"].get("features"):
            break
    save("tracks", tracks)
    features = (tracks["body"] or {}).get("features") or []
    if features:
        track_id = features[0]["properties"]["id"]
        save("track_points", call("GET", f"/api/v1/tracks/{track_id}/points", key))
    # The recording's first segment is a two-minute stop, shorter than
    # Dawarich's automatic visit detection; create it as a suggested visit
    # through the API to record the visit answers.
    stop = points[:16]
    visit = {"visit": {
        "name": "Stop", "status": "suggested",
        "latitude": round(sum(p[0] for p in stop) / len(stop), 6),
        "longitude": round(sum(p[1] for p in stop) / len(stop), 6),
        "started_at": stop[0][3], "ended_at": stop[-1][3]}}
    created = save("visit_create", call("POST", "/api/v1/visits", key, body=visit))
    visit_id = (created["body"] or {}).get("id")
    save("visits", call("GET", "/api/v1/visits", key,
                        {"start_at": DAY[0], "end_at": DAY[1]}))
    if visit_id:
        save("visit_possible_places", call(
            "GET", f"/api/v1/visits/{visit_id}/possible_places", key))
        save("visit_rename", call("PATCH", f"/api/v1/visits/{visit_id}", key,
                                  body={"visit": {"name": "Morning stop"}}))
        save("visit_confirm", call("PATCH", f"/api/v1/visits/{visit_id}", key,
                                   body={"visit": {"status": "confirmed"}}))
        save("visit_unconfirm", call("PATCH", f"/api/v1/visits/{visit_id}", key,
                                     body={"visit": {"status": "suggested"}}),
             note="undo of a confirmation")
        places = save("visit_possible_places_again", call(
            "GET", f"/api/v1/visits/{visit_id}/possible_places", key))["body"] or []
        if places:
            save("visit_choose_place", call(
                "PATCH", f"/api/v1/visits/{visit_id}", key,
                body={"visit": {"place_id": places[0]["id"], "status": "confirmed"}}))
        save("timeline_with_visit", call("GET", "/api/v1/timeline", key,
                                         {"start_at": DAY[0], "end_at": DAY[1]}))
        save("visit_decline", call("PATCH", f"/api/v1/visits/{visit_id}", key,
                                   body={"visit": {"status": "declined"}}))
        save("visits_after_decline", call("GET", "/api/v1/visits", key,
                                          {"start_at": DAY[0], "end_at": DAY[1]}))
        save("visit_suggest_again", call(
            "PATCH", f"/api/v1/visits/{visit_id}", key,
            body={"visit": {"status": "suggested"}}))
    save("timeline", call("GET", "/api/v1/timeline", key,
                          {"start_at": DAY[0], "end_at": DAY[1]}))
    save("points_empty_day", call("GET", "/api/v1/points", key,
                                  dict(query, start_at=EMPTY_DAY[0],
                                       end_at=EMPTY_DAY[1], page=1)))
    save("timeline_empty_day", call("GET", "/api/v1/timeline", key,
                                    {"start_at": EMPTY_DAY[0],
                                     "end_at": EMPTY_DAY[1]}))
    save("stats", call("GET", "/api/v1/stats", key))
    save("tracked_months", call("GET", "/api/v1/points/tracked_months", key))
    save("countries_visited", call("GET", "/api/v1/countries/visited", key,
                                   {"start_at": DAY[0], "end_at": DAY[1]}))
    save("visited_cities", call("GET", "/api/v1/countries/visited_cities", key,
                                {"start_at": DAY[0], "end_at": DAY[1]}))

    # Two-factor login: enable 2FA, log in, answer the challenge, disable.
    setup = call("POST", "/api/v1/users/me/two_factor/setup", key,
                 body={"password": PASSWORD})
    secret = (setup["body"] or {}).get("otp_secret") or \
        (setup["body"] or {}).get("secret")
    if setup["status"] >= 300 or not secret:
        print(f"2FA setup failed: {setup['status']} {setup['body']}")
        return
    secrets.add(secret)
    if (setup["body"] or {}).get("provisioning_uri"):
        secrets.add(setup["body"]["provisioning_uri"])
    confirm = call("POST", "/api/v1/users/me/two_factor/confirm", key,
                   body={"password": PASSWORD, "otp_code": totp(secret)})
    for code in (confirm["body"] or {}).get("backup_codes") or []:
        secrets.add(code)
    print(f"2FA confirm: {confirm['status']}")
    challenge = call("POST", "/api/v1/auth/login",
                     body={"email": EMAIL, "password": PASSWORD})
    token = (challenge["body"] or {}).get("challenge_token")
    if token:
        secrets.add(token)
    save("auth_login_2fa", challenge)
    save("auth_otp_challenge_wrong", call(
        "POST", "/api/v1/auth/otp_challenge",
        body={"challenge_token": token, "otp_code": "000000"}))
    time.sleep(31)  # a fresh code: the confirmed one may not count twice
    save("auth_otp_challenge", call(
        "POST", "/api/v1/auth/otp_challenge",
        body={"challenge_token": token, "otp_code": totp(secret)}))
    time.sleep(31)
    disable = call("DELETE", "/api/v1/users/me/two_factor", key,
                   body={"password": PASSWORD, "otp_code": totp(secret)})
    print(f"2FA disabled: {disable['status']}")


if __name__ == "__main__":
    main()
