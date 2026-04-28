"""Schema validator for cchelp criteria items."""
import json
from pathlib import Path
from typing import Iterable

import jsonschema
import yaml

SCHEMA_PATH = Path(__file__).parent.parent / "schema" / "item.schema.json"


class ValidationError(Exception):
    """Raised when a category file has structural issues beyond per-item schema."""


def _load_schema() -> dict:
    return json.loads(SCHEMA_PATH.read_text())


def validate_category_file(path: Path) -> list[str]:
    """
    Validate a category yml file.

    Returns list of error messages (empty if valid).
    Raises FileNotFoundError if path does not exist.
    """
    if not path.exists():
        raise FileNotFoundError(f"category file not found: {path}")

    items = yaml.safe_load(path.read_text()) or []
    if not isinstance(items, list):
        return [f"{path}: top-level must be a list of items"]

    schema = _load_schema()
    errors: list[str] = []
    seen_ids: set[str] = set()

    for idx, item in enumerate(items):
        # per-item JSON Schema check
        try:
            jsonschema.validate(item, schema)
        except jsonschema.ValidationError as e:
            errors.append(f"{path}[{idx}]: schema violation: {e.message}")
            continue

        # cross-item: id uniqueness
        item_id = item["id"]
        if item_id in seen_ids:
            errors.append(f"{path}[{idx}]: duplicate id '{item_id}'")
        seen_ids.add(item_id)

    return errors


def validate_all_categories(refs_dir: Path) -> dict[str, list[str]]:
    """Validate every *.yml under refs_dir. Returns {filename: errors}."""
    return {
        f.name: validate_category_file(f)
        for f in sorted(refs_dir.glob("*.yml"))
    }
