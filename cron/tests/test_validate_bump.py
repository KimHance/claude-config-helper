import json
from pathlib import Path
from scripts.validate_bump import validate


def test_evidence_present_keeps_level(tmp_path: Path):
    diff_dir = tmp_path / "diff"
    diff_dir.mkdir()
    (diff_dir / "skills.md.diff").write_text("--- a\n+++ b\n@@\n-x\n+y\n")
    bump = {"level": "minor", "reason": "...", "evidence_files": ["docs/baseline/skills.md"]}
    out = validate(bump, diff_dir, total_diff_lines=120)
    assert out["level"] == "minor"
    assert out["bump_warning"] is False


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
