"""GPX 1.1 from recorded points (https://www.topografix.com/GPX/1/1/):
one track, a new segment after a pause, time and elevation where known,
the accuracy in Vestigia's own extension (GPX has no field for it). No
GTK."""
from xml.etree import ElementTree as ET

from vestigia.tracker.protocols import iso

GPX_NS = "http://www.topografix.com/GPX/1/1"
EXT_NS = "https://github.com/nexumia-de/vestigia/gpx/1"
# A pause longer than this starts a new segment.
SEGMENT_BREAK_S = 30 * 60


def segments(fixes, gap=SEGMENT_BREAK_S):
    out = []
    for fix in sorted(fixes, key=lambda f: f.timestamp):
        if not out or fix.timestamp - out[-1][-1].timestamp > gap:
            out.append([])
        out[-1].append(fix)
    return out


def write(fixes, name, creator="Travel Log"):
    """The GPX document as UTF-8 bytes."""
    ET.register_namespace("", GPX_NS)
    ET.register_namespace("vestigia", EXT_NS)
    root = ET.Element(f"{{{GPX_NS}}}gpx", version="1.1", creator=creator)
    metadata = ET.SubElement(root, f"{{{GPX_NS}}}metadata")
    ET.SubElement(metadata, f"{{{GPX_NS}}}name").text = name
    fixes = list(fixes)
    if fixes:
        ET.SubElement(metadata, f"{{{GPX_NS}}}time").text = iso(
            min(f.timestamp for f in fixes))
    track = ET.SubElement(root, f"{{{GPX_NS}}}trk")
    ET.SubElement(track, f"{{{GPX_NS}}}name").text = name
    for segment in segments(fixes):
        seg = ET.SubElement(track, f"{{{GPX_NS}}}trkseg")
        for fix in segment:
            point = ET.SubElement(seg, f"{{{GPX_NS}}}trkpt",
                                  lat=f"{fix.lat:.7f}", lon=f"{fix.lon:.7f}")
            # Order matters in GPX 1.1: ele, time, ..., extensions.
            if fix.altitude is not None:
                ET.SubElement(point, f"{{{GPX_NS}}}ele").text = f"{fix.altitude:.1f}"
            ET.SubElement(point, f"{{{GPX_NS}}}time").text = iso(fix.timestamp)
            if fix.accuracy:
                ext = ET.SubElement(point, f"{{{GPX_NS}}}extensions")
                ET.SubElement(ext, f"{{{EXT_NS}}}accuracy").text = f"{fix.accuracy:.1f}"
    ET.indent(root)
    return ET.tostring(root, encoding="utf-8", xml_declaration=True) + b"\n"
