---
okf_version: "0.2"
---

# Vestigia knowledge bundle

[Open Knowledge Format](https://github.com/GoogleCloudPlatform/knowledge-catalog/blob/main/okf/SPEC.md)
(OKF v0.2) bundle of this app. Shared Phosh knowledge lives in
[../../phosh-toolkit/docs/index.md](../../phosh-toolkit/docs/index.md).
Change history is in [log.md](log.md).

# Plan

* [Roadmap](roadmap.md) - Goals and exit criteria of the milestones M0–M5; the work items are GitHub issues in those milestones.
* [Feature inventory](features.md) - What the app does with a Dawarich server, by priority and milestone.

# Design

* [Dawarich API](dawarich-api.md) - Endpoints for login, history, tracking settings and uploads; verified in the source and recorded from a local 1.18.1 server.
* [Tracking](tracking.md) - Location portal, filter, SQLite store, uploader with standard protocols, GPX export; open problems of background operation on Phosh.
* [Visual design](design.md) - Stock libadwaita with the track-violet accent and why, the screens, the review checklist.

# Development

* [Development environment](dev-environment.md) - Required hosts and how tests work without a server.
* [Bundled dependencies](dependencies.md) - protobuf-c, libshumate and phosh-toolkit's package in the Flatpak, with licences and licence files.

* [Owner checks](owner-checks.md) - What only the owner can do (phone, own server, secrets, other repositories), as one checklist.

# Decision records

* [Decisions](decisions/index.md) - Name, language, map widget, no own backend, licence, standard upload protocols, oldest server version.
