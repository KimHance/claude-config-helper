"""CLI entry: Job 3 — aggregate group-result-*.json → plan.json."""
import argparse
import json
from pathlib import Path

import yaml

from scripts.aggregate import (
    bind_to_categories,
    build_plan_records,
    dedup_records,
    flatten_group_results,
)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--group-results-dir", required=True, type=Path)
    ap.add_argument("--mapping", required=True, type=Path)
    ap.add_argument("--out", required=True, type=Path)
    args = ap.parse_args()

    binding = yaml.safe_load(args.mapping.read_text()) or {}
    priority_tabs = (binding.get("priority") or {}).get("tabs", [])

    group_results: list[dict] = []
    for f in sorted(args.group_results_dir.glob("group-result-*.json")):
        group_results.append(json.loads(f.read_text()))

    flat = flatten_group_results(group_results)
    deduped = dedup_records(flat, priority_tabs=priority_tabs)
    bound = bind_to_categories(deduped, binding)
    plan = build_plan_records(bound)

    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(plan, indent=2, ensure_ascii=False))
    print(f"aggregated {len(plan)} records → {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
