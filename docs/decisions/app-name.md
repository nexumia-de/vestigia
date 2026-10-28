---
type: Decision Record
title: App name Vestigia
description: The app is called Vestigia (id de.nexumia.Vestigia), not "Dawarich Companion"; "Dawarich" appears only as "for Dawarich".
tags: [decision, name, app-id, repository, trademark]
generated: { by: claude-code/2.1.311, at: 2026-10-27T16:30:00Z }
---

# Status

Accepted (2026-10-27), chosen by the owner from proposals.

# Context

The owner asked for a Dawarich client and suggested "Dawarich
Companion". Dawarich has its own official mobile apps, so an app named
"Dawarich …" in the app grid and the stores would look official, and the
name would be fixed in the app id for good (a changed id is a new app
for Flatpak). Cirro follows the same rule for DWD's names.

# Decision

- Name **Vestigia**, Latin for footprints, traces.
- App id `de.nexumia.Vestigia` ([domain-based names](../../../phosh-toolkit/docs/decisions/domain-names.md)),
  repository `nexumia-de/vestigia`, Python package `vestigia`, command
  `vestigia`, User-Agent
  `Vestigia/<version> (+https://github.com/nexumia-de/vestigia)`.
- Summary "Location history and tracking for Dawarich"; "Dawarich" as a
  keyword in the `.desktop` file and metainfo so search finds it. No
  Dawarich logo; the icon is our own.

# Consequences

- README and About dialog state that the app is independent and not
  affiliated with Dawarich.
