"""Extract deleted facts from baseline-sync diffs for C8 cross-check trio."""
from __future__ import annotations
import json
import sys
from pathlib import Path


def extract_deletions(apply_summary: dict, reports_dir: Path, diff_dir: Path) -> list[dict]:
    """Return list of {category, deleted_line} for each removed baseline line.

    A "deletion" is any diff line starting with `-` that is not a diff
    header (`--- ` old-file marker). Content after the leading `-` is the
    deleted line, including markdown bullet `- ` prefix when present.
    """
    out: list[dict] = []
    for entry in apply_summary.get("details", []):
        if entry.get("changed_sections", 0) <= 0:
            continue
        cat = Path(entry["file"]).stem
        diff_file = diff_dir / f"{cat}.md.diff"
        if not diff_file.exists():
            continue
        for line in diff_file.read_text().splitlines():
            # unified-diff old-file header
            if line.startswith("--- "):
                continue
            # ignore @@ hunks and context lines (starting with space)
            if not line.startswith("-"):
                continue
            removed = line[1:].strip()
            if not removed:
                continue
            out.append({"category": cat, "deleted_line": removed})
    return out


def main() -> int:
    if len(sys.argv) != 4:
        print(
            "Usage: parse_deletion_facts.py <apply_summary.json> <reports_dir> <diff_dir>",
            file=sys.stderr,
        )
        return 2
    summary = json.loads(Path(sys.argv[1]).read_text())
    out = extract_deletions(summary, Path(sys.argv[2]), Path(sys.argv[3]))
    print(json.dumps(out, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
