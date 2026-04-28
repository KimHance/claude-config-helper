from pathlib import Path

import pytest

from verifiers.schema_validator import ValidationError, validate_category_file

FIXTURES = Path(__file__).parent / "fixtures"


def test_valid_yml_passes():
    errors = validate_category_file(FIXTURES / "valid_skills.yml")
    assert errors == []


def test_duplicate_id_rejected():
    errors = validate_category_file(FIXTURES / "invalid_dup_id.yml")
    assert any("duplicate id" in e for e in errors)


def test_missing_file_raises():
    with pytest.raises(FileNotFoundError):
        validate_category_file(FIXTURES / "nonexistent.yml")
