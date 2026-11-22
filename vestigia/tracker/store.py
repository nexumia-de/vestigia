"""Recorded points in SQLite ($XDG_DATA_HOME/vestigia/points.sqlite). A
point is on disk before anything else happens; uploads mark it per
target instead of deleting it, so it stays for GPX export until it is
pruned (docs/tracking.md, step 3). Used from one thread. No GTK."""
import os
import sqlite3
import time

from phosh_toolkit.settings import app_dir

from vestigia.tracker.fix import Fix

SCHEMA = """
CREATE TABLE IF NOT EXISTS points (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp REAL NOT NULL,
    lat REAL NOT NULL, lon REAL NOT NULL, accuracy REAL,
    altitude REAL, speed REAL);
CREATE INDEX IF NOT EXISTS points_time ON points (timestamp);
CREATE TABLE IF NOT EXISTS uploads (
    point_id INTEGER NOT NULL REFERENCES points (id) ON DELETE CASCADE,
    target TEXT NOT NULL, uploaded_at REAL NOT NULL,
    PRIMARY KEY (point_id, target));
CREATE TABLE IF NOT EXISTS parked (
    point_id INTEGER NOT NULL REFERENCES points (id) ON DELETE CASCADE,
    target TEXT NOT NULL, reason TEXT, parked_at REAL NOT NULL,
    PRIMARY KEY (point_id, target));
"""
COLUMNS = "id, lat, lon, accuracy, timestamp, altitude, speed"


def default_path():
    return app_dir("data", "vestigia") / "points.sqlite"


def _fix(row):
    return row[0], Fix(*row[1:])


class Store:
    def __init__(self, path=None, clock=time.time):
        self.path = path or default_path()
        self.clock = clock
        self.path.parent.mkdir(parents=True, exist_ok=True)
        if not self.path.exists():
            # Positions are personal data: readable by the user only.
            os.close(os.open(self.path, os.O_CREAT | os.O_WRONLY, 0o600))
        self.db = sqlite3.connect(self.path, isolation_level=None)
        self.db.execute("PRAGMA foreign_keys = ON")
        self.db.execute("PRAGMA journal_mode = WAL")
        # Every commit reaches the disk: a crash or a dead battery after
        # add() loses nothing.
        self.db.execute("PRAGMA synchronous = FULL")
        self.db.executescript(SCHEMA)

    def close(self):
        self.db.close()

    def add(self, fix):
        """Store a point at once; its id."""
        cursor = self.db.execute(
            "INSERT INTO points (timestamp, lat, lon, accuracy, altitude, speed)"
            " VALUES (?, ?, ?, ?, ?, ?)",
            (fix.timestamp, fix.lat, fix.lon, fix.accuracy, fix.altitude, fix.speed))
        return cursor.lastrowid

    def pending(self, target, limit=None):
        """(id, Fix) not yet uploaded to `target` and not parked there,
        oldest first."""
        query = (f"SELECT {COLUMNS} FROM points p WHERE NOT EXISTS "
                 "(SELECT 1 FROM uploads u WHERE u.point_id = p.id AND u.target = ?)"
                 " AND NOT EXISTS (SELECT 1 FROM parked k WHERE k.point_id = p.id"
                 " AND k.target = ?) ORDER BY timestamp, id")
        args = [target, target]
        if limit:
            query += " LIMIT ?"
            args.append(limit)
        return [_fix(row) for row in self.db.execute(query, args)]

    def count_pending(self, target):
        return len(self.pending(target))

    def mark_uploaded(self, target, ids):
        now = self.clock()
        with self.db:
            self.db.execute("BEGIN")
            self.db.executemany(
                "INSERT OR IGNORE INTO uploads (point_id, target, uploaded_at) "
                "VALUES (?, ?, ?)", [(i, target, now) for i in ids])

    def park(self, target, point_id, reason):
        """Keep a point the target refuses out of the queue."""
        self.db.execute("INSERT OR REPLACE INTO parked (point_id, target, reason,"
                        " parked_at) VALUES (?, ?, ?, ?)",
                        (point_id, target, reason, self.clock()))

    def parked(self, target):
        return [(row[0], row[1]) for row in self.db.execute(
            "SELECT point_id, reason FROM parked WHERE target = ? ORDER BY point_id",
            (target,))]

    def last_upload(self, target):
        row = self.db.execute("SELECT MAX(uploaded_at) FROM uploads WHERE target = ?",
                              (target,)).fetchone()
        return row[0]

    def between(self, start, end):
        """Fixes with start <= timestamp < end (Unix seconds), in order."""
        return [_fix(row)[1] for row in self.db.execute(
            f"SELECT {COLUMNS} FROM points WHERE timestamp >= ? AND timestamp < ?"
            " ORDER BY timestamp, id", (start, end))]

    def days(self):
        """Unix seconds of the first and last point, or None."""
        row = self.db.execute("SELECT MIN(timestamp), MAX(timestamp) FROM points").fetchone()
        return None if row[0] is None else row

    def prune(self, keep_days, target=None):
        """Delete points older than `keep_days`; with a target only those
        it received or refused, so nothing waiting is lost."""
        cutoff = self.clock() - keep_days * 86400
        if target is None:
            cursor = self.db.execute("DELETE FROM points WHERE timestamp < ?", (cutoff,))
        else:
            cursor = self.db.execute(
                "DELETE FROM points WHERE timestamp < ? AND (id IN (SELECT point_id"
                " FROM uploads WHERE target = ?) OR id IN (SELECT point_id FROM"
                " parked WHERE target = ?))", (cutoff, target, target))
        return cursor.rowcount
