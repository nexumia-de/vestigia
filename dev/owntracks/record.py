#!/usr/bin/env python3
"""Record the answers of the local OwnTracks Recorder
(dev/owntracks/compose.yml) into tests/data/owntracks/, in the same
format as dev/dawarich/record.py. Standard library only."""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "dawarich"))
import record as dawarich  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
dawarich.OUT = ROOT / "tests" / "data" / "owntracks"
dawarich.SERVER = "http://127.0.0.1:8083"
dawarich.KEPT_HEADERS = ("content-type",)
dawarich.SERVER_NAME = "OwnTracks Recorder 1.0.7"
dawarich.BY = "dev/owntracks/record.py"
USER = {"X-Limit-U": "demo", "X-Limit-D": "phone"}


def main():
    lat, lon, ele, when, hdop, speed = dawarich.gpx_points()[0]
    from datetime import datetime
    point = {"_type": "location", "lat": lat, "lon": lon, "alt": round(ele),
             "acc": round(hdop), "tid": "vg",
             "tst": int(datetime.fromisoformat(when.replace("Z", "+00:00"))
                        .timestamp())}
    note = ""
    save = dawarich.save
    save("pub_location", dawarich.call("POST", "/pub", body=point,
                                       headers=USER), note)
    save("pub_without_user", dawarich.call("POST", "/pub", body=point), note)
    save("pub_incomplete", dawarich.call("POST", "/pub", headers=USER,
                                         body={"_type": "location", "lat": lat}),
         "a location without lon and tst")
    last = dawarich.call("GET", "/api/0/last")
    save("last", last, note)
    print(json.dumps(last["body"])[:200])


if __name__ == "__main__":
    main()
