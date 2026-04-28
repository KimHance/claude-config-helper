"""CLI entry: U2 diff. For each refs/*.yml, classify items vs fetched body."""
import argparse
import json
from pathlib import Path

import yaml

from scripts.diff import classify_items


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--refs-dir", required=True, type=Path)
    ap.add_argument("--fetched-dir", required=True, type=Path)
    ap.add_argument("--out", required=True, type=Path)
    args = ap.parse_args()

    out = {}
    for refs_file in sorted(args.refs_dir.glob("*.yml")):
        category = refs_file.stem
        items = yaml.safe_load(refs_file.read_text()) or []
        body_path = args.fetched_dir / f"{category}.md"
        if not body_path.exists():
            out[category] = {"error": f"fetched body missing: {body_path}"}
            continue
        body = body_path.read_text()
        statuses = classify_items(items, body)
        out[category] = {item_id: status.value for item_id, status in statuses.items()}

    args.out.write_text(json.dumps(out, indent=2))


if __name__ == "__main__":
    main()
