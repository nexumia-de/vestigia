"""A position fix and the distance between two. No GTK."""
import math
from dataclasses import dataclass

EARTH_RADIUS_M = 6371008.8


@dataclass(frozen=True)
class Fix:
    lat: float
    lon: float
    # Horizontal accuracy in metres (0: unknown).
    accuracy: float
    # Unix seconds.
    timestamp: float
    altitude: float = None
    # Metres per second.
    speed: float = None


def distance_m(a, b):
    """Great-circle distance between two fixes (haversine)."""
    lat1, lat2 = math.radians(a.lat), math.radians(b.lat)
    dlat = lat2 - lat1
    dlon = math.radians(b.lon - a.lon)
    h = math.sin(dlat / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2) ** 2
    return 2 * EARTH_RADIUS_M * math.asin(math.sqrt(h))
