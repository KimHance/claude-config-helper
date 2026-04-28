from pathlib import Path

import pytest
import yaml

from verifiers.file_check import check_file_exists, check_substring
from verifiers.line_count import check_line_count
from verifiers.regex import check_regex

FIXTURES = Path(__file__).parent / "fixtures"
SAMPLE_DIR = FIXTURES / "sample-skill"


def test_regex_pass():
    item = {
        "verifier": {"kind": "regex", "pattern": "^[a-z0-9-]+$", "max_length": 64},
    }
    passed, evidence = check_regex(item, value="my-skill")
    assert passed
    assert "my-skill" in evidence


def test_regex_fail_pattern():
    item = {
        "verifier": {"kind": "regex", "pattern": "^[a-z0-9-]+$", "max_length": 64},
    }
    passed, evidence = check_regex(item, value="My_Skill")
    assert not passed
    assert "did not match pattern" in evidence


def test_regex_fail_max_length():
    item = {
        "verifier": {"kind": "regex", "pattern": "^[a-z0-9-]+$", "max_length": 5},
    }
    passed, evidence = check_regex(item, value="my-skill")
    assert not passed
    assert "exceeds max_length" in evidence


def test_line_count_pass():
    item = {"verifier": {"kind": "line-count", "target": "SKILL.md", "max": 500}}
    passed, evidence = check_line_count(item, base_dir=SAMPLE_DIR)
    assert passed
    assert "3 lines" in evidence


def test_line_count_fail():
    item = {"verifier": {"kind": "line-count", "target": "SKILL.md", "max": 2}}
    passed, evidence = check_line_count(item, base_dir=SAMPLE_DIR)
    assert not passed
    assert "exceeds" in evidence


def test_line_count_target_missing():
    item = {"verifier": {"kind": "line-count", "target": "MISSING.md", "max": 500}}
    passed, evidence = check_line_count(item, base_dir=SAMPLE_DIR)
    assert not passed
    assert "not found" in evidence


def test_file_exists_pass():
    item = {"verifier": {"kind": "file-exists", "target": "SKILL.md"}}
    passed, evidence = check_file_exists(item, base_dir=SAMPLE_DIR)
    assert passed


def test_file_exists_fail():
    item = {"verifier": {"kind": "file-exists", "target": "NOPE.md"}}
    passed, evidence = check_file_exists(item, base_dir=SAMPLE_DIR)
    assert not passed


def test_substring_pass():
    item = {"verifier": {"kind": "substring", "target": "SKILL.md", "needle": "name: sample"}}
    passed, evidence = check_substring(item, base_dir=SAMPLE_DIR)
    assert passed


def test_substring_fail():
    item = {"verifier": {"kind": "substring", "target": "SKILL.md", "needle": "missing-text"}}
    passed, evidence = check_substring(item, base_dir=SAMPLE_DIR)
    assert not passed
    assert "not found" in evidence
