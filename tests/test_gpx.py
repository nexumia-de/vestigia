"""GPX export of the real recording, validated against the GPX 1.1
schema with xmllint. The schema is downloaded, not committed (it carries
no licence): CI fetches it; locally run

    curl -fsSL -o tests/data/gpx/gpx.xsd https://www.topografix.com/GPX/1/1/gpx.xsd
"""
import subprocess
import xml.etree.ElementTree as ET
from pathlib import Path

from gpx_fixes import fixes

from vestigia.tracker import gpx

SCHEMA = Path(__file__).parent / "data" / "gpx" / "gpx.xsd"
NS = {"g": gpx.GPX_NS, "v": gpx.EXT_NS}


def test_schema_is_there():
    assert SCHEMA.is_file(), __doc__


def test_valid_gpx_11(tmp_path):
    path = tmp_path / "day.gpx"
    path.write_bytes(gpx.write(fixes(), "2024-04-21"))
    result = subprocess.run(["xmllint", "--noout", "--schema", str(SCHEMA), str(path)],
                            capture_output=True, text=True)
    assert result.returncode == 0, result.stderr


def test_content():
    items = fixes()
    root = ET.fromstring(gpx.write(items, "2024-04-21"))
    segments = root.findall("g:trk/g:trkseg", NS)
    # The recording pauses for an hour and for 34 minutes.
    assert [len(s) for s in segments] == [16, 13, 14]
    first = segments[0].find("g:trkpt", NS)
    assert first.get("lat") == "37.1685682" and first.get("lon") == "-3.5962120"
    assert first.findtext("g:time", namespaces=NS) == "2024-04-21T09:07:31Z"
    assert first.findtext("g:ele", namespaces=NS) == "719.2"
    assert first.findtext("g:extensions/v:accuracy", namespaces=NS) == "5.3"
    assert sum(len(s) for s in segments) == len(items)


def test_empty_is_valid(tmp_path):
    path = tmp_path / "empty.gpx"
    path.write_bytes(gpx.write([], "nothing"))
    assert subprocess.run(["xmllint", "--noout", "--schema", str(SCHEMA), str(path)],
                          capture_output=True).returncode == 0
