"""Fixes of the real OsmAnd recording in tests/data/source/ (OsmAnd
writes the accuracy in metres into <hdop>)."""
import xml.etree.ElementTree as ET
from datetime import datetime
from pathlib import Path

from vestigia.tracker.fix import Fix

GPX = Path(__file__).parent / "data" / "source" / "gpx_track_multiple_segments.gpx"
NS = {"g": "http://www.topografix.com/GPX/1/1", "osmand": "https://osmand.net"}


def fixes():
    root = ET.fromstring(GPX.read_text(encoding="utf-8").strip())
    out = []
    for p in root.iterfind(".//g:trkpt", NS):
        when = datetime.fromisoformat(p.find("g:time", NS).text.replace("Z", "+00:00"))
        speed = p.find("g:extensions/osmand:speed", NS)
        out.append(Fix(float(p.get("lat")), float(p.get("lon")),
                       float(p.find("g:hdop", NS).text), when.timestamp(),
                       float(p.find("g:ele", NS).text),
                       float(speed.text) if speed is not None else None))
    return out
