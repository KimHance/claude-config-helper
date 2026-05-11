import json
from pathlib import Path
from scripts.validate_bump import validate, count_configurable_surfaces


def test_evidence_missing_demotes_to_patch(tmp_path: Path):
    diff_dir = tmp_path / "diff"
    diff_dir.mkdir()
    bump = {"level": "major", "reason": "...", "evidence_files": ["docs/baseline/ghost.md"]}
    out = validate(bump, diff_dir, total_diff_lines=120)
    assert out["level"] == "patch"
    assert "demoted" in (out.get("validation_notes") or "")


def test_major_with_small_diff_sets_warning(tmp_path: Path):
    diff_dir = tmp_path / "diff"
    diff_dir.mkdir()
    (diff_dir / "skills.md.diff").write_text("--- a\n+++ b\n@@\n-x\n+y\n")
    bump = {"level": "major", "reason": "...", "evidence_files": ["docs/baseline/skills.md"]}
    out = validate(bump, diff_dir, total_diff_lines=3)
    assert out["level"] == "major"
    assert out["bump_warning"] is True


def test_minor_with_insufficient_surfaces_demotes_to_patch(tmp_path: Path):
    """Conservative: minor requires ≥3 distinct configurable surfaces."""
    diff_dir = tmp_path / "diff"
    diff_dir.mkdir()
    (diff_dir / "skills.md.diff").write_text(
        "--- a\n+++ b\n@@\n+ small wording clarification\n"
    )
    bump = {"level": "minor", "reason": "...", "evidence_files": ["docs/baseline/skills.md"]}
    out = validate(bump, diff_dir, total_diff_lines=10)
    assert out["level"] == "patch"
    assert "configurable surfaces" in out.get("validation_notes", "")


def test_minor_with_three_surfaces_stays_minor(tmp_path: Path):
    """Three distinct configurable surfaces qualifies for minor."""
    diff_dir = tmp_path / "diff"
    diff_dir.mkdir()
    (diff_dir / "settings.md.diff").write_text(
        "--- a\n+++ b\n@@\n"
        "+ CLAUDE_CODE_NEW_FOO env var added for X\n"
        "+ --new-flag CLI flag controls Y\n"
        "+ permissions.disableNewMode setting added\n"
    )
    bump = {"level": "minor", "reason": "3 new surfaces", "evidence_files": ["docs/baseline/settings.md"]}
    out = validate(bump, diff_dir, total_diff_lines=10)
    assert out["level"] == "minor"


def test_count_configurable_surfaces_detects_all_three_types():
    lines = [
        "Use --plugin-url to fetch zip",
        "Set CLAUDE_CODE_HIDE_CWD to hide startup logo",
        "Add permissions.disableAutoMode to settings",
    ]
    n = count_configurable_surfaces(lines)
    assert n == 3


def test_count_configurable_surfaces_dedup():
    """Same surface mentioned twice counts once."""
    lines = [
        "Use --foo for X",
        "Note: --foo also affects Y",
    ]
    n = count_configurable_surfaces(lines)
    assert n == 1


def test_count_configurable_surfaces_excludes_common_caps_and_paths():
    lines = [
        "Returns JSON from HTTP endpoint",  # JSON, HTTP excluded
        "See docs/baseline/skills.md",  # .md path excluded
        "URL: https://example.com",  # URL excluded
    ]
    n = count_configurable_surfaces(lines)
    assert n == 0


def test_patch_unchanged(tmp_path: Path):
    """Patch level should never be demoted further."""
    diff_dir = tmp_path / "diff"
    diff_dir.mkdir()
    (diff_dir / "skills.md.diff").write_text("--- a\n+++ b\n@@\n+ minor wording\n")
    bump = {"level": "patch", "reason": "...", "evidence_files": ["docs/baseline/skills.md"]}
    out = validate(bump, diff_dir, total_diff_lines=10)
    assert out["level"] == "patch"
