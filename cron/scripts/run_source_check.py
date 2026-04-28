"""CLI entry: Run source integrity check for a single plan record.

Loads a plan JSON, finds the record by item_id, and calls
verifiers.source_integrity.check_source_integrity. Outputs JSON
{"ok": bool, "reason": str, "url_status": int|None} to stdout.
"""
import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path


def main():
    ap = argparse.ArgumentParser(
        description="Check source integrity for a single plan record."
    )
    ap.add_argument("--plan", required=True, type=Path,
                    help="Path to plan.json")
    ap.add_argument("--record-id", required=True,
                    help="item_id of the record to check")
    args = ap.parse_args()

    plan = json.loads(args.plan.read_text())
    record = next(
        (r for r in plan if r["item_id"] == args.record_id),
        None,
    )

    if record is None:
        result = {"ok": False, "reason": f"record id '{args.record_id}' not found in plan", "url_status": None}
        print(json.dumps(result))
        sys.exit(0)

    # REMOVE records have no payload with source; treat as ok
    if record["action"] == "REMOVE" or not record.get("payload"):
        result = {"ok": True, "reason": "REMOVE record; no source to check", "url_status": None}
        print(json.dumps(result))
        sys.exit(0)

    from verifiers.source_integrity import check_source_integrity

    now = datetime.now(timezone.utc)
    si = check_source_integrity(record["payload"], now=now)

    result = {
        "ok": si.ok,
        "reason": si.reason,
        "url_status": si.url_status,
    }
    print(json.dumps(result))


if __name__ == "__main__":
    main()
