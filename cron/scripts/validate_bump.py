"""Validate the LLM-decided bump.json against actual diff evidence."""
from __future__ import annotations
import json
import sys
from pathlib import Path


def validate(bump: dict, diff_dir: Path, total_diff_lines: int) -> dict:
    out = dict(bump)
    out.setdefault("bump_warning", False)
    evidence = bump.get("evidence_files", []) or []
    diff_files = {p.name.replace(".diff", ""): p for p in diff_dir.glob("*.diff")}
    missing = []
    for ev in evidence:
        ev_name = Path(ev).name
        if ev_name not in diff_files or not diff_files[ev_name].read_text().strip():
            missing.append(ev)
    if missing:
        out["level"] = "patch"
        out["validation_notes"] = f"demoted to patch: evidence missing in diff: {missing}"
        return out
    if out.get("level") == "major" and total_diff_lines < 5:
        out["bump_warning"] = True
    return out


def main() -> int:
    if len(sys.argv) != 4:
        print("Usage: validate_bump.py <bump.json> <diff_dir> <total_diff_lines>", file=sys.stderr)
        return 2
    bump = json.loads(Path(sys.argv[1]).read_text())
    diff_dir = Path(sys.argv[2])
    total = int(sys.argv[3])
    print(json.dumps(validate(bump, diff_dir, total), indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
