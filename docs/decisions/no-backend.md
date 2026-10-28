---
type: Decision Record
title: No own backend
description: Vestigia talks only to servers the user configured (Dawarich, upload targets) and the OSM tile server.
tags: [decision, architecture, backend, privacy]
generated: { by: claude-code/2.1.311, at: 2026-10-27T16:30:00Z }
---

# Status

Accepted (2026-10-27).

# Context

The user already runs a Dawarich server. Location history is among the
most sensitive personal data.

# Decision

No server component and no third-party service: history and settings
come from the configured Dawarich server, uploads go to it or to an
upload target the user entered; map tiles come from OSM.
No analytics, no crash reporting service.

# Consequences

- Features need a Dawarich endpoint or happen on the phone.
- Search for places (if added) must use the Dawarich server or a
  service the user chooses, not a fixed third party.
