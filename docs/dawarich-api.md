---
type: Reference
title: Dawarich API
description: The Dawarich REST endpoints Vestigia uses for login, history, tracking settings and uploads, what was verified in the source and what is still open.
resource: https://github.com/Freika/dawarich
tags: [api, dawarich, data, upload, auth]
generated: { by: claude-code/2.1.311, at: 2026-11-22T07:00:00Z }
sources:
  - id: swagger
    title: Dawarich OpenAPI description (swagger/v1/swagger.yaml, 1.18.1, commit 60941b3)
    url: https://github.com/Freika/dawarich/blob/60941b330525af23207c380b7cec788e46d04822/swagger/v1/swagger.yaml
  - id: routes
    title: Dawarich routes (config/routes.rb, commit 60941b3)
    url: https://github.com/Freika/dawarich/blob/60941b330525af23207c380b7cec788e46d04822/config/routes.rb
  - id: apictl
    title: Dawarich ApiController (app/controllers/api_controller.rb, commit 60941b3)
    url: https://github.com/Freika/dawarich/blob/60941b330525af23207c380b7cec788e46d04822/app/controllers/api_controller.rb
  - id: overland
    title: Overland batches controller (commit 60941b3)
    url: https://github.com/Freika/dawarich/blob/60941b330525af23207c380b7cec788e46d04822/app/controllers/api/v1/overland/batches_controller.rb
  - id: points
    title: Points controller (commit 60941b3)
    url: https://github.com/Freika/dawarich/blob/60941b330525af23207c380b7cec788e46d04822/app/controllers/api/v1/points_controller.rb
  - id: mobile
    title: Mobile settings controller (commit 60941b3)
    url: https://github.com/Freika/dawarich/blob/60941b330525af23207c380b7cec788e46d04822/app/controllers/api/v1/settings/mobile_controller.rb
  - id: docs-tracking
    title: Dawarich docs, Track your location
    url: https://dawarich.app/docs/tutorials/track-your-location
  - id: rel-1101
    title: Dawarich 1.10.1 release notes
    url: https://newreleases.io/project/github/Freika/dawarich/release/1.10.1
  - id: recorded
    title: Answers of a local Dawarich 1.18.1 server recorded on 2026-11-22 (tests/data/dawarich/, dev/dawarich/record.py)
    url: https://github.com/nexumia-de/vestigia/tree/main/tests/data/dawarich
  - id: source-1181
    title: Dawarich 1.18.1 source inside the freikin/dawarich:1.18.1 image (app/jobs/tracks, app/controllers, config/schedule.yml), read 2026-11-22
    url: https://github.com/Freika/dawarich/tree/60941b330525af23207c380b7cec788e46d04822
---

# Status of these facts

Read from the Dawarich source at **1.18.1** (2026-10-26, commit
`60941b3`) on 2026-10-27, smoke-tested the same day against a local
1.18.1 server from `dev/dawarich/` ([dev environment](dev-environment.md)),
and on 2026-11-22 recorded from that server into `tests/data/dawarich/`
with `dev/dawarich/record.py`[^recorded]: one JSON file per answer
(request, status, the headers Vestigia reads, body; API key, password,
2FA secret and challenge token replaced by `REDACTED`). The positions
are those of a real OsmAnd recording that Dawarich ships as a test
fixture (`spec/fixtures/files/gpx/gpx_track_multiple_segments.gpx`,
AGPL-3.0, copied to `tests/data/source/`), uploaded as an Overland
batch; nothing in the recordings is invented. Every running instance
serves its own API description at `/api-docs`[^docs-tracking].

# Authentication

- Every user has one API key (account page in the web UI).
- The server accepts the key as query parameter `api_key` **or** as
  header `Authorization: Bearer <key>`, for every API controller[^apictl].
  Vestigia uses only the header, so the key never appears in URLs, proxy
  or server access logs.
