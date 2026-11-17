"""Metadata, build files and manifest agree with each other."""
import re
import xml.etree.ElementTree as ET
from pathlib import Path

import vestigia

ROOT = Path(__file__).resolve().parent.parent
APP_ID = "de.nexumia.Vestigia"


def test_version_matches_meson_and_metainfo():
    meson = (ROOT / "meson.build").read_text()
    assert re.search(r"version: '([^']+)'", meson).group(1) == vestigia.VERSION
    metainfo = ET.parse(ROOT / "data" / f"{APP_ID}.metainfo.xml")
    assert metainfo.find("releases/release").get("version") == vestigia.VERSION


def test_every_module_is_installed():
    meson = (ROOT / "meson.build").read_text()
    for path in (ROOT / "vestigia").rglob("*.py"):
        name = path.relative_to(ROOT).as_posix()
        assert f"'{name}'" in meson, name


def test_phone_metadata():
    desktop = (ROOT / "data" / f"{APP_ID}.desktop").read_text()
    # Phosh matches the substring "mobile;" case-insensitively.
    assert re.search(r"^X-Purism-FormFactor=.*mobile;", desktop,
                     re.IGNORECASE | re.MULTILINE)
    assert re.search(r"^Keywords=.*dawarich;", desktop, re.MULTILINE)
    root = ET.parse(ROOT / "data" / f"{APP_ID}.metainfo.xml").getroot()
    assert root.findtext("metadata_license") == "CC0-1.0"
    length = root.find("recommends/display_length")
    assert length.get("compare") == "ge" and length.text == "360"
    assert {"touch", "pointing", "keyboard"} <= {
        c.text for c in root.findall("supports/control")}
    assert root.find("url[@type='donation']").text == vestigia.SUPPORT_URL


def test_manifest_permissions_and_pinned_toolkit():
    manifest = (ROOT / f"{APP_ID}.yml").read_text()
    block = manifest.split("finish-args:\n", 1)[1].split("\ncleanup:", 1)[0]
    args = [line.strip()[2:] for line in block.splitlines()
            if line.strip().startswith("- --")]
    # Network only; location and secrets come through portals.
    assert sorted(args) == sorted(["--share=ipc", "--socket=fallback-x11",
                                   "--socket=wayland", "--device=dri",
                                   "--share=network"])
    commit = re.search(r"- name: phosh-toolkit.*?commit: (\w+)", manifest, re.S)
    assert commit and len(commit.group(1)) == 40
    assert "- name: libshumate" in manifest


def test_every_module_has_a_checker():
    manifest = (ROOT / f"{APP_ID}.yml").read_text()
    remote = len(re.findall(r"^ +- type: (?:git|archive|file)$", manifest, re.M))
    assert remote == manifest.count("x-checker-data:")


def test_stable_build_from_source_tree():
    assert vestigia.APP_ID == APP_ID and not vestigia.NIGHTLY
    assert vestigia.VERSION_LABEL == vestigia.VERSION
    assert vestigia.NAME == "Travel Log"


def test_icons_exist():
    icons = ROOT / "data" / "icons" / "hicolor"
    assert (icons / "scalable" / "apps" / f"{APP_ID}.svg").is_file()
    assert (icons / "symbolic" / "apps" / f"{APP_ID}-symbolic.svg").is_file()


def test_accent_only_through_variables():
    css = (ROOT / "vestigia" / "style.css").read_text()
    assert "--accent-bg-color: #6741d9;" in css
    design = (ROOT / "docs" / "design.md").read_text()
    assert "#6741d9" in design
