"""A day of history from the server's answers: tracks as position lists,
the timeline summary and visits. Pure functions, no GTK."""
from dataclasses import dataclass, field
from datetime import date, datetime, time, timedelta


@dataclass
class Visit:
    name: str
    status: str
    started_at: str
    ended_at: str
    lat: float
    lon: float
    visit_id: int = 0
    place_id: int = 0


@dataclass
class Day:
    day: date
    # Lists of (lat, lon), one per track (or one for the raw points).
    tracks: list = field(default_factory=list)
    # True when the server had points but no computed tracks yet.
    from_points: bool = False
    summary: dict = field(default_factory=dict)
    visits: list = field(default_factory=list)
    # (south, west, north, east) or None.
    bounds: tuple = None

    @property
    def empty(self):
        return not self.tracks and not self.visits

    def positions(self):
        out = [p for track in self.tracks for p in track]
        out += [(v.lat, v.lon) for v in self.visits]
        return out


def day_range(day, tz=None):
    """ISO 8601 start and end of a local day (the phone's time zone)."""
    tz = tz or datetime.now().astimezone().tzinfo
    start = datetime.combine(day, time.min, tz)
    end = datetime.combine(day + timedelta(days=1), time.min, tz) - timedelta(seconds=1)
    return start.isoformat(), end.isoformat()


def tracks_from_features(features):
    """(lat, lon) lists from GeoJSON LineStrings ([lon, lat] pairs)."""
    tracks = []
    for feature in features or []:
        geometry = (feature or {}).get("geometry") or {}
        lines = []
        if geometry.get("type") == "LineString":
            lines = [geometry.get("coordinates") or []]
        elif geometry.get("type") == "MultiLineString":
            lines = geometry.get("coordinates") or []
        for line in lines:
            track = [(float(c[1]), float(c[0])) for c in line if len(c) >= 2]
            if len(track) >= 2:
                tracks.append(track)
    return tracks


def track_from_points(points):
    """One (lat, lon) list from raw points, in time order."""
    points = sorted(points or [], key=lambda p: p.get("timestamp") or 0)
    return [(float(p["latitude"]), float(p["longitude"])) for p in points
            if p.get("latitude") is not None and p.get("longitude") is not None]


def from_timeline(days, day):
    """(summary, visits, bounds) of `day` in a timeline answer."""
    for entry in days or []:
        if entry.get("date") != day.isoformat():
            continue
        visits = []
        for item in entry.get("entries") or []:
            if item.get("type") != "visit":
                continue
            place = item.get("place") or {}
            if place.get("lat") is None or place.get("lng") is None:
                continue
            visits.append(Visit(
                name=item.get("name") or place.get("name") or "Visit",
                status=item.get("status") or "", visit_id=item.get("visit_id") or 0,
                place_id=item.get("place_id") or 0,
                started_at=item.get("started_at") or "",
                ended_at=item.get("ended_at") or "",
                lat=float(place["lat"]), lon=float(place["lng"])))
        b = entry.get("bounds") or {}
        bounds = None
        if all(b.get(k) is not None for k in ("sw_lat", "sw_lng", "ne_lat", "ne_lng")):
            bounds = (b["sw_lat"], b["sw_lng"], b["ne_lat"], b["ne_lng"])
        return entry.get("summary") or {}, visits, bounds
    return {}, [], None


def load(client, day):
    """The Day from the server, blocking (worker thread). Falls back to
    raw points when the server has not computed tracks yet
    (docs/dawarich-api.md, "Tracks")."""
    start, end = day_range(day)
    result = Day(day=day)
    result.tracks = tracks_from_features(client.tracks(start, end))
    if not result.tracks:
        track = track_from_points(client.points(start, end))
        if len(track) >= 2:
            result.tracks = [track]
            result.from_points = True
    result.summary, result.visits, result.bounds = from_timeline(
        client.timeline(start, end), day)
    return result
