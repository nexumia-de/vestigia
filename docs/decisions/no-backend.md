---
type: Decision Record
title: No own backend
description: Vestigia talks only to the user's own Dawarich server and the OSM tile server.
tags: [decision, architecture, backend, privacy]
generated: { by: claude-code/2.1.311, at: 2026-10-27T16:30:00Z }
---

# Status

Accepted (2026-10-27).

# Context

The user already runs a Dawarich server. Location history is among the
most sensitive personal data.

# Decision

No server component and no third-party service: history, settings and
uploads go to the configured Dawarich server; map tiles come from OSM.
No analytics, no crash reporting service.

# Consequences

- Features need a Dawarich endpoint or happen on the phone.
- Search for places (if added) must use the Dawarich server or a
  service the user chooses, not a fixed third party.
