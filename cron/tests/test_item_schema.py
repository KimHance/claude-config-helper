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
