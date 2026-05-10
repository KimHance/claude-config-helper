import json
import textwrap
from pathlib import Path

from scripts.apply_baseline_sync_reports import apply_report, split_by_h2, merge_by_h2


def test_split_by_h2_basic():
    md = textwrap.dedent("""
        # title

        intro text

        ## Fundamentals
        - a
        - b

        ## Advanced
        - c

        ## Recommended
        - d

        ## Anti-patterns
        - e
    """).strip() + "\n"

    head, sections = split_by_h2(md)
    assert "# title" in head
    assert "intro text" in head
    assert sections["Fundamentals"].strip() == "- a\n- b"
    assert sections["Advanced"].strip() == "- c"
    assert sections["Recommended"].strip() == "- d"
    assert sections["Anti-patterns"].strip() == "- e"


def test_merge_by_h2_roundtrip():
    md = textwrap.dedent("""
        # x

        ## Fundamentals
        - a

        ## Advanced
        - b
    """).strip() + "\n"
    head, sections = split_by_h2(md)
    merged = merge_by_h2(head, sections, ["Fundamentals", "Advanced"])
    assert merged.strip() == md.strip()


def test_merge_replaces_only_changed():
    md_before = textwrap.dedent("""
        # x

        ## Fundamentals
        - old fundamentals

        ## Advanced
        - keep me
    """).strip() + "\n"
    head, sections = split_by_h2(md_before)
    sections["Fundamentals"] = "- new fundamentals\n"
    merged = merge_by_h2(head, sections, ["Fundamentals", "Advanced"])
    assert "new fundamentals" in merged
    assert "keep me" in merged
    assert "old fundamentals" not in merged


def test_apply_report_no_changes(tmp_path: Path):
    rule = tmp_path / "skills.md"
    original = (
        "# skills\n\n"
        "## Fundamentals\n- a\n\n"
        "## Advanced\n- b\n\n"
        "## Recommended\n- c\n\n"
        "## Anti-patterns\n- d\n"
    )
    rule.write_text(original)
    report = {
        "category": "skills",
        "rule_file": str(rule),
        "sections": {
            "Fundamentals": {"changed": False},
            "Advanced": {"changed": False},
            "Recommended": {"changed": False},
            "Anti-patterns": {"changed": False},
        },
    }
    section_names = ["Fundamentals", "Advanced", "Recommended", "Anti-patterns"]
    result = apply_report(report, section_names)
    assert result["changed_sections"] == 0
    assert rule.read_text() == original  # byte-for-byte intact


def test_apply_report_one_changed(tmp_path: Path):
    rule = tmp_path / "skills.md"
    rule.write_text(
        "# skills\n\n"
        "## Fundamentals\n- old\n\n"
        "## Advanced\n- keep\n"
    )
    report = {
        "category": "skills",
        "rule_file": str(rule),
        "sections": {
            "Fundamentals": {"changed": True, "new_body": "- new\n"},
            "Advanced": {"changed": False},
        },
    }
    result = apply_report(report, ["Fundamentals", "Advanced"])
    assert result["changed_sections"] == 1
    text = rule.read_text()
    assert "- new" in text
    assert "- old" not in text
    assert "- keep" in text


def test_apply_report_unknown_section_ignored(tmp_path: Path):
    rule = tmp_path / "skills.md"
    rule.write_text("# skills\n\n## Fundamentals\n- a\n")
    report = {
        "category": "skills",
        "rule_file": str(rule),
        "sections": {
            "Fundamentals": {"changed": False},
            "BogusSection": {"changed": True, "new_body": "should not appear"},
        },
    }
    result = apply_report(report, ["Fundamentals"])
    assert "BogusSection" not in rule.read_text()
    assert "should not appear" not in rule.read_text()
    assert result["changed_sections"] == 0
