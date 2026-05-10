import json
from pathlib import Path
from scripts.apply_bump import bump_version, apply_bump


def test_bump_version_minor():
    assert bump_version("0.4.2", "minor") == "0.5.0"


def test_bump_version_major():
    assert bump_version("0.4.2", "major") == "1.0.0"


def test_bump_version_patch():
    assert bump_version("0.4.2", "patch") == "0.4.3"


def test_apply_bump_writes_file(tmp_path: Path):
    manifest = tmp_path / "plugin.json"
    manifest.write_text(json.dumps({"name": "cchelp", "version": "0.4.2"}, indent=2))
    new = apply_bump(manifest, "minor")
    assert new == "0.5.0"
    after = json.loads(manifest.read_text())
    assert after["version"] == "0.5.0"
