---
type: Plan
title: Roadmap
description: Goals and exit criteria of the milestones M0–M5, history view first, then tracking; the work items are GitHub issues in the milestones linked here.
tags: [plan, roadmap, milestones]
generated: { by: claude-code/2.1.311, at: 2026-10-27T16:30:00Z }
---

# How the plan is tracked

Work items are [issues](https://github.com/nexumia-de/vestigia/issues),
grouped by [milestones](https://github.com/nexumia-de/vestigia/milestones)
and `area: …` labels; issues without a milestone are the
[backlog](https://github.com/nexumia-de/vestigia/issues?q=is%3Aissue+is%3Aopen+no%3Amilestone).
This file keeps only the goals; never add task checklists here. The
workflow is the toolkit's
[planning with issues and milestones](../../phosh-toolkit/docs/planning.md).

# Principle

Read first, then write. M1 shows the user's existing history from the
server, which is useful on its own and proves the API client, the map
and the account handling. Tracking follows in M2 (app open) and M3
(app closed, screen off), the hardest part on Phosh
([tracking](tracking.md)). Feature priorities:
[feature inventory](features.md).

# M0 – Verify the API and scaffold

[Milestone M0](https://github.com/nexumia-de/vestigia/milestone/1)

**Goal**: an empty but installable app and recorded answers from a real
Dawarich server.

**Exit criteria**: the open questions 1, 2, 5 and 7 in
[Dawarich API](dawarich-api.md) answered from a real server and the
answers stored in `tests/data/`; the app scaffolded from the toolkit
skeleton with metadata, Flatpak manifest (libshumate), CI, ruleset and
tests; nightly builds install on the phone from the shared repository.

# M1 – Connect and show a day

[Milestone M1](https://github.com/nexumia-de/vestigia/milestone/2)

**Goal**: log in to the own server and see where you were on any day.

**Exit criteria**: account setup with e-mail/password (2FA) or API key,
key in the Secret portal; OSM map with attribution, User-Agent and tile
cache from shared toolkit code; tracks of the selected day with
previous/next day and a date picker; day summary and visits in an
`AdwNavigationSplitView` sidebar that collapses on the phone; cached
days open offline; empty, error and offline states; checked at 360×720.

# M2 – Tracking while the app is open

[Milestone M2](https://github.com/nexumia-de/vestigia/milestone/3)

**Goal**: record the phone's position and upload it with a standard
protocol, without losing points when the network is gone.

**Exit criteria**: the [tracking](tracking.md) pipeline (portal, filter,
SQLite store, uploader for Overland and OwnTracks HTTP with back-off)
with tests on recorded fixes and answers; any upload target, filled in
from the Dawarich account by default; local tracking settings, synced
with `/api/v1/settings/mobile` for Dawarich; GPX export; start/stop,
status and the live track on the map; a recorded walk shows up
correctly in the Dawarich web UI and in a second Overland or OwnTracks
receiver.

# M3 – Background tracking on the phone

[Milestone M3](https://github.com/nexumia-de/vestigia/milestone/4)

**Goal**: tracking keeps working with the window closed and the screen
off, at a battery cost that is measured and acceptable.

**Exit criteria**: decision record on background operation (suspend,
autostart, indicator) based on measurements on the phone; gaps and
battery drain per hour recorded in [tracking](tracking.md); tracking
resumes after reboot when it was on.

# M4 – Visits, timeline and statistics

[Milestone M4](https://github.com/nexumia-de/vestigia/milestone/5)

**Goal**: the parts of the Dawarich web UI that are useful on the go.

**Exit criteria**: visits can be confirmed, declined and assigned to a
place; statistics per year/month with countries and cities; date ranges
and a calendar that marks days with data.

# M5 – Extras

[Milestone M5](https://github.com/nexumia-de/vestigia/milestone/6)

**Goal**: richer map layers once the core works well.

**Exit criteria**: hexagon or "fog of war" layer; photos along a track;
family members' positions, each only if the server has the feature
enabled.

# Risks

- **Background tracking on Phosh** may need suspend inhibition and cost
  more battery than users accept; the fallback is "tracking while the
  screen is on" plus honest gaps. Measured in M3.
- **API churn**: Dawarich releases often (1.17 to 1.18.1 within four
  days in October 2026). Pin a minimum server version, test against
  recorded answers, and fail visibly on unknown responses.
- **Large ranges**: GeoJSON for months of tracks can be megabytes on the
  phone; the vector tile endpoints are the way out (open question 6 in
  [Dawarich API](dawarich-api.md)).
- **Personal data**: a bug that logs the key or positions leaks the
  user's movements; review logging and screenshots with recorded demo
  data only.
