---
type: Concept
title: Tracking
description: How Vestigia records positions on the phone, filters and queues them, and uploads them with standard protocols (Dawarich or any Overland/OwnTracks server) or exports GPX; the open problems of running in the background on Phosh.
tags: [tracking, location, upload, overland, owntracks, gpx, background, battery, phosh]
generated: { by: claude-code/2.1.330, at: 2026-11-22T12:00:00Z }
sources:
  - id: portal-location
    title: XDG Desktop Portal, Location
    url: https://flatpak.github.io/xdg-desktop-portal/docs/doc-org.freedesktop.portal.Location.html
  - id: portal-background
    title: XDG Desktop Portal, Background
    url: https://flatpak.github.io/xdg-desktop-portal/docs/doc-org.freedesktop.portal.Background.html
  - id: portal-inhibit
    title: XDG Desktop Portal, Inhibit
    url: https://flatpak.github.io/xdg-desktop-portal/docs/doc-org.freedesktop.portal.Inhibit.html
---

# Status

Pipeline built in M2 (2026-11-22) and tested in the cloud container with
the fixes of a real recording and recorded server answers; nothing is
measured on the phone yet ([owner checks](owner-checks.md)). Background
operation is M3 ([roadmap](roadmap.md)).

# Pipeline

```
location portal ──fix──▶ filter ──point──▶ store (SQLite) ──batch──▶ uploader ──▶ upload target
   (GeoClue, GNSS)     distance/time/        on disk,                 Overland or      (Dawarich or any
                       accuracy, (0,0)       survives restart         OwnTracks HTTP   compatible server)
                                                  │
                                                  └──▶ GPX export (no server needed)
```

1. **Source** (`vestigia/tracker/source.py`): the XDG location portal
   (GeoClue behind it) through `phosh_toolkit.location` (toolkit v0.7.0).
   Precise mode asks for `EXACT` accuracy so GeoClue uses the GNSS
   receiver[^portal-location] and lets every move through to the filter;
   significant mode asks for street level and moves of 100 m or more.
   The wrapper reports latitude, longitude and accuracy only; the fix
   gets the arrival time, no altitude or speed (owner checks: a toolkit
   extension would add them).
2. **Filter** (`vestigia/tracker/filter.py`, no GTK): drop (0, 0) and
   invalid coordinates, fixes worse than the accuracy limit (metres),
   fixes not newer than the last kept one, and fixes both closer than
   the distance and younger than the interval since the last kept
   point. Tested on the 43 fixes of a real OsmAnd recording
   (`tests/data/source/`). The settings are local; with a Dawarich
   account they can sync with `/api/v1/settings/mobile`
   ([Dawarich API](dawarich-api.md)).
3. **Store** (`vestigia/tracker/store.py`, no GTK): every kept point is
   written to `$XDG_DATA_HOME/vestigia/points.sqlite` (mode 600, WAL,
   `synchronous=FULL`) before anything else happens, so a crash, a
   reboot or a dead network loses nothing. Uploads are marked per target
   (`uploads` table), points a target refuses are parked per target
   (`parked`), nothing is deleted on upload. Pruning removes points older
   than the keep time (setting, default 30 days) only once the current
   target has them or refused them; without a target, by age alone.
4. **Uploader**: knows nothing about Dawarich; it sends to an upload
   target (URL, protocol, credentials) chosen by the user or filled in
   from the Dawarich account ([standard protocols](decisions/upload-protocols.md)).
   Overland: up to `batch_size` points per request when the network is
   up (`GNetworkMonitor`), marked uploaded only after
   `{"result":"ok"}`; OwnTracks: one point per request, any `2xx`
   counts. It backs off exponentially on errors. A `422` batch is split
   to find and park the bad point instead of blocking the queue.
   Retrying after a lost answer is safe with Dawarich, which stores a
   re-sent batch once ([Dawarich API](dawarich-api.md)); other servers
   may differ.
5. **Status in the UI**: tracking on/off, points waiting, last
   successful upload, last error as an `AdwBanner`.
6. **GPX export**: a day or range from the store as a GPX 1.1 file
   through the file chooser portal.

The pipeline modules (filter, store, uploader, GPX writer) stay free of
GTK so they run in tests with recorded fixes and recorded server answers.

# Background operation on Phosh (open)

The phone is only useful as a tracker if recording continues with the
window closed and the screen off. Known obstacles, all to be checked on
the device:

- **Suspend**: Phosh phones suspend shortly after the screen turns off
  unless something inhibits it. The Inhibit portal can block
  suspend[^portal-inhibit], at a battery cost; without it there are
  gaps. Whether the modem or GNSS can wake the phone is unknown.
- **Running without a window**: a `GApplication` can `hold()` itself
  after the last window closes. Starting at login needs the Background
  portal's autostart[^portal-background]; whether Phosh shows its
  "running in background" permission dialog is unknown.
- **GNSS power**: a permanently open GNSS session drains the battery;
  `significant` mode should use coarser fixes or longer intervals.
- **Indicator**: the user must always see that tracking is on (a
  persistent notification or the location indicator in the top bar).

These choices become a decision record in M3 after measurements on the
phone (issues labelled `on device`).

[^portal-location]: XDG Desktop Portal, Location
[^portal-background]: XDG Desktop Portal, Background
[^portal-inhibit]: XDG Desktop Portal, Inhibit
