---
type: Decision Record
title: Week and month ranges with GeoJSON tracks
description: The map shows a day, a week or a month, drawn from /api/v1/tracks (GeoJSON); Dawarich's vector tiles are not used for now, longer ranges are not offered; the calendar marks days with data from one timeline request per month.
tags: [decision, map, history, performance, dawarich]
generated: { by: claude-code/2.1.330, at: 2026-11-22T15:00:00Z }
sources:
  - id: recorded
    title: Recorded answers of Dawarich 1.18.1 (tests/data/dawarich/tracks.json, tracked_months.json, timeline*.json)
    url: https://github.com/nexumia-de/vestigia/tree/main/tests/data/dawarich
  - id: shumate-vector
    title: libshumate 1.7 VectorRenderer (a map source with a MapLibre style, not an overlay layer)
    url: https://gnome.pages.gitlab.gnome.org/libshumate/class.VectorRenderer.html
---

# Status

Accepted (2026-11-22) by best practice during the issue clean-up;
issue 24 asked to measure on the phone first. The measurement is on the
[owner checks](../owner-checks.md); it can lift the month limit or bring
the vector tiles back.

# Context

`/api/v1/tracks` returns a day's or a range's tracks as GeoJSON
LineStrings with already thinned coordinates (27 points for a 37-minute
walk in the recording[^recorded]). Dawarich also serves all tracks as
Mapbox vector tiles (`/api/v1/tiles/tracks/{z}/{x}/{y}.mvt`, Bearer
works, [Dawarich API](../dawarich-api.md)). libshumate draws vector
tiles only as a whole map source with a MapLibre style
(`Shumate.VectorRenderer`)[^shumate-vector]; an overlay over the OSM
raster tiles would need a second map layer with its own style JSON and
would show every track of every time, not those of the chosen range.
`/api/v1/points/tracked_months` names the months with data, not the
days.

# Decision

1. Ranges: **day, week (Monday to Sunday) and month**, chosen in the
   date popover; previous/next move by the range. Tracks come from
   `/api/v1/tracks` for the range (all pages), summary and visits from
   `/api/v1/timeline` for the range. No vector tiles for now.
2. Longer ranges (a year, everything) are not offered: they would need
   the tiles or a server-side simplification; a month of daily walks is
   a few thousand coordinates, which `PathLayer` draws.
3. Raw points are a fallback for single days only (a month of raw
   points can be tens of thousands).
4. Only single days are cached for offline use.
5. Calendar marks: `/api/v1/points/tracked_months` once per page, then
   for a shown month with data one `/api/v1/timeline` request for the
   month; days with entries are marked.

# Consequences

- A user with dense months may wait a few seconds for a month; to be
  measured on the phone.
- If longer ranges are wanted later, the vector tiles with a small
  MapLibre style are the way; the Bearer header already works for them.

[^recorded]: Recorded answers of Dawarich 1.18.1 (tests/data/dawarich/tracks.json, tracked_months.json, timeline*.json)
[^shumate-vector]: libshumate 1.7 VectorRenderer (a map source with a MapLibre style, not an overlay layer)
