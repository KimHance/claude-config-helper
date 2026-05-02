"""Sub-agent 가 자기 group-result-*.json 작성 후 schema 사전 검증 용 CLI."""
import argparse
import json
import sys
from pathlib import Path

import jsonschema

SCHEMA_PATH = Path(__file__).parent.parent / "schema" / "group-result.schema.json"
ITEM_SCHEMA_PATH = Path(__file__).parent.parent / "schema" / "item.schema.json"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--file", required=True, type=Path)
    args = ap.parse_args()

    schema = json.loads(SCHEMA_PATH.read_text())
    item_schema = json.loads(ITEM_SCHEMA_PATH.read_text())
    data = json.loads(args.file.read_text())

    try:
        jsonschema.validate(data, schema)
    except jsonschema.ValidationError as e:
        print(f"FAIL: group-result schema violation: {e.message}", file=sys.stderr)
        return 1

    # records 의 verifier 도 item.schema 의 verifier oneOf 로 추가 검증
    for idx, rec in enumerate(data.get("records", [])):
        # item.schema 와 일치하는 record subset 만 추출 (page/category_hint 제외)
        item_view = {k: v for k, v in rec.items() if k not in ("page", "category_hint")}
        item_view["category"] = rec["category_hint"]  # item.schema 는 category 필드 요구
        try:
            jsonschema.validate(item_view, item_schema)
        except jsonschema.ValidationError as e:
            print(f"FAIL: record[{idx}] item-schema violation: {e.message}", file=sys.stderr)
            return 1

    print(f"OK: group-result valid ({len(data.get('records', []))} records)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
