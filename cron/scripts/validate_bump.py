"""Validate the LLM-decided bump.json against actual diff evidence.

Conservative demotion rules:
  - evidence_files missing in diff → demote to patch
  - level=minor but diff lacks ≥3 distinct new "configurable surface" tokens
    (CLI flags `--foo`, env vars `UPPER_SNAKE_CASE`, dotted setting keys
    `a.b.c`) → demote to patch
  - level=major with total_diff_lines < 5 → keep major but flag bump_warning
"""
from __future__ import annotations
import json
import re
import sys
from pathlib import Path


_CLI_FLAG_RE = re.compile(r"(?<![\w-])--[a-z][a-z0-9-]+", re.IGNORECASE)
_ENV_VAR_RE = re.compile(r"(?<![A-Z_])[A-Z][A-Z0-9_]{4,}(?![A-Z_])")
_DOTTED_KEY_RE = re.compile(r"(?<![\w.])[a-z][a-zA-Z0-9]+(?:\.[a-zA-Z][a-zA-Z0-9_]+){1,}")


def count_configurable_surfaces(added_lines: list[str]) -> int:
    """Count distinct new configurable surface tokens across added (+) lines.

    A configurable surface = something users would write in settings or on CLI:
    CLI flags, env vars (long form), dotted setting paths.
    """
    surfaces: set[str] = set()
    for line in added_lines:
        for m in _CLI_FLAG_RE.findall(line):
            surfaces.add(m.lower())
        for m in _ENV_VAR_RE.findall(line):
            # exclude common all-caps non-env-var words
            if m in {"NULL", "TRUE", "FALSE", "JSON", "YAML", "HTTP", "HTTPS", "URL", "PATH", "OAUTH"}:
                continue
            surfaces.add(m)
        for m in _DOTTED_KEY_RE.findall(line):
            # exclude file paths / URLs / common TLDs
            if m.startswith(("http", "code.claude")):
                continue
            if m.endswith((".md", ".json", ".yml", ".yaml", ".com", ".org", ".io", ".net", ".dev", ".sh", ".py")):
                continue
            surfaces.add(m.lower())
    return len(surfaces)


def extract_added_lines(diff_dir: Path) -> list[str]:
    """Return all added-line content from every diff file in diff_dir.

    Any diff line starting with `+` (and not the `+++ ` new-file header) is
    considered an addition. Content after the leading `+` is returned, so
    markdown bullet `+- foo` yields `- foo`.
    """
    out: list[str] = []
    for diff_file in diff_dir.glob("*.diff"):
        for line in diff_file.read_text().splitlines():
            if line.startswith("+++ "):
                continue
            if not line.startswith("+"):
                continue
            out.append(line[1:])
    return out


def validate(bump: dict, diff_dir: Path, total_diff_lines: int) -> dict:
    out = dict(bump)
    out.setdefault("bump_warning", False)

    # 1. Evidence existence check
    evidence = bump.get("evidence_files", []) or []
    diff_files = {p.name.replace(".diff", ""): p for p in diff_dir.glob("*.diff")}
    missing = []
    for ev in evidence:
        ev_name = Path(ev).name
        if ev_name not in diff_files or not diff_files[ev_name].read_text().strip():
            missing.append(ev)
    if missing:
        out["level"] = "patch"
        out["validation_notes"] = (
            f"demoted to patch: evidence missing in diff: {missing}"
        )
        return out

    # 2. Conservative minor demote: minor requires ≥3 distinct configurable surfaces
    if out.get("level") == "minor":
        added = extract_added_lines(diff_dir)
        surface_count = count_configurable_surfaces(added)
        if surface_count < 3:
            out["level"] = "patch"
            note = (
                f"demoted to patch: 'minor' requires ≥3 distinct new configurable "
                f"surfaces (CLI flags / env vars / dotted setting keys); "
                f"diff has {surface_count}."
            )
            out["validation_notes"] = (out.get("validation_notes", "") + " | " + note).strip(" |")

    # 3. Major + tiny diff = suspicious
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
