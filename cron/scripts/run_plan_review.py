"""CLI entry: U3.5 Plan Review (deterministic checks 1-3).

Check 4 (semantic) is performed by the plan-reviewer agent itself; this script
produces a partial verdict that the agent then completes.
"""
import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

from verifiers.schema_validator import validate_category_file
from verifiers.source_integrity import check_source_integrity


def _check_verifier_executable(item: dict) -> tuple[bool, str]:
    v = item["verifier"]
    kind = v["kind"]
    try:
        if kind == "regex":
            import re
            re.compile(v["pattern"])
        elif kind == "yaml-parse":
            if not v.get("target"):
                return False, "yaml-parse missing target"
        elif kind == "json-schema":
            schema_ref = v["schema_ref"]
            if not Path(schema_ref).exists():
                return False, f"schema_ref not found: {schema_ref}"
        elif kind == "llm-judge":
            if len(v.get("rubric", "")) < 30:
                return False, "rubric < 30 chars"
        return True, "executable"
    except Exception as e:
        return False, f"{type(e).__name__}: {e}"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--plan", required=True, type=Path)
    ap.add_argument("--fetched-dir", required=True, type=Path)
    ap.add_argument("--out", required=True, type=Path)
    args = ap.parse_args()

    plan = json.loads(args.plan.read_text())
    now = datetime.now(timezone.utc)

    verdict = {"approved": [], "rejected": []}

    for record in plan:
        if record["action"] == "REMOVE":
            verdict["approved"].append(record["item_id"])
            continue
        item = record["payload"]
        if not item:
            verdict["rejected"].append({"id": record["item_id"], "check": "schema", "reason": "empty payload"})
            continue

        # Check 1: source integrity
        si = check_source_integrity(item, now=now)
        if not si.ok:
            verdict["rejected"].append({"id": item["id"], "check": "source", "reason": si.reason})
            continue

        # Check 3: verifier executability (skip 2; 2 is JSON Schema validation done at write-time)
        ok, reason = _check_verifier_executable(item)
        if not ok:
            verdict["rejected"].append({"id": item["id"], "check": "verifier", "reason": reason})
            continue

        verdict["approved"].append(item["id"])

    args.out.write_text(json.dumps(verdict, indent=2))


if __name__ == "__main__":
    main()
