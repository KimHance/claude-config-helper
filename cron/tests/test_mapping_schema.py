import json
from pathlib import Path

import jsonschema
import pytest
import yaml

REPO_ROOT = Path(__file__).parent.parent.parent
SCHEMA = REPO_ROOT / "cron" / "schema" / "category-binding.schema.json"


@pytest.fixture
def schema():
    return json.loads(SCHEMA.read_text())


def test_valid_mapping_passes(schema):
    data = {
        "categories": [
            {
                "name": "skills",
                "bind": [
                    {"tab": "Build with Claude Code", "group": "Tools and plugins", "page_filter": "skills"}
                ],
                "review_file": "skills/review/references/skills.yml",
                "benchmark": True,
            },
            {
                "name": "hooks",
                "bind": [
                    {"tab": "Build with Claude Code", "group": "Automation", "page_filter": "hooks*"},
                    {"tab": "Reference", "group": "Reference", "page_filter": "hooks*"}
                ],
                "review_file": "skills/review/references/hooks.yml",
            }
        ],
        "excluded_tabs": ["Agent SDK", "What's New"],
        "priority": {"tabs": ["Reference", "Configuration", "Administration", "Build with Claude Code"]}
    }
    jsonschema.validate(data, schema)


def test_missing_categories_fails(schema):
    with pytest.raises(jsonschema.ValidationError):
        jsonschema.validate({"excluded_tabs": []}, schema)


def test_category_without_bind_fails(schema):
    data = {
        "categories": [
            {"name": "skills", "review_file": "skills.yml"}  # bind 누락
        ]
    }
    with pytest.raises(jsonschema.ValidationError):
        jsonschema.validate(data, schema)


def test_bind_entry_requires_tab_and_group(schema):
    data = {
        "categories": [
            {
                "name": "skills",
                "bind": [{"tab": "Reference"}],  # group 누락
                "review_file": "skills.yml",
            }
        ]
    }
    with pytest.raises(jsonschema.ValidationError):
        jsonschema.validate(data, schema)


def test_actual_mapping_yml_conforms(schema):
    """실제 .github/criteria-mapping.yml 이 새 schema 통과해야 함 (Task 9 후)."""
    data = yaml.safe_load((REPO_ROOT / ".github" / "criteria-mapping.yml").read_text())
    # 현재 시점엔 옛 형식이라 fail; Task 9 에서 갱신 후 pass
    # 본 테스트는 conditional skip 이 아닌, Task 9 후 자연 통과
    jsonschema.validate(data, schema)
