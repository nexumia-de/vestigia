---
type: Decision Record
title: Standard protocols for uploads
description: Proposed - the tracker uploads with the open Overland or OwnTracks HTTP protocols to any URL, Dawarich is one target among others; GPX export works without a server.
tags: [decision, upload, tracking, protocol, gpx]
generated: { by: claude-code/2.1.311, at: 2026-10-27T17:10:00Z }
sources:
  - id: overland
    title: Overland GPS Tracker README (protocol, settings; read 2026-10-27)
    url: https://github.com/aaronpk/Overland-iOS/blob/main/README.md
  - id: owntracks-http
    title: OwnTracks booklet, HTTP mode (commit a0b5542, 2026-10-06)
    url: https://github.com/owntracks/booklet/blob/a0b55428cd4abaa2384babeb96dfa88b58c24fb6/docs/tech/http.md
  - id: owntracks-json
    title: OwnTracks booklet, JSON payloads (commit a0b5542)
    url: https://github.com/owntracks/booklet/blob/a0b55428cd4abaa2384babeb96dfa88b58c24fb6/docs/tech/json.md
  - id: gpx
    title: GPX 1.1 Schema Documentation (topografix.com, proxy 403 on 2026-10-27, not read)
    url: https://www.topografix.com/GPX/1/1/
---

# Status

Proposed (2026-10-27) by the owner's request "build tracking on
standards, not on Dawarich's own API". To be confirmed with real
servers in M0 (duplicates on retry, largest batch).

# Context

Dawarich has no tracking protocol of its own: its ingest endpoints
speak the formats of third-party tracker apps, namely Overland
(batches), OwnTracks (one point per request) and the Traccar Client
JSON format ([Dawarich API](../dawarich-api.md)). Other self-hosted
servers accept the same formats; OwnTracks HTTP mode, for example, is
what the OwnTracks Recorder receives[^owntracks-http]. A tracker tied to
Dawarich's settings and login would be useless to everyone else and to
the owner if they ever change servers. A phone is often offline and
should wake the radio as rarely as possible.

# Decision

1. The tracker (filter, queue, uploader) knows nothing about Dawarich.
   An **upload target** is a URL, a protocol and optional credentials
   (Bearer token or HTTP basic auth).
2. Protocols: **Overland** (default; a POST with
   `{"locations": [GeoJSON points]}`, confirmed by `{"result":"ok"}`,
   which Dawarich sends[^overland]) and **OwnTracks HTTP**
   (`_type: location` JSON[^owntracks-json], one point per POST, HTTP basic auth, any `2xx` counts as received and
   the answer is usually `[]`[^owntracks-http]), for servers that only
   speak OwnTracks. Traccar Client JSON only if a user needs it
   (backlog).
3. When the account in the app is a Dawarich server, the target is
   filled in from it (`/api/v1/overland/batches`, Bearer key), and the
   tracking settings may sync with `/api/v1/settings/mobile`. Without a
   Dawarich account, the settings stay local.
4. **GPX 1.1 export**[^gpx] of recorded days from the local store, so
   tracking is useful without any server and the data can go anywhere.
5. Points stay queued in SQLite until the target confirms them;
   recorded points are kept locally for a configurable time for GPX
   export.

# Consequences

- The tracker can be tested against recorded answers of more than one
  server, and could later become its own app without a rewrite.
- Two upload formats to maintain; both are small and stable.
- A `422` (Dawarich) rejects a whole Overland batch; the uploader splits
  it to isolate the bad point.
- Whether a retry after a lost answer duplicates points depends on the
  server; M0 checks Dawarich.

[^overland]: Overland GPS Tracker README
[^owntracks-http]: OwnTracks booklet, HTTP mode
[^owntracks-json]: OwnTracks booklet, JSON payloads
[^gpx]: GPX 1.1 Schema Documentation
