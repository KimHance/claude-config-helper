from pathlib import Path
from scripts.parse_deletion_facts import extract_deletions


def test_no_changes_returns_empty(tmp_path: Path):
    summary = {"details": [{"file": "docs/baseline/skills.md", "changed_sections": 0}]}
    reports_dir = tmp_path / "reports"
    diff_dir = tmp_path / "diff"
    reports_dir.mkdir()
    diff_dir.mkdir()
    out = extract_deletions(summary, reports_dir, diff_dir)
    assert out == []


def test_extracts_deleted_line(tmp_path: Path):
    summary = {"details": [
        {"file": "docs/baseline/permissions.md", "changed_sections": 1}
    ]}
    reports_dir = tmp_path / "reports"
    reports_dir.mkdir()
    (reports_dir / "permissions.json").write_text(
        '{"sections": {"Anti-patterns": {"changed": true}}}'
    )
    diff_dir = tmp_path / "diff"
    diff_dir.mkdir()
    (diff_dir / "permissions.md.diff").write_text(
        "--- a\n+++ b\n@@\n context\n"
        "- Do not place project-scope `permissions.skipDangerousModePermissionPrompt`\n"
        " other\n"
    )
    out = extract_deletions(summary, reports_dir, diff_dir)
    assert len(out) == 1
    assert out[0]["category"] == "permissions"
    assert "skipDangerousModePermissionPrompt" in out[0]["deleted_line"]


def test_ignores_diff_header_lines(tmp_path: Path):
    """diff header `---` lines must not be treated as deletions."""
    summary = {"details": [
        {"file": "docs/baseline/skills.md", "changed_sections": 1}
    ]}
    reports_dir = tmp_path / "reports"
    reports_dir.mkdir()
    (reports_dir / "skills.json").write_text('{"sections": {}}')
    diff_dir = tmp_path / "diff"
    diff_dir.mkdir()
    (diff_dir / "skills.md.diff").write_text(
        "--- /tmp/baseline-before/skills.md\n"
        "+++ docs/baseline/skills.md\n"
        "@@\n"
        " keep\n"
    )
    out = extract_deletions(summary, reports_dir, diff_dir)
    assert out == []


def test_multiple_deletions_across_categories(tmp_path: Path):
    summary = {"details": [
        {"file": "docs/baseline/permissions.md", "changed_sections": 1},
        {"file": "docs/baseline/skills.md", "changed_sections": 1},
        {"file": "docs/baseline/hooks.md", "changed_sections": 0},
    ]}
    reports_dir = tmp_path / "reports"
    reports_dir.mkdir()
    (reports_dir / "permissions.json").write_text('{"sections": {}}')
    (reports_dir / "skills.json").write_text('{"sections": {}}')
    diff_dir = tmp_path / "diff"
    diff_dir.mkdir()
    (diff_dir / "permissions.md.diff").write_text(
        "--- a\n+++ b\n@@\n- alpha removed\n"
    )
    (diff_dir / "skills.md.diff").write_text(
        "--- a\n+++ b\n@@\n- beta removed\n- gamma removed\n"
    )
    (diff_dir / "hooks.md.diff").write_text("")
    out = extract_deletions(summary, reports_dir, diff_dir)
    assert len(out) == 3
    cats = sorted({e["category"] for e in out})
    assert cats == ["permissions", "skills"]
