---
type: Decision Record
title: Python and PyGObject
description: Vestigia is written in Python with PyGObject, the same stack as Cirro and the toolkit's demo app.
tags: [decision, language, python]
generated: { by: claude-code/2.1.311, at: 2026-10-27T16:30:00Z }
---

# Status

Accepted (2026-10-27).

# Context

The toolkit supports Python, Vala and Rust. The app is UI, HTTP and a
small SQLite queue; nothing is compute-heavy. Cirro and the toolkit's
demo app use Python, and shared code in phosh-toolkit is a Python
package ([code reuse](../../../phosh-toolkit/docs/decisions/code-reuse.md)).

# Decision

Python 3 with PyGObject (GTK 4, libadwaita, libshumate, libsoup 3,
libportal, libsecret), `sqlite3` from the standard library for the
upload queue. Build with meson, tests with pytest.

# Consequences

- No modules beyond the GNOME runtime except libshumate (and its
  dependency protobuf-c), as in Cirro.
- Code shared with Cirro (location portal, HTTP client, map setup) moves
  into phosh-toolkit instead of being copied.
