import json
from pathlib import Path

import jsonschema
import pytest

SCHEMA_PATH = Path(__file__).parent.parent / "schema" / "group-result.schema.json"


@pytest.fixture
def schema():
    return json.loads(SCHEMA_PATH.read_text())


def test_minimal_ok_result_passes(schema):
    result = {
        "tab": "Build with Claude Code",
        "group": "Agents",
        "status": "ok",
        "records": [],
        "empty_pages": [],
        "errors": [],
    }
    jsonschema.validate(result, schema)


def test_full_result_passes(schema):
    result = {
        "tab": "Reference",
        "group": "Reference",
        "status": "partial",
        "records": [
            {
                "id": "hook-input-via-stdin",
                "type": "qualitative",
                "proposition": "...",
                "verifier": {"kind": "llm-judge", "rubric": "..." * 10},
                "source": {
                    "url": "https://code.claude.com/docs/en/hooks",
                    "fetched_at": "2026-05-02T02:00:00Z",
                    "quote": "Command hooks read stdin",
                },
                "severity": "critical",
                "category_hint": "hooks",
                "page": "en/hooks",
            }
        ],
        "empty_pages": [
            {
                "page": "en/troubleshoot-install",
                "reason": "high-level guide; no verifiable schema",
                "suspicious": False,
            }
        ],
        "errors": [
            {"page": "en/some-broken", "reason": "fetch failed: 404"}
        ],
    }
    jsonschema.validate(result, schema)


def test_invalid_status_fails(schema):
    result = {
        "tab": "Reference",
        "group": "Reference",
        "status": "weird-status",
        "records": [],
        "empty_pages": [],
        "errors": [],
    }
    with pytest.raises(jsonschema.ValidationError):
        jsonschema.validate(result, schema)


def test_record_missing_category_hint_fails(schema):
    result = {
        "tab": "Reference",
        "group": "Reference",
        "status": "ok",
        "records": [
            {
                "id": "x",
                "type": "programmatic",
                "proposition": "p",
                "verifier": {"kind": "regex", "pattern": "."},
                "source": {"url": "https://e.com", "fetched_at": "2026-05-02T02:00:00Z", "quote": "qqqqq"},
                "severity": "important",
                # category_hint 누락
                "page": "en/x",
            }
        ],
        "empty_pages": [],
        "errors": [],
    }
    with pytest.raises(jsonschema.ValidationError):
        jsonschema.validate(result, schema)
