"""The tracking settings Dawarich keeps for its mobile apps
(GET/PATCH /api/v1/settings/mobile, docs/dawarich-api.md): which fields
map to Vestigia's own, with the server's clamps. `accuracy` (a level
1–6) and `track_break` have no documented meaning and are not synced.
No GTK."""
CLAMPS = {"distance_filter": (1, 10000), "time_filter": (1, 3600),
          "batch_size": (1, 1000)}
MODES = ("precise", "significant")


def clamp(name, value):
    low, high = CLAMPS[name]
    return max(low, min(int(value), high))


def to_server(settings):
    return {"tracking_mode": settings.mode,
            "distance_filter": clamp("distance_filter", settings.distance),
            "time_filter": clamp("time_filter", settings.interval),
            "batch_size": clamp("batch_size", settings.batch_size),
            "upload_automatically": bool(settings.upload_automatically)}


def apply(server, settings):
    """Take the server's values into `settings`; True if any changed.
    An empty answer (a new account) changes nothing."""
    before = (settings.mode, settings.distance, settings.interval,
              settings.batch_size, settings.upload_automatically)
    if server.get("tracking_mode") in MODES:
        settings.mode = server["tracking_mode"]
    for key, attr in (("distance_filter", "distance"), ("time_filter", "interval"),
                      ("batch_size", "batch_size")):
        if isinstance(server.get(key), (int, float)):
            setattr(settings, attr, clamp(key, server[key]))
    if isinstance(server.get("upload_automatically"), bool):
        settings.upload_automatically = server["upload_automatically"]
    after = (settings.mode, settings.distance, settings.interval,
             settings.batch_size, settings.upload_automatically)
    return before != after
