"""Request bodies of the two upload protocols. No GTK.

Overland: {"locations": [GeoJSON Point features]}, answered by
{"result": "ok"} (aaronpk/Overland-iOS README). OwnTracks HTTP: one
`_type: location` object per request, any 2xx counts (OwnTracks booklet,
HTTP and JSON payloads)."""
import json
from datetime import datetime, timezone


def iso(timestamp):
    return datetime.fromtimestamp(timestamp, timezone.utc).strftime(
        "%Y-%m-%dT%H:%M:%SZ")


def overland_feature(fix, device_id=""):
    properties = {"timestamp": iso(fix.timestamp)}
    if fix.accuracy:
        properties["horizontal_accuracy"] = round(fix.accuracy, 1)
    if fix.altitude is not None:
        properties["altitude"] = round(fix.altitude, 1)
    if fix.speed is not None:
        properties["speed"] = round(fix.speed, 2)
    if device_id:
        properties["device_id"] = device_id
    return {"type": "Feature",
            "geometry": {"type": "Point", "coordinates": [fix.lon, fix.lat]},
            "properties": properties}


def overland_body(fixes, device_id=""):
    return json.dumps({"locations": [overland_feature(f, device_id)
                                     for f in fixes]}).encode()


def overland_accepted(body):
    """Overland receivers confirm a batch with {"result": "ok"}."""
    try:
        return json.loads(body or b"null").get("result") == "ok"
    except (ValueError, AttributeError):
        return False


def owntracks_body(fix, tracker_id="vg"):
    data = {"_type": "location", "lat": fix.lat, "lon": fix.lon,
            "tst": int(fix.timestamp), "tid": tracker_id}
    if fix.accuracy:
        data["acc"] = round(fix.accuracy)
    if fix.altitude is not None:
        data["alt"] = round(fix.altitude)
    if fix.speed is not None:
        data["vel"] = round(fix.speed * 3.6)      # km/h in OwnTracks
    return json.dumps(data).encode()
