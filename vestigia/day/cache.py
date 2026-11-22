"""Fetched days on disk, keyed by server and day, for offline use:
$XDG_CACHE_HOME/vestigia/days/<server hash>/<YYYY-MM-DD>.json. Only
what the day view shows is stored; log out removes everything. No GTK."""
import hashlib
import json
import os
import shutil
from dataclasses import asdict
from datetime import date, timedelta

from phosh_toolkit.settings import app_dir

from vestigia.day.model import Day, Visit

VERSION = 1


def root():
    return app_dir("cache", "vestigia") / "days"


def _path(server_url, day):
    key = hashlib.sha256(server_url.encode()).hexdigest()[:16]
    return root() / key / f"{day.isoformat()}.json"


def final(day, today=None):
    """Days before yesterday no longer change on the server (tracks are
    computed within 12 hours, docs/dawarich-api.md): the saved copy is
    enough. Today and yesterday are always fetched again."""
    today = today or date.today()
    return day < today - timedelta(days=1)


def save(server_url, result):
    path = _path(server_url, result.day)
    path.parent.mkdir(parents=True, exist_ok=True)
    data = asdict(result)
    data["day"] = result.day.isoformat()
    tmp = path.with_suffix(".tmp")
    fd = os.open(tmp, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    with os.fdopen(fd, "w", encoding="utf-8") as f:
        json.dump({"version": VERSION, "day": data}, f)
    tmp.replace(path)


def load(server_url, day):
    """The saved Day or None."""
    try:
        data = json.loads(_path(server_url, day).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None
    if data.get("version") != VERSION:
        return None
    d = data["day"]
    return Day(day=date.fromisoformat(d["day"]),
               tracks=[[tuple(p) for p in track] for track in d["tracks"]],
               from_points=d["from_points"], summary=d["summary"],
               visits=[Visit(**v) for v in d["visits"]],
               bounds=tuple(d["bounds"]) if d["bounds"] else None)


def forget(server_url, day):
    """Drop one saved day (its visits changed on the server)."""
    try:
        _path(server_url, day).unlink()
    except FileNotFoundError:
        pass


def clear():
    shutil.rmtree(root(), ignore_errors=True)
