---
type: Decision Record
title: Tracking in the background on Phosh
description: While tracking, the app holds itself without a window, inhibits suspend through the Inhibit portal (on by default, can be switched off), shows a notification with Stop, resumes after a restart, and can start at login through the Background portal; numbers from the phone still to be measured.
tags: [decision, tracking, background, battery, phosh, portal]
generated: { by: claude-code/2.1.330, at: 2026-11-22T13:00:00Z }
sources:
  - id: portal-inhibit
    title: XDG Desktop Portal, Inhibit
    url: https://flatpak.github.io/xdg-desktop-portal/docs/doc-org.freedesktop.portal.Inhibit.html
  - id: portal-background
    title: XDG Desktop Portal, Background
    url: https://flatpak.github.io/xdg-desktop-portal/docs/doc-org.freedesktop.portal.Background.html
  - id: gapplication
    title: GApplication hold/release and GtkApplication inhibit (GTK 4 API)
    url: https://docs.gtk.org/gtk4/method.Application.inhibit.html
---

# Status

Accepted (2026-11-22) by best practice during the issue clean-up,
without measurements on the phone; issue 18 asked for measurements
first. The design does not depend on their outcome except for the
default of "Keep the phone awake"; the measurements are on the
[owner checks](../owner-checks.md) and may change that default.

# Context

A tracker is only useful if it records with the window closed and the
screen off ([tracking](../tracking.md)). Phosh phones suspend soon after
the screen turns off; a suspended phone delivers no fixes. Ways to stay
alive on a Linux phone without root are the portals: Inhibit (block
suspend)[^portal-inhibit] and Background (run without a window, start
at login)[^portal-background]. Android and iOS trackers keep a
foreground service with a permanent notification; users expect to see
that recording is on and to stop it in one tap.

# Decision

1. **No window needed**: while tracking, the application calls
   `GApplication.hold()`; closing the window keeps it running, opening
   the app again shows the live state. Stopping releases the hold.
2. **Suspend**: while tracking, `GtkApplication.inhibit(SUSPEND)` (the
   Inhibit portal in the Flatpak)[^gapplication] with the reason
   "Recording your location". Setting "Keep the phone awake while
   tracking", **on by default**: without it a suspended phone records
   nothing, which users would read as a bug. Turning it off saves power
   and leaves gaps. The screen may still turn off (no IDLE inhibit).
3. **Visible**: a notification "Recording your location" with the
   status line and a **Stop** button (`app.stop-tracking`), replaced on
   every change and withdrawn on stop. Phosh also shows its own location
   indicator while GeoClue is in use.
4. **Restart**: `tracking.json` remembers that tracking was on; the
   next start (also `vestigia --background` at login) resumes it.
5. **Login**: setting "Start at Login", off by default, asks the
   Background portal for autostart with `vestigia --background`, which
   starts without a window and resumes tracking if it was on.
6. **Power**: significant mode (street-level accuracy, 100 m) is the
   documented choice for long days; precise mode keeps GNSS on.

# Consequences

- Battery drain while tracking with the phone awake is the price of no
  gaps; to be measured (issue 21 on the owner checks).
- Whether Phosh shows the Background portal's dialog and honours
  autostart is unchecked; if it does not, "Start at Login" has no effect
  and the app says nothing worse than that.
- `phosh_toolkit.location` needs a parent window; without one (started
  at login) Vestigia passes none to libportal (owner checks: a toolkit
  option for that).

[^portal-inhibit]: XDG Desktop Portal, Inhibit
[^portal-background]: XDG Desktop Portal, Background
[^gapplication]: GApplication hold/release and GtkApplication inhibit (GTK 4 API)
