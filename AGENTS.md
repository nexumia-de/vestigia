@../phosh-toolkit/agents/core.md
@../phosh-toolkit/agents/gtk-app.md

# Vestigia

Location history and tracking app for Phosh, a client for a
self-hosted [Dawarich](https://dawarich.app/) server. Two jobs: show the
user's history (tracks, visits, stats) on a map, and record the phone's
position and upload it to that server or to any Overland or OwnTracks
receiver.

- App id: `de.nexumia.Vestigia`. Visible name: **Travel Log** (chosen by
  the owner on 2026-11-06, [decision](docs/decisions/app-name.md)); the
  code name Vestigia stays for the repository, app id, package, docs and
  `User-Agent`.
- Plan: [milestones](https://github.com/nexumia-de/vestigia/milestones); goals in [docs/roadmap.md](docs/roadmap.md).
- The Dawarich API and its open questions:
  [docs/dawarich-api.md](docs/dawarich-api.md). Verify every unverified
  fact there against a real server (or the Dawarich source at a recorded
  version) before building on it, and record the result in that file.
- The app talks only to servers the user configured (Dawarich, upload
  targets) and to the OSM tile server; there is no own backend.
- The tracker (filter, store, uploader) speaks only standard protocols
  (Overland, OwnTracks HTTP, GPX export) and has no Dawarich-specific
  code; Dawarich specifics live in the API client
  ([docs/decisions/upload-protocols.md](docs/decisions/upload-protocols.md)).
- The API key is a password: keep it in the Secret portal (libsecret),
  never in a settings file, a log line or a URL. Send it as
  `Authorization: Bearer <key>`, never as `?api_key=`.
- Location data is personal data: no analytics, no third-party
  services, no upload anywhere but the servers the user configured.
- Never use Dawarich's logo or present the app as official. "Dawarich"
  may appear only to say what the app works with ("for Dawarich").
- Send a descriptive `User-Agent` (`Vestigia/<version> (+repo URL)`)
  with every HTTP request and cache map tiles; OSM tile usage policy
  requires both.
- The cloud dev environment needs these hosts allowed:
  [docs/dev-environment.md](docs/dev-environment.md).
