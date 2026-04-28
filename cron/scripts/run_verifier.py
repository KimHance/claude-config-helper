"""CLI entry: Run a single verifier for a refs item.

Dispatches to the appropriate verifier function based on the item's
verifier.kind. Outputs JSON {"id": ..., "passed": bool, "evidence": str}
to stdout.
"""
import argparse
import json
import subprocess
import sys
from pathlib import Path

import yaml


def main():
    ap = argparse.ArgumentParser(
        description="Run a single verifier item against a target."
    )
    ap.add_argument("--refs", required=True, type=Path,
                    help="Path to refs YAML file")
    ap.add_argument("--item-id", required=True,
                    help="ID of the item in the refs YAML")
    ap.add_argument("--target", required=True, type=Path,
                    help="Path to the target file to check against")
    ap.add_argument("--value", default=None,
                    help="String value for regex verifiers")
    args = ap.parse_args()

    items = yaml.safe_load(args.refs.read_text()) or []
    item = next((it for it in items if it["id"] == args.item_id), None)
    if item is None:
        result = {"id": args.item_id, "passed": False, "evidence": f"item id '{args.item_id}' not found in {args.refs}"}
        print(json.dumps(result))
        sys.exit(0)

    kind = item["verifier"]["kind"]
    base_dir = args.target.parent

    try:
        if kind == "regex":
            from verifiers.regex import check_regex
            value = args.value if args.value is not None else args.target.read_text(encoding="utf-8").strip()
            passed, evidence = check_regex(item, value=value)

        elif kind == "line-count":
            from verifiers.line_count import check_line_count
            passed, evidence = check_line_count(item, base_dir=base_dir)

        elif kind == "file-exists":
            from verifiers.file_check import check_file_exists
            passed, evidence = check_file_exists(item, base_dir=base_dir)

        elif kind == "substring":
            from verifiers.file_check import check_substring
            passed, evidence = check_substring(item, base_dir=base_dir)

        elif kind == "yaml-parse":
            from verifiers.yaml_parse import check_yaml_parse
            passed, evidence = check_yaml_parse(item, base_dir=base_dir)

        elif kind == "json-schema":
            from verifiers.yaml_parse import check_json_schema
            passed, evidence = check_json_schema(item, base_dir=base_dir)

        elif kind == "shell":
            spec = item["verifier"]
            expected_exit = spec.get("expected_exit", 0)
            proc = subprocess.run(
                spec["command"],
                shell=True,
                capture_output=True,
                text=True,
            )
            passed = proc.returncode == expected_exit
            evidence = (
                f"exit {proc.returncode} (expected {expected_exit}); "
                f"stdout={proc.stdout.strip()!r}; stderr={proc.stderr.strip()!r}"
            )

        elif kind == "llm-judge":
            passed = False
            evidence = "llm-judge kind is handled by self-eval-runner agent, not this script"

        else:
            passed = False
            evidence = f"unknown verifier kind: {kind!r}"

    except Exception as e:
        passed = False
        evidence = f"{type(e).__name__}: {e}"

    result = {"id": args.item_id, "passed": passed, "evidence": evidence}
    print(json.dumps(result))


if __name__ == "__main__":
    main()
