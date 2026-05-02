import json
from pathlib import Path

import jsonschema
import pytest

SCHEMA_PATH = Path(__file__).parent.parent / "schema" / "item.schema.json"


@pytest.fixture
def schema():
    return json.loads(SCHEMA_PATH.read_text())


def test_programmatic_regex_item_passes(schema):
    item = {
        "id": "skill-name-charset",
        "type": "programmatic",
        "proposition": "name field matches lowercase + numbers + hyphens, length <= 64",
        "verifier": {
            "kind": "regex",
            "pattern": "^[a-z0-9-]+$",
            "max_length": 64,
        },
        "source": {
            "url": "https://code.claude.com/docs/en/skills#frontmatter-reference",
            "fetched_at": "2026-04-29T02:00:00Z",
            "quote": "Lowercase letters, numbers, and hyphens only (max 64 characters)",
        },
        "severity": "critical",
        "category": "skills",
    }
    jsonschema.validate(item, schema)


def test_qualitative_llm_judge_item_passes(schema):
    item = {
        "id": "skill-description-explains-when",
        "type": "qualitative",
        "proposition": "description explains WHEN to use",
        "verifier": {
            "kind": "llm-judge",
            "rubric": "Pass: includes timing language. Fail: only describes function.",
        },
        "source": {
            "url": "https://code.claude.com/docs/en/skills",
            "fetched_at": "2026-04-29T02:00:00Z",
            "quote": "What the skill does and when to use it.",
        },
        "severity": "important",
        "category": "skills",
    }
    jsonschema.validate(item, schema)


def test_missing_source_quote_fails(schema):
    item = {
        "id": "x",
        "type": "programmatic",
        "proposition": "p",
        "verifier": {"kind": "regex", "pattern": "."},
        "source": {
            "url": "https://example.com",
            "fetched_at": "2026-04-29T02:00:00Z",
            # quote 누락
        },
        "severity": "important",
        "category": "skills",
    }
    with pytest.raises(jsonschema.ValidationError):
        jsonschema.validate(item, schema)


def test_invalid_severity_fails(schema):
    item = {
        "id": "x",
        "type": "programmatic",
        "proposition": "p",
        "verifier": {"kind": "regex", "pattern": "."},
        "source": {
            "url": "https://example.com",
            "fetched_at": "2026-04-29T02:00:00Z",
            "quote": "q",
        },
        "severity": "blocker",  # invalid
        "category": "skills",
    }
    with pytest.raises(jsonschema.ValidationError):
        jsonschema.validate(item, schema)


def test_id_kebab_case_required(schema):
    item = {
        "id": "Skill_Name",  # invalid: 대문자 + 언더스코어
        "type": "programmatic",
        "proposition": "p",
        "verifier": {"kind": "regex", "pattern": "."},
        "source": {
            "url": "https://example.com",
            "fetched_at": "2026-04-29T02:00:00Z",
            "quote": "q",
        },
        "severity": "important",
        "category": "skills",
    }
    with pytest.raises(jsonschema.ValidationError):
        jsonschema.validate(item, schema)


def test_item_with_additional_sources_passes(schema):
    item = {
        "id": "hook-input-via-stdin",
        "type": "qualitative",
        "proposition": "command hooks read from stdin",
        "verifier": {"kind": "llm-judge", "rubric": "Pass if script reads from stdin (sys.stdin, etc.)."},
        "source": {
            "url": "https://code.claude.com/docs/en/hooks",
            "fetched_at": "2026-05-02T02:00:00Z",
            "quote": "Command hooks receive input via stdin",
        },
        "additional_sources": [
            {
                "url": "https://code.claude.com/docs/en/hooks-guide",
                "fetched_at": "2026-05-02T02:00:00Z",
                "quote": "For command hooks, input arrives on stdin as JSON",
            }
        ],
        "severity": "critical",
        "category": "hooks",
    }
    jsonschema.validate(item, schema)


def test_item_without_additional_sources_still_passes(schema):
    """additional_sources 는 옵션 — 없어도 valid."""
    item = {
        "id": "skill-name-charset",
        "type": "programmatic",
        "proposition": "name 이 lowercase + 숫자 + 하이픈, 64자 이하",
        "verifier": {"kind": "regex", "pattern": "^[a-z0-9-]+$", "max_length": 64},
        "source": {
            "url": "https://code.claude.com/docs/en/skills",
            "fetched_at": "2026-05-02T02:00:00Z",
            "quote": "Lowercase letters, numbers, and hyphens only",
        },
        "severity": "critical",
        "category": "skills",
    }
    jsonschema.validate(item, schema)


def test_additional_sources_invalid_entry_fails(schema):
    """additional_sources 의 각 entry 도 source 와 같은 형식이어야 함 (url+fetched_at+quote)."""
    item = {
        "id": "x",
        "type": "programmatic",
        "proposition": "p",
        "verifier": {"kind": "regex", "pattern": "."},
        "source": {
            "url": "https://example.com",
            "fetched_at": "2026-05-02T02:00:00Z",
            "quote": "valid quote",
        },
        "additional_sources": [
            {"url": "https://example.com"}  # quote, fetched_at 누락
        ],
        "severity": "important",
        "category": "skills",
    }
    with pytest.raises(jsonschema.ValidationError):
        jsonschema.validate(item, schema)
