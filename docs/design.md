---
type: Concept
title: Visual design
description: Stock libadwaita with Vestigia's track-violet accent, why violet, the screens at 360 px and on the desktop, and the review checklist.
tags: [design, accent, adaptive, libadwaita]
resource: ../vestigia/style.css
generated: { by: claude-code/2.1.326, at: 2026-11-16T23:59:00Z }
sources:
  - id: accents
    resource: ../../phosh-toolkit/docs/decisions/app-accent-colours.md
    title: phosh-toolkit decision "One accent colour per app"
---

Vestigia follows the toolkit's [visual design](../../phosh-toolkit/docs/design.md)
and [adaptive UI](../../phosh-toolkit/docs/adaptive-libadwaita.md) rules.

# Accent

Track violet `#6741d9` with white text (contrast 6.3:1), set only
through `--accent-bg-color`/`--accent-fg-color` in `vestigia/style.css`
(plus `@define-color` for libadwaita 1.5 hosts)[^accents]. Light and
dark follow the system; Preferences → Appearance → Style offers Follow
System / Light / Dark (`phosh_toolkit.style`). The metainfo branding
colours are `#ddd3f7` (light) and `#33206e` (dark).

Why violet (chosen 2026-11-16 for the scaffold):

- Distinct from the other apps: Jukebox (Nauta) teal `#127a8a`, Home
  Cinema (Ephyra) Jellyfin blue `#00a4dc`, Watch Health (Pulsus) pulse
  red `#c6345a`; Weather Radar (Cirro) and Nuntius set no own accent
  (checked in their style sheets on 2026-11-16).
- The accent will also draw the track on the map (M1). OSM's standard
  tiles use green (parks, woods), blue (water), orange and yellow
  (roads) and red (motorways, POIs); a saturated violet line stands out
  against all of them.

# Screens

| Screen | Narrow (≤ 600 sp) | Wide |
|---|---|---|
| Connect to Dawarich (no account) | `AdwPreferencesPage`: server address; log in with e-mail and password (pill "Log In", suggested) or paste the API key ("Use Key"); errors in an `AdwBanner`; scrolls for the on-screen keyboard, nothing focused when it opens | same, centred column |
| Day (account saved) | OSM map filling the page with the day's tracks (accent line over a casing in the accent's text colour) and visits as markers, fitted to the day (again after a resize until the user moves the map); bottom bar within thumb reach: Previous Day, date button with a calendar popover, Next Day (off for today); header: title with the day as subtitle, menu; "Show My Location" as a round OSD button bottom right | same |
| Day without data | `AdwStatusPage` "No Data on This Day" instead of the map; the bottom bar stays | same |
| Day not loaded | `AdwStatusPage` "Server Unreachable" (no saved copy) or "Day Not Loaded" with the reason, both with Retry | same |
| Key rejected (`401`) | Back to Connect to Dawarich with the banner "The server rejected the API key. Log in again."; the address stays, the key is removed | same |
| Server too old | `AdwBanner` on the day page with the version found and the one needed | same |
| Recording | Record button in the header (red while recording), `AdwBanner` with the tracker's status and Stop, today's own points as a live line in `--accent-color`; an empty today shows the map instead of "No Data" | same |
| Day offline | The saved copy with an `AdwBanner` "Offline: showing the saved copy" and Retry | same |
| Day Summary (sidebar of the day) | `AdwOverlaySplitView` sidebar with its own header: Summary (distance, time moving, places visited as property rows) and Visits (name, local times; tap centres the map). Below 600 sp it overlays the map, starts hidden and opens with the header's sidebar button; not a nested navigation split view (one navigation view per window) | beside the map, shown |
| Visit (pushed from the sidebar) | Name (entry row with apply), time, status, "Show on Map"; Place: the server's suggestions as a choice list; pills "Confirm Visit" (suggested) and "Decline Visit" (destructive, at the end, away from the thumb). Every change has an Undo toast; a decline is sent only when its toast closes | same |
| Statistics (pushed, main menu) | All-time totals; year chooser; distance per month as rows with the number (`numeric`) and a level bar in the accent colour (never colour alone); countries and cities of that year, or why there are none | same |
| Two-Factor Code (pushed) | One entry row and "Verify" | same |
| Preferences | `AdwPreferencesDialog`, page General: Account (e-mail, server, "Log Out" with Undo toast), Appearance → Style; page Tracking: Recording (mode, distance, interval, accuracy limit as spin rows), Upload (where to, automatic, batch size), Other Server (shown only for it: protocol, address, log-in method, user, token or password), In the Background (keep the phone awake while tracking, start at login), On This Phone (keep days, same settings on every device) | same |

Every page is pushed onto one `AdwNavigationView`. The app icon (a
trail of steps across a map to a place marker) and its symbolic variant
are drawn for Vestigia, AGPL like the app; no Dawarich logo.

# Review checklist

The toolkit's checklist, and for Vestigia: no horizontal scrolling at
360 px, icon-only buttons (menu) have tooltips and labels, "Dawarich"
only to say what the app connects to, never as the app's name.

[^accents]: phosh-toolkit decision "One accent colour per app"
