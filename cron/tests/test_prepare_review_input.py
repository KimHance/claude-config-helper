import json
from pathlib import Path
from scripts.prepare_review_input import build_review_input


def test_skip_unchanged_categories(tmp_path: Path):
    apply_summary = {
        "details": [
            {"file": "docs/baseline/skills.md", "changed_sections": 1},
            {"file": "docs/baseline/hooks.md", "changed_sections": 0},
        ]
    }
    reports_dir = tmp_path / "reports"
    reports_dir.mkdir()
    (reports_dir / "skills.json").write_text(json.dumps({
        "category": "skills", "rule_file": "docs/baseline/skills.md",
        "sections": {"Advanced": {"changed": True, "reason": "added Skill(name)", "sources": ["url"]}}
    }))
    diff_dir = tmp_path / "diff"
    diff_dir.mkdir()
    (diff_dir / "skills.md.diff").write_text("--- a\n+++ b\n@@\n-old\n+new\n")
    (diff_dir / "hooks.md.diff").write_text("")
    out = build_review_input(apply_summary, reports_dir, diff_dir, repo_root=tmp_path)
    assert "skills" in out
    assert "hooks" not in out
    assert "added Skill(name)" in out
