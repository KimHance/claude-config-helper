import json
from pathlib import Path

import jsonschema
import yaml

REPO_ROOT = Path(__file__).parent.parent.parent
SCHEMA = REPO_ROOT / "cron" / "schema" / "category-mapping.schema.json"
MAPPING = REPO_ROOT / ".github" / "criteria-mapping.yml"


def test_mapping_yml_conforms_to_schema():
    schema = json.loads(SCHEMA.read_text())
    data = yaml.safe_load(MAPPING.read_text())
    jsonschema.validate(data, schema)
