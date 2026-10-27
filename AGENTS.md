@../phosh-toolkit/AGENTS.md

# Vestigia

Location history and tracking app for Phosh, a client for a
self-hosted [Dawarich](https://dawarich.app/) server. Two jobs: show the
user's history (tracks, visits, stats) on a map, and record the phone's
position and upload it to the server. The shared rules in
../phosh-toolkit/AGENTS.md apply as well.

- App id: `de.nexumia.Vestigia`.
- Plan: work items are [issues](https://github.com/nexumia-de/vestigia/issues)
  in [milestones](https://github.com/nexumia-de/vestigia/milestones);
  goals per milestone are in [docs/roadmap.md](docs/roadmap.md). Work on
  the issues of the current milestone first; do not start later
  milestones without asking.
- The Dawarich API and its open questions:
  [docs/dawarich-api.md](docs/dawarich-api.md). Verify every unverified
  fact there against a real server (or the Dawarich source at a recorded
  version) before building on it, and record the result in that file.
- The app talks only to the user's Dawarich server and to the OSM tile
  server; there is no own backend.
- The API key is a password: keep it in the Secret portal (libsecret),
  never in a settings file, a log line or a URL. Send it as
  `Authorization: Bearer <key>`, never as `?api_key=`.
- Location data is personal data: no analytics, no third-party
  services, no upload anywhere but the user's own server.
- Never use Dawarich's logo or present the app as official. "Dawarich"
  may appear only to say what the app works with ("for Dawarich").
- Send a descriptive `User-Agent` (`Vestigia/<version> (+repo URL)`)
  with every HTTP request and cache map tiles; OSM tile usage policy
  requires both.
- The cloud dev environment needs these hosts allowed:
  [docs/dev-environment.md](docs/dev-environment.md).
