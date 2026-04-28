"""U4 Apply (deterministic). PHASE 1 SCOPE: refs only. Templates and agent prompt propagation deferred to phase 2 (separate spec)."""
import argparse
import json
from pathlib import Path

import yaml


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--plan", required=True, type=Path)
    ap.add_argument("--review", required=True, type=Path)
    ap.add_argument("--refs-dir", required=True, type=Path)
    args = ap.parse_args()

    plan = json.loads(args.plan.read_text())
    review = json.loads(args.review.read_text())
    approved_ids = set(review.get("approved_records", review.get("approved", [])))

    # 카테고리별 그룹
    by_cat: dict[str, list] = {}
    for record in plan:
        if record["item_id"] not in approved_ids:
            continue
        by_cat.setdefault(record["category"], []).append(record)

    for category, records in by_cat.items():
        refs_path = args.refs_dir / f"{category}.yml"
        items = yaml.safe_load(refs_path.read_text()) if refs_path.exists() else []
        items = items or []
        items_by_id = {it["id"]: it for it in items}

        for r in records:
            if r["action"] == "ADD":
                items_by_id[r["item_id"]] = r["payload"]
            elif r["action"] == "UPDATE":
                items_by_id[r["item_id"]] = r["payload"]
            elif r["action"] == "REMOVE":
                items_by_id.pop(r["item_id"], None)

        new_items = sorted(items_by_id.values(), key=lambda it: it["id"])
        refs_path.parent.mkdir(parents=True, exist_ok=True)
        refs_path.write_text(yaml.safe_dump(new_items, sort_keys=False, allow_unicode=True))

    print(f"applied {len(approved_ids)} approved records across {len(by_cat)} categories")


if __name__ == "__main__":
    main()
