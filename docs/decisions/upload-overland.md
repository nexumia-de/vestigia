---
type: Decision Record
title: Overland batches for uploads
description: Proposed - recorded points go to /api/v1/overland/batches in groups from an on-disk queue, not one by one.
tags: [decision, upload, tracking, api]
generated: { by: claude-code/2.1.311, at: 2026-10-27T16:30:00Z }
---

# Status

Proposed (2026-10-27); to be confirmed with a real server in M0
(duplicates on retry, largest batch).

# Context

Dawarich ingests points through OwnTracks (one point per request),
Overland (batches) and Traccar ([Dawarich API](../dawarich-api.md)). A
phone is often offline and should wake the radio as rarely as possible.

# Decision

Queue points in SQLite and upload them as Overland batches of
`batch_size` points (server setting, 1–1000).

# Consequences

- One request per batch instead of per point: fewer radio wake-ups.
- A `422` rejects the whole batch; the uploader splits it to isolate the
  bad point.
- If the server does not deduplicate, a retry after a lost answer can
  duplicate a batch; M0 checks this.