- `POST /api/v1/auth/login` with e-mail and password returns the
  `api_key`; with two-factor authentication enabled it answers `202`
  with a short-lived `challenge_token` to exchange at
  `POST /api/v1/auth/otp_challenge`[^swagger]. So the app can offer
  "log in with e-mail and password" as well as "paste API key".
- `GET /api/v1/health` needs no key and reports the server version[^swagger]
  (header or body: open, see below). `GET /api/v1/users/me` checks the key.

# Reading history

| Endpoint | Returns | Use |
|---|---|---|
| `GET /api/v1/tracks?start_at&end_at&page&per_page` | GeoJSON FeatureCollection of LineStrings, paginated | Day/range view on the map |
| `GET /api/v1/tracks/{id}/points` | Points of one track | Detail, speed/altitude |
| `GET /api/v1/points?start_at&end_at&page&per_page&order` | Raw points, paginated; headers `X-Current-Page`, `X-Total-Pages`[^points] | Fallback when no tracks are computed; editing |
| `GET /api/v1/timeline?start_at&end_at&distance_unit` | Day-by-day visits, tracks and summary | Timeline sidebar |
| `GET /api/v1/visits`, `PATCH /api/v1/visits/{id}`, `…/possible_places` | Visits; confirm/decline, pick a place | Visits (M4) |
| `GET /api/v1/stats` | Distance and counts per year/month | Statistics (M4) |
| `GET /api/v1/points/tracked_months` | Months that have data | Calendar marks |
| `GET /api/v1/places`, `…/nearby` | Saved places | Markers |
| `GET /api/v1/countries/visited`, `…/visited_cities` | Countries and cities | Statistics (M4) |
| `GET /api/v1/maps/hexagons`, `…/fog` | Hexagon density, "fog of war" | Extras (M5) |
| `GET /api/v1/tiles/tracks/{z}/{x}/{y}.mvt` | Vector tiles of all tracks[^routes] | Option for long ranges, see open questions |

Many read endpoints take `mask_privacy_zones` to leave out data inside
the user's privacy zones[^swagger]; Vestigia sets it whenever the result
could end up in a screenshot or share.

# Tracking settings

`GET`/`PATCH /api/v1/settings/mobile` stores the tracking settings of
the mobile apps on the server: `tracking_mode` (`precise` or
`significant`), `distance_filter`, `time_filter`, `accuracy`,
`track_break`, `tracking_visits`, `auto_start`, `upload_automatically`,
`upload_all_on_tracking_stop`, `batch_size`, plus `updated_at`[^swagger].
Vestigia reads and writes these instead of keeping its own copy, so the
settings are the same on every device of the user. The server clamps
numbers to `distance_filter` 1–10000, `time_filter` 1–3600,
`track_break` 1–1440, `accuracy` 1–6 and `batch_size` 1–1000, and
ignores an unknown `tracking_mode`[^mobile]. Units are not documented:
probably metres, seconds and minutes, and `accuracy` an index into the
mobile platforms' accuracy levels (open question).

# Uploading points

Three ingest endpoints exist: OwnTracks (`/api/v1/owntracks/points`,
one point per request), Overland (`/api/v1/overland/batches`, many
points per request) and Traccar (`/api/v1/traccar/points`)[^routes].
`/api/v1/points` for writes is deprecated in favour of the OwnTracks
route[^docs-tracking]. With a Dawarich account Vestigia uses **Overland batches**, because it
queues points while offline and uploads them in groups; the tracker
itself only speaks standard protocols
([standard protocols](decisions/upload-protocols.md), [tracking](tracking.md)).

Overland batch body[^swagger][^overland]:

```json
{"locations": [
  {"type": "Feature",
   "geometry": {"type": "Point", "coordinates": [13.356718, 52.502397]},
   "properties": {"timestamp": "2026-10-27T15:00:00Z",
                  "horizontal_accuracy": 8, "altitude": 40, "speed": 1.2}}
]}
```

