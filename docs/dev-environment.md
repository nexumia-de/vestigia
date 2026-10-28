---
type: Playbook
title: Development environment
description: Network hosts, the local Dawarich server for tests, and how tests work without a server.
tags: [development, network, cloud, testing]
generated: { by: claude-code/2.1.311, at: 2026-10-27T16:30:00Z }
---

# Required hosts

| Host | Used for |
|---|---|
| `registry-1.docker.io`, `auth.docker.io`, `production.cloudflare.docker.com` | Docker images for the local Dawarich server; pulled on 2026-10-27 |
| `tile.openstreetmap.org` | Base map tiles; answered on 2026-10-27 |
| `dawarich.app` | Dawarich documentation (docs only); proxy `403` on 2026-10-27 even after `*.dawarich.app` was allowed: the wildcard does not cover the bare domain |
| `github.com` | Dawarich source (read with git; the session proxy serves anonymous clones of public repositories), Flatpak sources |
| `owntracks.org` | OwnTracks booklet (docs only; read from its GitHub repository instead); proxy `403` on 2026-10-27, also after `*.owntracks.org` was allowed (bare domain) |
| `www.topografix.com` | GPX 1.1 schema (docs only); answered on 2026-10-27 after `*.topografix.com` was allowed |
| `download.gnome.org` | libshumate source archive for the Flatpak build; answered on 2026-10-27 |

Plus the toolkit's needs (Flathub, apt, GitHub). In a cloud agent
environment the hosts go under the environment's network access
settings (allowed domains).

# Working without a server

- Tests use real answers recorded from a Dawarich server and stored in
  `tests/data/dawarich/`, with the API key, e-mail addresses and exact
  home positions removed (positions shifted, not invented).
- Never replace missing live answers with invented samples.

# Local Dawarich server

`dev/dawarich/up.sh` starts Dawarich 1.18.1 with PostGIS and Redis
(images pinned by digest in `dev/dawarich/compose.yml`, adapted from
Dawarich's `docker/docker-compose.yml`), creates the account
`demo@vestigia.test` / `vestigia-demo-password` and prints its API key.
The server listens on `127.0.0.1:3000` only. Secrets are random per
checkout in `dev/dawarich/.env` (git-ignored); 2FA keys are set so
two-factor login can be tested. Stop and wipe with
`docker compose -f dev/dawarich/compose.yml down -v`.

Works in the cloud container (checked 2026-10-27): the Docker daemon is
not running there by default, `up.sh` starts it; the first start pulls
about 1 GB of images and takes about two minutes.
