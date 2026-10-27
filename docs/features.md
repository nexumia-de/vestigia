---
type: Concept
title: Feature inventory
description: What Vestigia does with a Dawarich server, ordered by priority, with the endpoints each feature needs.
tags: [features, scope, dawarich]
generated: { by: claude-code/2.1.311, at: 2026-10-27T16:30:00Z }
---

# Scope

Vestigia is a phone-first client for a Dawarich server: it shows the
user's own history and records new positions. The history view needs
Dawarich; the tracker only uses standard protocols and also works with
other servers or none ([standard protocols](decisions/upload-protocols.md)). It does not replace the
web UI for administration (imports, exports, users, family setup,
webhooks); those stay in the browser.

Priorities: **P1** must have for the first usable release, **P2** next,
**P3** later or optional. Endpoints: [Dawarich API](dawarich-api.md).

| Feature | Prio | Endpoints | Milestone |
|---|---|---|---|
| Connect to a server: URL plus e-mail/password (with 2FA) or API key; key in the Secret portal | P1 | `auth/login`, `auth/otp_challenge`, `health`, `users/me` | M1 |
| Map with the tracks of one day, previous/next day, date picker | P1 | `tracks`, fallback `points` | M1 |
| Day summary: distance, time moving, visits in a sidebar | P1 | `timeline` | M1 |
| Own location on the map | P1 | location portal | M1 |
| Record positions while the app is open, with an offline queue | P1 | `overland/batches` | M2 |
| Upload to any Overland or OwnTracks HTTP server instead of (or without) Dawarich | P1 | – | M2 |
| Export recorded days as GPX | P2 | – | M2 |
| Tracking settings, local or synced with Dawarich's other devices (mode, filters, batch size) | P1 | `settings/mobile` | M2 |
| Tracking status: on/off, points waiting, last upload | P1 | – | M2 |
| Record with the window closed and the screen off, start at login | P1 | Background and Inhibit portals | M3 |
| Visits: confirm, decline, pick or rename the place | P2 | `visits`, `visits/{id}/possible_places`, `places` | M4 |
| Statistics per year and month, countries and cities | P2 | `stats`, `countries/visited`, `countries/visited_cities` | M4 |
| Date ranges and a calendar with days that have data | P2 | `points/tracked_months` | M4 |
| Hexagon density / "fog of war" layer | P3 | `maps/hexagons`, `maps/hexagons/fog` | M5 |
| Photos along a track | P3 | `photos`, `photos/{id}/thumbnail` | M5 |
| Family members' positions | P3 | `families/locations` | M5 |
| Notes on a day or place | P3 | `notes` | backlog |
| Edit or delete points | P3 | `points/{id}`, `points/bulk_destroy` | backlog |
