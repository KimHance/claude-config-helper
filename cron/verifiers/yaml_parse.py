"""YAML frontmatter parser + JSON Schema verifier."""
import json
import re
from pathlib import Path

import jsonschema
import yaml

FRONTMATTER_RE = re.compile(r"^---\s*\n(.*?)\n---\s*\n", re.DOTALL)


def _extract_frontmatter(target: Path) -> dict | None:
    body = target.read_text(encoding="utf-8")
    m = FRONTMATTER_RE.match(body)
    if not m:
        return None
    return yaml.safe_load(m.group(1)) or {}


def check_yaml_parse(item: dict, *, base_dir: Path) -> tuple[bool, str]:
    spec = item["verifier"]
    target = base_dir / spec["target"]
    if not target.exists():
        return False, f"target {spec['target']} not found"

    fm = _extract_frontmatter(target)
    if fm is None:
        return False, f"{spec['target']} has no YAML frontmatter"

    expected = spec.get("expect_keys", [])
    missing = [k for k in expected if k not in fm]
    if missing:
        return False, f"frontmatter missing keys: {missing}"
    return True, f"frontmatter parsed; keys present: {list(fm.keys())}"


def check_json_schema(item: dict, *, base_dir: Path) -> tuple[bool, str]:
    spec = item["verifier"]
    target = base_dir / spec["target"]
    if not target.exists():
        return False, f"target {spec['target']} not found"

    fm = _extract_frontmatter(target)
    if fm is None:
        return False, f"{spec['target']} has no YAML frontmatter to validate"

    schema = json.loads(Path(spec["schema_ref"]).read_text())
    try:
        jsonschema.validate(fm, schema)
    except jsonschema.ValidationError as e:
        return False, f"schema violation: {e.message}"
    return True, "frontmatter conforms to schema"
