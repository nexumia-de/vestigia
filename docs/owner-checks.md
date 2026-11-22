---
type: Concept
title: Owner checks
description: What only the owner can do - the real phone, the owner's own Dawarich server and account, secrets, other repositories - as one checklist; closed issues point here.
tags: [owner, checklist, planning, device]
generated: { by: claude-code/2.1.330, at: 2026-11-22T07:00:00Z }
---

# Why

On 2026-11-22 every open issue was closed: built and tested in the
cloud container, decided, or reduced to a step that needs the phone,
the owner's Dawarich server or account, a secret or another
repository. Those steps are collected here instead of staying open as
issues ([planning](../../phosh-toolkit/docs/planning.md)). None of them
has been done yet. Tick an item off by deleting it; write results into
the concept file named in the item.

# Checklist

## Real server (issue 2)

- [ ] Optional: run `dev/dawarich/record.py` against your own server
  once (edit `SERVER`, `EMAIL`, `PASSWORD` locally, do not commit them)
  and compare with `tests/data/dawarich/`; differences go to
  [Dawarich API](dawarich-api.md). Do not commit those answers: they
  hold your positions.
- [ ] Open the official Dawarich iOS or Android app's tracking settings
  and note the units it shows for distance filter, time filter,
  accuracy and track break (open question 4 in
  [Dawarich API](dawarich-api.md)).
