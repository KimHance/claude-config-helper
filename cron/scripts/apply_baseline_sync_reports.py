"""Baseline-sync JSON reports → baseline file patcher.

Reads JSON reports produced by the baseline-sync-check step, splits each baseline
markdown file by ## headings, replaces only the sections marked
`changed: true`, and writes the file back. Sections marked `changed: false`
or absent from the report are left byte-for-byte unchanged.
"""
from __future__ import annotations

import re
from typing import Dict, Tuple


_H2_RE = re.compile(r"^## (.+?)\s*$", re.MULTILINE)


def split_by_h2(md: str) -> Tuple[str, Dict[str, str]]:
    """Split a markdown string at every level-2 heading.

    Returns (head, sections) where head is everything before the first ##
    and sections maps each heading text to its body (everything between
    that ## and the next ## or end-of-file).
    """
    matches = list(_H2_RE.finditer(md))
    if not matches:
        return md, {}
    head = md[: matches[0].start()]
    sections: Dict[str, str] = {}
    for i, m in enumerate(matches):
        name = m.group(1).strip()
        body_start = m.end()
        body_end = matches[i + 1].start() if i + 1 < len(matches) else len(md)
        body = md[body_start:body_end]
        body = body.lstrip("\n")
        sections[name] = body
    return head, sections


def merge_by_h2(head: str, sections: Dict[str, str], order: list[str]) -> str:
    """Reassemble a markdown string in the given section order.

    `order` is the canonical section name list (from criteria-mapping
    `section_names`). Sections not in `order` are appended at the end in
    insertion order.
    """
    head = head.rstrip() + "\n\n" if head.strip() else ""
    parts = [head]
    seen = set()
    for name in order:
        if name in sections:
            body = sections[name].rstrip() + "\n"
            parts.append(f"## {name}\n{body}\n")
            seen.add(name)
    for name, body in sections.items():
        if name not in seen:
            body = body.rstrip() + "\n"
            parts.append(f"## {name}\n{body}\n")
    out = "".join(parts).rstrip() + "\n"
    return out


def apply_report(report: dict, section_names: list[str]) -> dict:
    """Apply a single oracle JSON report to its rule file.

    Returns stats: {file, changed_sections, total_sections}. Mutates the
    rule_file on disk only when at least one section is changed.
    """
    from pathlib import Path

    rule_path = Path(report["rule_file"])
    if not rule_path.exists():
        return {
            "file": str(rule_path),
            "changed_sections": 0,
            "skipped": "missing",
        }

    original = rule_path.read_text()
    head, sections = split_by_h2(original)

    sections_in_report: dict = report.get("sections", {}) or {}
    allowed = set(section_names)
    changed = 0

    for name in section_names:
        info = sections_in_report.get(name)
        if not info:
            continue
        if info.get("changed") is True:
            new_body = info.get("new_body", "")
            sections[name] = new_body
            changed += 1
        # changed: false → leave sections[name] untouched

    # Drop any keys the report invented that are outside section_names
    for k in list(sections.keys()):
        if k not in allowed:
            sections.pop(k)

    new_text = merge_by_h2(head, sections, section_names)
    if new_text != original:
        rule_path.write_text(new_text)

    return {
        "file": str(rule_path),
        "changed_sections": changed,
        "total_sections": len(section_names),
    }


def main() -> int:
    """CLI: apply_baseline_sync_reports.py <reports_dir> <criteria_mapping_yaml>"""
    import json
    import sys
    from pathlib import Path

    import yaml  # local import — keeps split/merge unit tests dependency-free

    if len(sys.argv) != 3:
        print(
            "Usage: apply_baseline_sync_reports.py <reports_dir> <criteria_mapping_yaml>",
            file=sys.stderr,
        )
        return 2

    reports_dir = Path(sys.argv[1])
    mapping = yaml.safe_load(Path(sys.argv[2]).read_text())
    section_names: list[str] = mapping["section_names"]

    stats: list[dict] = []
    for report_file in sorted(reports_dir.glob("*.json")):
        report = json.loads(report_file.read_text())
        stats.append(apply_report(report, section_names))

    summary = {
        "files_processed": len(stats),
        "files_with_changes": sum(
            1 for s in stats if s.get("changed_sections", 0) > 0
        ),
        "total_sections_changed": sum(
            s.get("changed_sections", 0) for s in stats
        ),
        "details": stats,
    }
    print(json.dumps(summary, indent=2))
    return 0


if __name__ == "__main__":
    import sys

    sys.exit(main())
