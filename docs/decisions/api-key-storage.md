---
type: Decision Record
title: The API key in the Secret portal
description: The Dawarich API key lives only in the keyring (libsecret, Secret portal in the Flatpak); the settings file holds the server address; a locked or missing keyring is shown, never hidden.
tags: [decision, security, keyring, api-key]
generated: { by: claude-code/2.1.330, at: 2026-11-22T08:00:00Z }
sources:
  - id: portal-secret
    title: XDG Desktop Portal, Secret
    url: https://flatpak.github.io/xdg-desktop-portal/docs/doc-org.freedesktop.portal.Secret.html
  - id: keyring
    title: phosh-toolkit lib/phosh_toolkit/keyring.py (v0.7.0)
    url: https://github.com/nexumia-de/phosh-toolkit/blob/v0.7.0/lib/phosh_toolkit/keyring.py
---

# Status

Accepted (2026-11-22, issue 5).

# Context

The API key gives full read and write access to the user's whole
location history. Inside the Flatpak, libsecret talks to the Secret
portal, which stores app secrets encrypted in the user's keyring without
any extra permission[^portal-secret]. On a phone the keyring can be
locked or, on unusual setups, missing.

# Decision

- `vestigia/secrets.py` stores the key with `phosh_toolkit.keyring`
  (schema = app id, attribute `kind=api-key`, label "Travel Log:
  Dawarich API key")[^keyring]. Nothing else is secret: e-mail and
  password of a login are used once to fetch the key and never stored.
- `settings.json` holds the style and `server_url` only (a test checks
  its keys). The key is sent only as `Authorization: Bearer`, never in a
  URL, and never logged.
- When the keyring refuses the key, the toolkit keeps it in memory for
  the session. The window then shows an `AdwBanner` ("kept only until
  Travel Log closes"), so the user knows they will have to log in again.
- Log out clears the key and the cached days.
- Tests and demo mode set `VESTIGIA_KEYRING=memory` and never touch the
  real keyring.

# Consequences

- Reading whether the toolkit fell back to memory uses its private
  `_memory`; a public accessor in the toolkit would remove that
  ([owner checks](../owner-checks.md)).
- Every start with a locked keyring asks for the key again (by design).

[^portal-secret]: XDG Desktop Portal, Secret
[^keyring]: phosh-toolkit lib/phosh_toolkit/keyring.py (v0.7.0)
