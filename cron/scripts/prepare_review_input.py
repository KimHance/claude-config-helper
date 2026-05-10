"""Build a single markdown bundle for self-review, restricted to changed categories."""
from __future__ import annotations
import json
import sys
from pathlib import Path


def build_review_input(apply_summary: dict, reports_dir: Path, diff_dir: Path, repo_root: Path) -> str:
    parts: list[str] = ["# Review Input (changed categories only)\n"]
    for entry in apply_summary.get("details", []):
        if entry.get("changed_sections", 0) <= 0:
            continue
        rule_path = Path(entry["file"])
        cat = rule_path.stem
        report_file = reports_dir / f"{cat}.json"
        diff_file = diff_dir / f"{rule_path.name}.diff"
        if not report_file.exists():
            continue
        report = json.loads(report_file.read_text())
        parts.append(f"\n## category: {cat}\n")
        parts.append(f"\n### diff\n```diff\n{diff_file.read_text() if diff_file.exists() else ''}\n```\n")
        parts.append("\n### reasons\n")
        for sec, info in (report.get("sections") or {}).items():
            if info.get("changed"):
                parts.append(f"- **{sec}**: {info.get('reason','')} (sources: {info.get('sources',[])})\n")
        yml_path = repo_root / "skills" / "review" / "references" / f"{cat}.yml"
        if yml_path.exists():
            parts.append(f"\n### review yml ({yml_path.relative_to(repo_root)})\n```yaml\n{yml_path.read_text()}\n```\n")
    return "".join(parts)


def main() -> int:
    if len(sys.argv) != 5:
        print("Usage: prepare_review_input.py <apply_summary.json> <reports_dir> <diff_dir> <out_md>", file=sys.stderr)
        return 2
    apply_summary = json.loads(Path(sys.argv[1]).read_text())
    reports_dir = Path(sys.argv[2])
    diff_dir = Path(sys.argv[3])
    out_md = Path(sys.argv[4])
    out_md.write_text(build_review_input(apply_summary, reports_dir, diff_dir, repo_root=Path.cwd()))
    print(out_md)
    return 0


if __name__ == "__main__":
    sys.exit(main())
