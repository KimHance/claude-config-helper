"""Bump plugin.json version per patch/minor/major."""
from __future__ import annotations
import json
import sys
from pathlib import Path


def bump_version(version: str, level: str) -> str:
    major, minor, patch = (int(x) for x in version.split("."))
    if level == "major":
        return f"{major + 1}.0.0"
    if level == "minor":
        return f"{major}.{minor + 1}.0"
    if level == "patch":
        return f"{major}.{minor}.{patch + 1}"
    raise ValueError(f"unknown level: {level}")


def apply_bump(manifest_path: Path, level: str) -> str:
    data = json.loads(manifest_path.read_text())
    new = bump_version(data["version"], level)
    data["version"] = new
    manifest_path.write_text(json.dumps(data, indent=2) + "\n")
    return new


def main() -> int:
    if len(sys.argv) != 3:
        print("Usage: apply_bump.py <plugin.json> <patch|minor|major>", file=sys.stderr)
        return 2
    new = apply_bump(Path(sys.argv[1]), sys.argv[2])
    print(new)
    return 0


if __name__ == "__main__":
    sys.exit(main())
