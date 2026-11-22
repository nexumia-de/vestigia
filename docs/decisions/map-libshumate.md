---
type: Decision Record
title: libshumate as map widget
description: The map is a libshumate view with OSM raster tiles; tracks are path layers, visits and places marker layers.
tags: [decision, map, libshumate, osm]
generated: { by: claude-code/2.1.311, at: 2026-10-27T16:30:00Z }
---

# Status

Accepted (2026-10-27), following Cirro's
[map decision](https://github.com/nexumia-de/cirro/blob/main/docs/decisions/map-libshumate.md).

# Context

Vestigia needs a pannable, pinch-zoomable map in GTK 4 that draws
lines and markers. Cirro already builds libshumate 1.7.0 in its Flatpak
and has measured it on the phone. A web view with the Dawarich web UI
or Leaflet would pull WebKitGTK into the Flatpak and feel non-native.

# Decision

Use `Shumate.SimpleMap` with an OSM raster renderer; tracks are
`Shumate.PathLayer`s, visits, places and the own position
`Shumate.MarkerLayer`s. Map setup (tile source, User-Agent, cache,
attribution) is shared with Cirro through phosh-toolkit.

# Consequences

- The Flatpak builds libshumate and protobuf-c like Cirro; the module
  snippets come from the toolkit rather than being copied.
- Long ranges may need Dawarich's vector tiles instead of GeoJSON
  ([Dawarich API](../dawarich-api.md), open question 6).

# Implementation (2026-11-22, issue 6)

`vestigia/map/view.py`: `Shumate.SimpleMap` with an OSM raster source
(`https://tile.openstreetmap.org/{z}/{x}/{y}.png`, attribution
"© OpenStreetMap contributors" linking to the copyright page, as the OSM
tile usage policy asks), `Shumate.set_user_agent()` with Vestigia's
`User-Agent`, and libshumate's built-in tile cache (100 MB in
`$XDG_CACHE_HOME`, files keyed by source). Tracks are two `PathLayer`s
(casing and line) with colours read from `style.css` classes; visits and
the own location are `MarkerLayer`s. The own location comes from
`phosh_toolkit.location` (portal, `EXACT`, 10 m) after a tap on "Show My
Location" (tooltip and accessible label). `VESTIGIA_TILES=off` leaves the
tiles out in tests.

