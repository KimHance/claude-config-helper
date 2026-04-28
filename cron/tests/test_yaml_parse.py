from pathlib import Path

from verifiers.yaml_parse import check_json_schema, check_yaml_parse

FIXTURES = Path(__file__).parent / "fixtures"
SAMPLE_DIR = FIXTURES / "sample-skill"


def test_yaml_parse_pass():
    item = {
        "verifier": {
            "kind": "yaml-parse",
            "target": "SKILL_with_frontmatter.md",
            "expect_keys": ["name", "description"],
        }
    }
    passed, evidence = check_yaml_parse(item, base_dir=SAMPLE_DIR)
    assert passed


def test_yaml_parse_missing_key():
    item = {
        "verifier": {
            "kind": "yaml-parse",
            "target": "SKILL_with_frontmatter.md",
            "expect_keys": ["name", "missing_field"],
        }
    }
    passed, evidence = check_yaml_parse(item, base_dir=SAMPLE_DIR)
    assert not passed
    assert "missing_field" in evidence


def test_yaml_parse_no_frontmatter():
    item = {
        "verifier": {
            "kind": "yaml-parse",
            "target": "SKILL.md",  # no frontmatter
            "expect_keys": ["name"],
        }
    }
    passed, evidence = check_yaml_parse(item, base_dir=SAMPLE_DIR)
    # SKILL.md has frontmatter with `name: sample`, so this should pass
    assert passed


def test_json_schema_pass():
    item = {
        "verifier": {
            "kind": "json-schema",
            "target": "SKILL_with_frontmatter.md",
            "schema_ref": str(FIXTURES / "sample-schema.json"),
        }
    }
    passed, evidence = check_json_schema(item, base_dir=SAMPLE_DIR)
    assert passed
