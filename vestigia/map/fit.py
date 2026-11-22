"""Zoom level and centre that show a set of positions in a viewport of a
given size, for the Web Mercator tiles of OSM. No GTK."""
import math

TILE = 256
MAX_ZOOM = 18
# A single place or a short walk: closer than this makes no sense.
MAX_FIT_ZOOM = 17


def bounds(positions):
    """(south, west, north, east) of (lat, lon) pairs, or None."""
    positions = list(positions)
    if not positions:
        return None
    lats = [p[0] for p in positions]
    lons = [p[1] for p in positions]
    return min(lats), min(lons), max(lats), max(lons)


def _y(lat):
    lat = max(min(lat, 85.0511), -85.0511)
    rad = math.radians(lat)
    return (1 - math.log(math.tan(rad) + 1 / math.cos(rad)) / math.pi) / 2


def fit(box, width, height, padding=32):
    """(lat, lon, zoom) that shows `box` (south, west, north, east) in a
    viewport of width × height pixels with `padding` pixels on each side."""
    south, west, north, east = box
    lat = (south + north) / 2
    lon = (west + east) / 2
    dx = (east - west) / 360
    dy = abs(_y(south) - _y(north))
    usable_w = max(width - 2 * padding, 1)
    usable_h = max(height - 2 * padding, 1)
    zoom = MAX_FIT_ZOOM
    for z in range(MAX_FIT_ZOOM, -1, -1):
        size = TILE * 2 ** z
        if dx * size <= usable_w and dy * size <= usable_h:
            zoom = z
            break
    else:
        zoom = 0
    return lat, lon, float(zoom)
