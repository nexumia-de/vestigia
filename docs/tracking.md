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
4. **Uploader** (`vestigia/tracker/uploader.py`, `target.py`,
   `protocols.py`, no GTK): knows nothing about Dawarich; it sends to an
   upload target (URL, protocol, Bearer / basic / no auth, secret in the
   keyring). With a Dawarich account the target is filled in from it
   (`vestigia/api/upload_target.py`: `/api/v1/overland/batches`, the
   account key as Bearer) unless the user enters another one.
   - Overland: up to `batch_size` (1–1000) points per POST
     `{"locations": [...]}`, marked uploaded only after
     `{"result":"ok"}`; any other 2xx is not a confirmation.
   - OwnTracks HTTP: one `_type: location` per POST, any 2xx counts;
     `X-Limit-U`/`X-Limit-D` name user and device for the OwnTracks
     Recorder, which answers `200 []` even to incomplete or invalid
     bodies (recorded from Recorder 1.0.7 in `tests/data/owntracks/`).
   - `400`/`422`: the batch is split in halves until the bad point is
     found; it is parked for that target and the rest goes on.
   - `401`: the run stops and the status says the target rejected the
     credentials (on a hosted Dawarich also its points limit); no retry
     until the target or key changes.
   - Network and server errors: the run stops, the next one follows
     after 30 s, doubling up to an hour (`backoff.py`), or at once when
     `GNetworkMonitor` reports the network back (`scheduler.py`).
   - A retry after a lost answer re-sends the batch: safe with
     Dawarich, which stores a re-sent batch once (recorded, issue 2).
5. **Service and status** (`vestigia/tracking/service.py`, owned by the
   application): record button in the day page's header (Ctrl+R,
   `app.toggle-tracking`; red while recording, tooltip and accessible
   label "Start/Stop Tracking"), an `AdwBanner` while recording
   ("Recording · 12 waiting · uploaded 10:14", or the upload or portal
   error) with Stop. Uploads run when `batch_size` points wait, every 5
   minutes, and when tracking stops (also with automatic upload off).
   Today's points from the store are drawn live over the day in the
   accent colour; the map follows them while the server has nothing for
   today. Tracking that was on is remembered in `tracking.json` (resumed
   in M3).
6. **GPX export** (`vestigia/tracker/gpx.py`, `vestigia/tracking/export.py`):
   main menu → "Export Day as GPX…" writes the points this phone
   recorded on the shown day as GPX 1.1: one track, a new segment after
   a pause of 30 minutes, `<ele>` and `<time>` where known, the accuracy
   in the extension `vestigia:accuracy` (namespace
   `https://github.com/nexumia-de/vestigia/gpx/1`; GPX has no accuracy
   field and `<hdop>` is no distance). Saved through `Gtk.FileDialog`,
   i.e. the file chooser portal in the Flatpak. Works without any
   server. Tests validate the output against the GPX 1.1 schema with
   `xmllint`; the schema is downloaded (CI step, or the `curl` line in
   `tests/test_gpx.py`), not committed, because it states no licence.

# Settings

`$XDG_CONFIG_HOME/vestigia/tracking.json` (`vestigia/tracker/config.py`):
mode (precise / significant moves), distance (m), interval (s), accuracy
limit (m), batch size, upload automatically, where points go (the
Dawarich account, another Overland or OwnTracks server with token or
user name and password in the keyring, or only this phone), keep time
(days). Preferences → Tracking edits them (`vestigia/tracking/settings_page.py`).

With a Dawarich account and "Same Settings on Every Device" on (the
default), mode, distance, interval, batch size and automatic upload are
shared through `/api/v1/settings/mobile` (`vestigia/api/mobile_settings.py`,
`vestigia/tracking/sync.py`): when the page opens the server's values
win; a new account (empty settings) gets the local ones; every change is
sent once the user stops editing for a second. The server's clamps
apply (distance 1–10000, interval 1–3600, batch 1–1000). Its `accuracy`
(a level 1–6) and `track_break` have no documented meaning and stay
unsynced; the units Vestigia assumes (metres, seconds) are on the
[owner checks](owner-checks.md).

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
