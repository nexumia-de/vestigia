---
type: Reference
title: Bundled dependencies
description: Every module the Flatpak bundles (protobuf-c, libshumate, phosh-toolkit's package) with pinned version, licence and licence files; everything else comes from the GNOME runtime.
tags: [dependencies, licensing, flatpak]
generated: { by: claude-code/2.1.330, at: 2026-11-22T09:00:00Z }
sources:
  - id: protobuf-c
    resource: https://github.com/protobuf-c/protobuf-c/releases/download/v1.5.2/protobuf-c-1.5.2.tar.gz
    title: protobuf-c 1.5.2 tarball (LICENSE)
  - id: libshumate
    resource: https://download.gnome.org/sources/libshumate/1.7/libshumate-1.7.0.tar.xz
    title: libshumate 1.7.0 tarball (COPYING, meson.build)
  - id: toolkit
    resource: https://github.com/nexumia-de/phosh-toolkit/tree/v0.7.0
    title: phosh-toolkit v0.7.0 (LICENSE, flatpak/libshumate.yml)
---

# Rules

The shared rules are in
[../../phosh-toolkit/docs/licensing.md](../../phosh-toolkit/docs/licensing.md).
CI fails if a module of `de.nexumia.Vestigia.yml` is missing here or
installs no licence files.

# Modules

| Module | Version | Licence | Licence files | Updates |
|---|---|---|---|---|
| `protobuf-c` | 1.5.2 | BSD-2-Clause[^protobuf-c] | `LICENSE` → `/app/share/licenses/<app id>/protobuf-c/` | in phosh-toolkit (`flatpak/libshumate.yml`) |
| `libshumate` | 1.7.0 | LGPL-2.1-or-later[^libshumate] | `COPYING` → `/app/share/licenses/<app id>/libshumate/` | in phosh-toolkit (`flatpak/libshumate.yml`) |
| `phosh-toolkit` | tag `v0.7.0` (commit `13275a7`) | GPL-3.0-or-later[^toolkit] (own code, same author) | `LICENSE` → `/app/share/licenses/<app id>/phosh-toolkit/` | git tag checker |

protobuf-c is only there because libshumate needs it for vector tiles.
Both come from the toolkit's shared module file
`toolkit/flatpak/libshumate.yml`, included through the git submodule
`toolkit/` at the same tag as the `phosh-toolkit` module (a test checks
that the two agree); their versions are kept current in phosh-toolkit,
not here ([decision](decisions/map-libshumate.md)). libshumate is LGPL;
CI publishes the source bundle with each release.

Only `lib/phosh_toolkit/` is installed; Vestigia uses `settings`
(`JsonStore`, `app_dir`), `style` (light/dark), `keyring`, `http`,
`tasks`, `location` (own position through the location portal) and
`testing`
([shared code](../../phosh-toolkit/docs/shared-connection.md#used-by)).
GPL-3.0-or-later code may be combined with Vestigia's AGPL-3.0-or-later
(section 13 of both licences).

# From the runtime (not bundled)

`org.gnome.Platform//51` provides Python 3, PyGObject, GTK 4,
libadwaita, libsoup 3, libsecret and libportal.

# Not used

No code or assets from Dawarich (AGPL-3.0); its API facts come from its
source ([Dawarich API](dawarich-api.md)).

[^protobuf-c]: protobuf-c 1.5.2 tarball (LICENSE)
[^libshumate]: libshumate 1.7.0 tarball (COPYING, meson.build)
[^toolkit]: phosh-toolkit v0.7.0 (LICENSE, flatpak/libshumate.yml)
