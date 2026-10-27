---
type: Playbook
title: Development environment
description: Network hosts and test data needed to develop Vestigia, in the cloud and locally.
tags: [development, network, cloud, testing]
generated: { by: claude-code/2.1.311, at: 2026-10-27T16:30:00Z }
---

# Required hosts

| Host | Used for |
|---|---|
| The owner's Dawarich server | Recording real API answers (M0), manual tests; not known yet, see issue "Record real API answers" |
| `tile.openstreetmap.org` | Base map tiles; answered on 2026-10-27 |
| `dawarich.app` | Dawarich documentation (docs only); proxy `403` on 2026-10-27 |
| `github.com` | Dawarich source (read with git; the session proxy serves anonymous clones of public repositories), Flatpak sources |
| `owntracks.org` | OwnTracks booklet (docs only; read from its GitHub repository instead); proxy `403` on 2026-10-27 |
| `www.topografix.com` | GPX 1.1 schema (docs only); proxy `403` on 2026-10-27 |
| `download.gnome.org` | libshumate source archive for the Flatpak build; answered on 2026-10-27 |

Plus the toolkit's needs (Flathub, apt, GitHub). In a cloud agent
environment the hosts go under the environment's network access
settings (allowed domains).

# Working without a server

- Tests use real answers recorded from a Dawarich server and stored in
  `tests/data/dawarich/`, with the API key, e-mail addresses and exact
  home positions removed (positions shifted, not invented).
- Never replace missing live answers with invented samples.
- A local server for development can run from Dawarich's own Docker
  Compose setup (`docker/` in the Dawarich repository); whether that
  works in the cloud container is open.
