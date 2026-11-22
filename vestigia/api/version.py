"""The oldest Dawarich version Vestigia supports
(docs/decisions/minimum-server-version.md). No GTK."""
import re

MIN_VERSION = (1, 18, 1)


def parse(text):
    """(major, minor, patch) from "1.18.1" or "v1.22.0-rc1"; None if
    the text holds no version."""
    match = re.search(r"(\d+)\.(\d+)(?:\.(\d+))?", text or "")
    if not match:
        return None
    return tuple(int(part or 0) for part in match.groups())


def supported(text):
    version = parse(text)
    return version is not None and version >= MIN_VERSION


def shown(version=MIN_VERSION):
    return ".".join(str(part) for part in version)