- `timestamp` is ISO 8601 or Unix seconds; other optional properties:
  `vertical_accuracy`, `speed`, `motion`, `activity`,
  `desired_accuracy`, `battery_level`, `battery_state`, `wifi`,
  `device_id`, `unique_id`.
- Answers: `201 {"result":"ok"}`, `422` invalid timestamp (whole batch
  rejected), `401` bad key, `500` on other errors[^overland]. A
  `validate_points_limit` check runs first (plan limit on hosted
  instances; status code open).
- Points at exactly (0, 0) are rejected by every ingest path since
  1.10.1[^rel-1101]; the app drops them before queueing.

# Checked on a local server (1.18.1, 2026-10-27 and 2026-11-22)

With curl (2026-10-27) and `dev/dawarich/record.py` (2026-11-22,
recordings in `tests/data/dawarich/<name>.json`) against
`dev/dawarich/` and a fresh account:

- `GET /api/v1/health` → `200 {"status":"ok"}`, version in the header
  `X-Dawarich-Version: 1.18.1` (also on every authenticated answer)
  (`health`).
- `Authorization: Bearer <key>` works for `users/me`, `points`,
  `settings/mobile`, `overland/batches`, `owntracks/points` and the
  vector tiles `tiles/tracks/{z}/{x}/{y}.mvt` (`200
  application/vnd.mapbox-vector-tile`, `204` for an empty tile, `401`
  without key); a wrong key gives `401` with an empty body
  (`users_me_bad_key`). HTTP basic auth (the OwnTracks app's own method)
  is **not** accepted (`401`, `owntracks_point_basic_auth`); the
  OwnTracks target must send Bearer.
- `POST /api/v1/auth/login` without 2FA → `200` with `user_id`, `email`,
  `api_key`, `status`, `plan` (self-hosted: `pro`), `active_until`
  (`auth_login`); wrong password → `401 {"error":"auth_failed",
  "message":"Invalid email or password"}`. With 2FA → `202
  {"two_factor_required":true,"challenge_token":…,"ttl":300}`
  (`auth_login_2fa`); `POST /api/v1/auth/otp_challenge` with
  `challenge_token` and `otp_code` → the same `200` as a plain login
  (`auth_otp_challenge`), a wrong code → `401 {"error":"auth_failed",
  "message":"Invalid two-factor code"}`.
- `GET /api/v1/users/me` → `{"user": {"id", "email", "settings":
  {"timezone", "maps": {"distance_unit"}, …}, …}}` (`users_me`).
- `GET /api/v1/settings/mobile` on a new account → `{"settings":{},
  "updated_at":null, …}`: no defaults, the app must bring its own.
  `PATCH` with `{"settings":{…}}` clamps (`distance_filter` 50000 →
  10000) and silently drops an unknown `tracking_mode`
  (`settings_mobile_*`).
- Overland batch → `201 {"result":"ok"}`; the **same batch sent twice
  stores the points once** (43 points after two uploads), so retrying
  after a lost answer is safe. A batch of 1001 points was accepted. A bad
  timestamp → `422 {"error": "Timestamp must be a date and time or Unix
  seconds"}`. A (0, 0) point is answered with `201` but not stored. A bad
  key → `401`, empty body.
- On hosted instances the points limit answers **`401`** with
  `{"error":"Points limit exceeded"}` (`ApiController`, not reachable on
  a self-hosted server)[^source-1181]; an uploader must read the body
  before treating a `401` as a rejected key.
- OwnTracks `_type: location` → `200 []`, stored with `tracker_id` from
  `tid`.
- `GET /api/v1/points` sends `X-Current-Page` and `X-Total-Pages`
  (`points_page1`, `points_page3`: 43 points, `per_page=20`, 3 pages);
  each point has `id`, `timestamp` (Unix seconds), `latitude`,
  `longitude` (strings), `altitude`, `accuracy`, `velocity`.
- **Tracks** (open question 5, answered): the real-time job
  `Tracks::RealtimeGenerationJob` only looks at points from the last 6
  hours (`IncrementalGenerator::LOOKBACK_HOURS`); older points wait for
  `Tracks::DailyGenerationJob`, scheduled every 12 hours
  (`config/schedule.yml`)[^source-1181]. Uploaded history therefore has
  no tracks for up to 12 hours. `POST /api/v1/recalculations?year=…`
  queues a rebuild (`202`; `409` while one runs); here it produced the
  track within 10 seconds (`tracks_before_recalculation`, `tracks`).
  Points recorded live by Vestigia are recent and get tracks about 45 s
  after upload. The day view falls back to points when a day has none.
- `GET /api/v1/tracks` → GeoJSON `FeatureCollection` of `LineString`s
  with `properties` `id`, `start_at`, `end_at`, `distance` (m),
  `avg_speed`, `duration`, … and the pagination headers (`tracks`).
  A stop of two minutes (the recording's first segment) does not become
  a track.
- `GET /api/v1/timeline` → `{"days": [{"date", "summary":
  {"total_distance", "distance_unit", "places_visited",
  "time_moving_minutes", "time_stationary_minutes", …}, "bounds":
  {"sw_lat", "sw_lng", "ne_lat", "ne_lng"}, "entries": [visit or
  journey]}]}`; times carry the user's time zone (`timeline`,
  `timeline_with_visit`).
- Visits: a two-minute stop is below automatic visit detection, so the
  recorder creates one through `POST /api/v1/visits` (status
  `suggested`) at the stop's position and time. `PATCH
  /api/v1/visits/{id}` with `name` or `status` answers the whole visit;
  after `declined` the visit **disappears**: it is no longer listed and
  a further `PATCH` answers `404` (`visit_decline`,
  `visits_after_decline`, `visit_suggest_again`). Declining cannot be
  undone through the API, so the app asks before declining.
- `GET /api/v1/stats`, `/api/v1/points/tracked_months` (`[{"year":
  2024, "months": ["Apr"]}]`), `/api/v1/countries/visited` and
  `/visited_cities` answer as recorded; countries and cities stay empty
  without reverse geocoding (`STORE_GEODATA=false` on the dev server).

# Open questions

1. ~~Record answers for all endpoints above~~ Done 2026-11-22.
2. ~~Is a re-sent batch deduplicated?~~ Yes (local server, 2026-10-27,
   again 2026-11-22).
3. ~~Largest batch, points limit~~: 1001 points accepted; the limit
   answers `401` "Points limit exceeded" (source). Vestigia sends at
   most `batch_size` (≤ 1000, the server's clamp).
4. Units of `distance_filter`, `time_filter`, `accuracy`, `track_break`
   are not stated in the source (only the clamps). Vestigia shows them
   as metres, seconds, an accuracy level 1–6 and minutes, which fits the
   ranges; to be compared with the official app by the owner
   ([owner checks](owner-checks.md)).
5. ~~Why no tracks?~~ 6-hour look-back of the real-time job, see above.
6. MVT tiles accept the Bearer header (2026-11-22); whether libshumate
   should draw them is decided with the range view (M4).
7. ~~Oldest supported version~~: 1.18.1, the version the answers were
   recorded from ([decision](decisions/minimum-server-version.md)).

[^swagger]: Dawarich OpenAPI description (swagger/v1/swagger.yaml, 1.18.1, commit 60941b3)
[^routes]: Dawarich routes (config/routes.rb, commit 60941b3)
[^apictl]: Dawarich ApiController (app/controllers/api_controller.rb, commit 60941b3)
[^overland]: Overland batches controller (commit 60941b3)
[^points]: Points controller (commit 60941b3)
[^mobile]: Mobile settings controller (commit 60941b3)
[^docs-tracking]: Dawarich docs, Track your location
[^rel-1101]: Dawarich 1.10.1 release notes
[^recorded]: Answers of a local Dawarich 1.18.1 server recorded on 2026-11-22
[^source-1181]: Dawarich 1.18.1 source inside the freikin/dawarich:1.18.1 image
