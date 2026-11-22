"""The upload target a Dawarich account gives: its Overland endpoint
with the account's key as Bearer token (docs/dawarich-api.md). The
tracker itself knows nothing about Dawarich. No GTK."""
from vestigia.tracker.target import BEARER, OVERLAND, Target

OVERLAND_PATH = "/api/v1/overland/batches"


def dawarich_target(server_url):
    return Target(OVERLAND, server_url.rstrip("/") + OVERLAND_PATH, BEARER)
