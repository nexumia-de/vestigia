"""The recorded server answers (tests/data/dawarich/) are complete and
carry no secrets."""
import json
import re
from pathlib import Path

DATA = Path(__file__).parent / "data" / "dawarich"
NEEDED = {"health", "auth_login", "auth_login_2fa", "auth_otp_challenge",
          "users_me", "tracks", "points_page1", "timeline", "settings_mobile_get",
          "overland_batch", "owntracks_point", "visits", "stats",
          "tracked_months", "countries_visited", "visited_cities"}


def recordings():
    return {path.stem: json.loads(path.read_text(encoding="utf-8"))
            for path in DATA.glob("*.json")}


def test_every_needed_answer_is_recorded():
    assert NEEDED <= set(recordings())


def test_recordings_name_server_and_date():
    for name, answer in recordings().items():
        assert answer["recorded"]["server"].startswith("Dawarich 1."), name
        assert re.fullmatch(r"\d{4}-\d{2}-\d{2}", answer["recorded"]["at"]), name
        assert {"request", "status", "headers", "body"} <= set(answer), name


def test_no_secrets():
    for path in DATA.glob("*.json"):
        text = path.read_text(encoding="utf-8")
        # Dawarich API keys are 64 hex digits.
        assert not re.search(r"[0-9a-f]{64}", text), path.name
        assert "vestigia-demo-password" not in text, path.name
        assert "otpauth://" not in text, path.name
    login = recordings()["auth_login"]["body"]
    assert login["api_key"] == "REDACTED"
