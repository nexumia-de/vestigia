"""Shared fixtures: private XDG directories and no map tiles for every
test."""
import sys
from pathlib import Path

import pytest

# The shared package from the sibling checkout (CI checks it out at the
# commit the Flatpak manifest pins and sets PYTHONPATH).
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "phosh-toolkit" / "lib"))


@pytest.fixture(autouse=True)
def xdg(tmp_path, monkeypatch):
    for name in ("XDG_CONFIG_HOME", "XDG_DATA_HOME", "XDG_CACHE_HOME"):
        monkeypatch.setenv(name, str(tmp_path / name.lower()))
    # No map tiles from the network in tests.
    monkeypatch.setenv("VESTIGIA_TILES", "off")
