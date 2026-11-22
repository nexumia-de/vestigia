---
type: Concept
title: Owner checks
description: What only the owner can do - the real phone, the owner's own Dawarich server and account, secrets, other repositories - as one checklist; closed issues point here.
tags: [owner, checklist, planning, device]
generated: { by: claude-code/2.1.330, at: 2026-11-22T07:00:00Z }
---

# Why

On 2026-11-22 every open issue was closed: built and tested in the
cloud container, decided, or reduced to a step that needs the phone,
the owner's Dawarich server or account, a secret or another
repository. Those steps are collected here instead of staying open as
issues ([planning](../../phosh-toolkit/docs/planning.md)). None of them
has been done yet. Tick an item off by deleting it; write results into
the concept file named in the item.

# Checklist

## Real server (issue 2)

- [ ] Optional: run `dev/dawarich/record.py` against your own server
  once (edit `SERVER`, `EMAIL`, `PASSWORD` locally, do not commit them)
  and compare with `tests/data/dawarich/`; differences go to
  [Dawarich API](dawarich-api.md). Do not commit those answers: they
  hold your positions.
- [ ] Open the official Dawarich iOS or Android app's tracking settings
  and note the units it shows for distance filter, time filter,
  accuracy and track break (open question 4 in
  [Dawarich API](dawarich-api.md)).

## Nightly builds on the phone (issue 3)

The workflow side is in place: `.github/workflows/flatpak.yml` builds
Travel Log (Nightly) on every push to `main` and moves the `nightly`
pre-release (the tag exists); the shared repository picks it up.

- [ ] In nexumia-de/phosh-apps, add the line `nexumia-de/vestigia` to
  `apps.txt` (this session has no write access there).
- [ ] Optional: add the secret `PUBLISH_TOKEN` to this repository so
  pushes notify phosh-apps at once instead of with its daily run.
- [ ] On the phone, install *Travel Log (Nightly)* from
  https://flatpak.nexumia.de/ in GNOME Software, start it, and check it
  shows in Phosh's app grid in mobile mode.

## A recorded walk on the phone (issue 17)

Everything up to the portal is tested in the container; the portal,
GeoClue, GNSS and a real network are not.

- [ ] Install the nightly, Preferences → Tracking: keep "Dawarich
  Account", note the settings. Tap the record button, allow the location
  dialog, walk 15–30 minutes, switch mobile data off for part of it
  (the banner should say "waiting for the network"), on again, stop.
- [ ] In the Dawarich web UI: every point arrives once (compare the
  count with the points of that day in Travel Log's GPX export), the
  track looks right; note gaps.
- [ ] The same with "Other Server" → OwnTracks HTTP to an OwnTracks
  Recorder (`dev/owntracks/compose.yml` works on a laptop in the same
  network).
- [ ] Write the results under "Results on the phone" in
  [tracking](tracking.md).

## Background tracking on the phone (issues 18 and 21)

The [decision](decisions/background-tracking.md) was taken without
measurements. On the phone, with the nightly:

- [ ] Start tracking, close the window, let the screen turn off for an
  hour: does the notification stay, do points keep coming (export the
  day as GPX and look for gaps)? Once with "Keep the phone awake while
  tracking" on, once off.
- [ ] Battery per hour (percent at start and end, `upower -d`) for
  precise and significant mode, screen off; write numbers and method
  under "Results on the phone" in [tracking](tracking.md). If the drain
  with the phone kept awake is unacceptable, change the default in
  `vestigia/tracker/config.py` and the decision.
- [ ] Turn "Start at Login" on: does Phosh show the Background portal's
  dialog? After a reboot, does tracking resume without opening the app?

## Toolkit follow-ups (issues 5, 7 and 12)

- [ ] phosh-toolkit (finding of issue 7, possibly the cause of the
  toolkit's unexplained UI test hangs in CI): under Xvfb a visible
  `Gtk.Spinner` keeps the frame clock always ready, so `run_until()`'s
  `iteration(False)` never reaches the idle callbacks that
  `phosh_toolkit.tasks` delivers results with. Vestigia's UI tests set
  `gtk-enable-animations` to false; the toolkit could do the same in
  `testing` or deliver with a higher priority.
- [ ] phosh-toolkit (issue 12): `location.Location` emits latitude,
  longitude and accuracy only, though the portal also sends altitude,
  speed and the fix time; with those in the signal Vestigia's points
  could carry them (Overland `altitude`/`speed`, GPX `<ele>`).
- [ ] phosh-toolkit: give `Keyring` a public way to ask whether a
  secret only lives in memory (Vestigia reads `_memory` in
  `vestigia/secrets.py`); then switch Vestigia to it.
