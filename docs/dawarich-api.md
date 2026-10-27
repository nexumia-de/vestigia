---
type: Reference
title: Dawarich API
description: The Dawarich REST endpoints Vestigia uses for login, history, tracking settings and uploads, what was verified in the source and what is still open.
resource: https://github.com/Freika/dawarich
tags: [api, dawarich, data, upload, auth]
generated: { by: claude-code/2.1.311, at: 2026-10-27T16:30:00Z }
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
---

# Status of these facts

Read from the Dawarich source at **1.18.1** (2026-10-26, commit
`60941b3`) on 2026-10-27. **Not yet checked against a running server**;
issue "Record real API answers" in M0 does that and stores the answers in
`tests/data/`. Every running instance serves its own API description at
`/api-docs`[^docs-tracking].

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

# Open questions

1. Answers and status codes of a real server for all endpoints above
   (M0 recording).
2. Is a re-sent batch deduplicated (same timestamp and position)? This
   decides whether the uploader may retry after a timeout without
   creating duplicates.
3. Largest batch the server accepts; response of the points limit.
4. Units of `distance_filter`, `time_filter`, `accuracy`,
   `track_break`; behaviour of `significant` mode in the official app.
5. When are tracks computed from new points (immediately or by a job)?
   The day view must handle "points but no tracks yet".
6. Do the MVT tile endpoints accept the Bearer header, and can libshumate's
   vector renderer draw them? Relevant for multi-month ranges.
7. Oldest server version Vestigia supports; how `/api/v1/health` reports
   the version.

[^swagger]: Dawarich OpenAPI description (swagger/v1/swagger.yaml, 1.18.1, commit 60941b3)
[^routes]: Dawarich routes (config/routes.rb, commit 60941b3)
[^apictl]: Dawarich ApiController (app/controllers/api_controller.rb, commit 60941b3)
[^overland]: Overland batches controller (commit 60941b3)
[^points]: Points controller (commit 60941b3)
[^mobile]: Mobile settings controller (commit 60941b3)
[^docs-tracking]: Dawarich docs, Track your location
[^rel-1101]: Dawarich 1.10.1 release notes
