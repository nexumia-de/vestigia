"""Vestigia: your location history from a Dawarich server, on Phosh phones."""

try:
    from vestigia.config import APP_ID, BUILD_LABEL
except ImportError:  # run from the source tree, config.py is not built
    APP_ID = "de.nexumia.Vestigia"
    BUILD_LABEL = ""
VERSION = "0.1.0"
# The nightly app is built from every push to main.
NIGHTLY = APP_ID.endswith(".Devel")
NAME = "Travel Log (Nightly)" if NIGHTLY else "Travel Log"
# About dialog, e.g. "0.1.0 (main · 8534d2c)" for a nightly build.
VERSION_LABEL = f"{VERSION} ({BUILD_LABEL})" if BUILD_LABEL else VERSION
REPO_URL = "https://github.com/nexumia-de/vestigia"
# Sent with every request (OSM tile usage policy, Dawarich).
USER_AGENT = f"Vestigia/{VERSION} (+{REPO_URL})"
# Voluntary support for development (phosh-toolkit docs/support.md).
SUPPORT_URL = "https://liberapay.com/suitably"
