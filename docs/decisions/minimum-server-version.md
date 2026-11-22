---
type: Decision Record
title: Oldest supported Dawarich version
description: Vestigia supports Dawarich 1.18.1 and newer, the version its recorded answers come from; older servers get a clear "server too old" message.
tags: [decision, dawarich, api, version]
generated: { by: claude-code/2.1.330, at: 2026-11-22T07:00:00Z }
sources:
  - id: recorded
    title: Answers of a local Dawarich 1.18.1 server (tests/data/dawarich/)
    url: https://github.com/nexumia-de/vestigia/tree/main/tests/data/dawarich
---

# Status

Accepted (2026-11-22), decided by best practice during the issue
clean-up; open question 7 of the [Dawarich API](../dawarich-api.md).

# Context

Dawarich releases often and its API grows with it: login with 2FA,
`/api/v1/timeline` and `/api/v1/settings/mobile` are recent. Every
server reports its version in the `X-Dawarich-Version` header of
`GET /api/v1/health`. Only one version has been checked against real
answers[^recorded].

# Decision

- The oldest supported version is **1.18.1**: the one the recordings in
  `tests/data/dawarich/` and the tests come from. Claiming support for
  an older version would need answers nobody has checked.
- The account setup reads the header; an older or unreadable version is
  refused with "server too old" and the version found. A newer version
  is accepted.
- The minimum moves only with new recordings (`dev/dawarich/record.py`
  against the new version), in the same commit as the constant
  `MIN_VERSION` in `vestigia/api/version.py`.

# Consequences

- Users on an older server must update Dawarich first; the message says
  so.
- Dependabot's updates of the dev server image (`dev/dawarich/compose.yml`)
  are the moment to re-record and, if the API changed, adapt.

[^recorded]: Answers of a local Dawarich 1.18.1 server (tests/data/dawarich/)
