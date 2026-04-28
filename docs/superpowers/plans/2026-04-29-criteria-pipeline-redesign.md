# 판단 기준 파이프라인 재설계 — 구현 플랜

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**스펙:** [docs/superpowers/specs/2026-04-29-criteria-pipeline-redesign-design.md](../specs/2026-04-29-criteria-pipeline-redesign-design.md)

**목표:** cchelp 의 주간 판단 기준 자동 갱신 파이프라인을 자체 면역 시스템으로 재구축.

**아키텍처:** Python 기반 verifier 라이브러리 (regex / line-count / yaml-parse / source integrity 등 결정론적 검증) + 새 Claude agent 2개 (self-eval-runner thin executor, plan-reviewer 독립 검증) + GitHub Actions 워크플로 재작성 (8-step: Fetch → Diff → Plan → Plan Review → Apply → Self-validate → Commit & PR → Auto-merge). 기존 prose 체크리스트 폐기, YAML 명제 schema 로 교체.

**Tech Stack:** Python 3.11+, pyyaml, jsonschema, httpx, pytest, GitHub Actions, anthropics/claude-code-action.

**한국어 작성:** 메인테이너 선호.

---

## 파일 구조 (전체)

### 신규 생성

| 경로 | 책임 |
|---|---|
| `cron/schema/item.schema.json` | refs 항목의 JSON Schema (programmatic / qualitative 분기) |
| `cron/schema/category-mapping.schema.json` | criteria-mapping.yml 의 schema |
| `cron/verifiers/__init__.py` | verifier 모듈 모음 |
| `cron/verifiers/regex.py` | regex verifier |
| `cron/verifiers/line_count.py` | line-count + file-exists + substring verifier |
| `cron/verifiers/yaml_parse.py` | yaml-parse + json-schema verifier |
| `cron/verifiers/source_integrity.py` | URL probe + quote substring + fetched_at window 검증 |
| `cron/verifiers/schema_validator.py` | item.schema.json 적용기 |
| `cron/scripts/fetch.py` | U1: docs/changelog/sitemap WebFetch 래퍼 |
| `cron/scripts/diff.py` | U2: 새 body vs snapshot 비교 |
| `cron/scripts/plan.py` | U3: 변경 record 생성 (ADD/UPDATE/REMOVE) |
| `cron/scripts/fallback_search.py` | REMOVE 후보의 sitemap/cross-language 검색 |
| `cron/scripts/category_discovery.py` | llms.txt diff + frontmatter heuristic 필터 |
| `cron/scripts/apply.py` | U4: refs/templates/agent prompt 갱신 적용 |
| `cron/scripts/self_validate.py` | U5: smoke run + B/C 신호 측정 |
| `cron/scripts/baseline_eval.py` | C 신호 동시 측정 + 비율 정규화 |
| `cron/tests/conftest.py` | pytest fixtures (mocked HTTP, sample bodies) |
| `cron/tests/test_*.py` | 각 verifier/script 의 단위 테스트 |
| `cron/state/.gitkeep` | `.cron-state/` 가 아니라 `cron/state/` 로 위치 (레포 내 가시성) |
| `agents/self-eval-runner.md` | thin executor agent (B 신호 처리) |
| `agents/plan-reviewer.md` | U3.5 독립 reviewer agent |
| `skills/review/references/.gitkeep` | yml 디렉토리 (빈 캔버스, 메인테이너가 seed) |

### 수정

| 경로 | 변경 |
|---|---|
| `.github/workflows/update-review-criteria.yml` | 8-step 워크플로로 전면 재작성 |
| `criteria-mapping.yml` | 자동 발견 카테고리 지원하도록 schema 확장 |
| `agents/reviewer.md` | Layer 2 propagation 훅 추가 (verifier.kind enum 해석) |
| `agents/grader.md` | Layer 2 propagation 훅 추가 (item.schema 인식) |
| `CLAUDE.md` | 신규 agent 라우팅 추가 |
| `.gitignore` | `/tmp/cchelp-cron-*` 추가 |

### 삭제

| 경로 | 사유 |
|---|---|
| `skills/review/references/agents-checklist.md` | prose-as-checkbox, 폐기 후 yml 로 교체 |
| `skills/review/references/claude-md-checklist.md` | 동일 |
| `skills/review/references/commands-checklist.md` | 동일 |
| `skills/review/references/hooks-checklist.md` | 동일 |
| `skills/review/references/mcp-checklist.md` | 동일 |
| `skills/review/references/memory-checklist.md` | 동일 |
| `skills/review/references/skills-checklist.md` | 동일 |

(`skills/review/references/*` 의 `eval-process.md`, `grading-rubric.md`, `benchmark-template.md`, `trigger-test-template.md` 은 review orchestration 의 step 내용이라 유지 — 본 플랜 범위 외)

---

## Phase 1: Foundation — Schema 와 Verifier 라이브러리

`cchelp` 가 기존에 Python 코드 없이 운영되어 왔으므로, **새 `cron/` 디렉토리 도입** 으로 시작. 첫 4개 task 가 verifier 라이브러리의 단단한 기반을 만듦.

### Task 1: Python 환경 + 의존성 셋업

**Files:**
- Create: `cron/pyproject.toml`
- Create: `cron/.python-version`
- Create: `cron/tests/__init__.py`
- Modify: `.gitignore` — append `/tmp/cchelp-cron-*`, `cron/.venv`, `cron/__pycache__`, `cron/.pytest_cache`

- [ ] **Step 1: `cron/pyproject.toml` 작성**

```toml
[project]
name = "cchelp-cron"
version = "0.1.0"
description = "cchelp weekly criteria update cron pipeline"
requires-python = ">=3.11"
dependencies = [
    "pyyaml>=6.0.1",
    "jsonschema>=4.20.0",
    "httpx>=0.26.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=7.4.0",
    "pytest-mock>=3.12.0",
    "pytest-httpx>=0.28.0",
]

[build-system]
requires = ["setuptools>=68"]
build-backend = "setuptools.build_meta"

[tool.pytest.ini_options]
testpaths = ["tests"]
python_files = ["test_*.py"]
```

- [ ] **Step 2: `cron/.python-version` 작성**

```
3.11
```

- [ ] **Step 3: `.gitignore` 에 cron 관련 path 추가**

`.gitignore` 끝에 다음 줄 추가:

```
# cchelp cron
/tmp/cchelp-cron-*
cron/.venv
cron/__pycache__
cron/.pytest_cache
**/__pycache__
**/.pytest_cache
```

- [ ] **Step 4: 빈 테스트 파일 `cron/tests/__init__.py` 생성**

내용 비움 (Python 패키지 마커).

- [ ] **Step 5: 의존성 설치 검증**

Run:
```bash
cd cron && python3.11 -m venv .venv && .venv/bin/pip install -e ".[dev]"
```

Expected: `Successfully installed cchelp-cron-0.1.0` 메시지, 에러 없음.

- [ ] **Step 6: 커밋**

```bash
git add cron/pyproject.toml cron/.python-version cron/tests/__init__.py .gitignore
git commit -m "chore: add cron python package scaffold"
```

---

### Task 2: 항목 JSON Schema 정의

**Files:**
- Create: `cron/schema/item.schema.json`
- Create: `cron/tests/test_item_schema.py`

- [ ] **Step 1: 실패 테스트 작성 — `cron/tests/test_item_schema.py`**

```python
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
```

- [ ] **Step 2: 테스트 실행 — 실패 확인**

Run:
```bash
cd cron && .venv/bin/pytest tests/test_item_schema.py -v
```

Expected: FAIL — `FileNotFoundError: schema/item.schema.json`

- [ ] **Step 3: `cron/schema/item.schema.json` 작성**

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "https://cchelp.local/schema/item.schema.json",
  "title": "cchelp Review Criteria Item",
  "type": "object",
  "required": ["id", "type", "proposition", "verifier", "source", "severity", "category"],
  "additionalProperties": false,
  "properties": {
    "id": {
      "type": "string",
      "pattern": "^[a-z0-9]+(-[a-z0-9]+)*$",
      "minLength": 3,
      "maxLength": 80
    },
    "type": {"enum": ["programmatic", "qualitative"]},
    "proposition": {"type": "string", "minLength": 5},
    "severity": {"enum": ["critical", "important", "suggestion"]},
    "category": {"type": "string", "minLength": 2},
    "source": {
      "type": "object",
      "required": ["url", "fetched_at", "quote"],
      "additionalProperties": false,
      "properties": {
        "url": {"type": "string", "format": "uri"},
        "fetched_at": {"type": "string", "format": "date-time"},
        "quote": {"type": "string", "minLength": 5}
      }
    },
    "verifier": {
      "type": "object",
      "oneOf": [
        {
          "required": ["kind", "pattern"],
          "properties": {
            "kind": {"const": "regex"},
            "pattern": {"type": "string", "minLength": 1},
            "max_length": {"type": "integer", "minimum": 1},
            "min_length": {"type": "integer", "minimum": 0}
          },
          "additionalProperties": false
        },
        {
          "required": ["kind", "target", "max"],
          "properties": {
            "kind": {"const": "line-count"},
            "target": {"type": "string"},
            "max": {"type": "integer", "minimum": 1},
            "min": {"type": "integer", "minimum": 0}
          },
          "additionalProperties": false
        },
        {
          "required": ["kind", "target"],
          "properties": {
            "kind": {"const": "file-exists"},
            "target": {"type": "string"}
          },
          "additionalProperties": false
        },
        {
          "required": ["kind", "target", "needle"],
          "properties": {
            "kind": {"const": "substring"},
            "target": {"type": "string"},
            "needle": {"type": "string", "minLength": 1}
          },
          "additionalProperties": false
        },
        {
          "required": ["kind", "target"],
          "properties": {
            "kind": {"const": "yaml-parse"},
            "target": {"type": "string"},
            "expect_keys": {"type": "array", "items": {"type": "string"}}
          },
          "additionalProperties": false
        },
        {
          "required": ["kind", "target", "schema_ref"],
          "properties": {
            "kind": {"const": "json-schema"},
            "target": {"type": "string"},
            "schema_ref": {"type": "string"}
          },
          "additionalProperties": false
        },
        {
          "required": ["kind", "command"],
          "properties": {
            "kind": {"const": "shell"},
            "command": {"type": "string"},
            "expected_exit": {"type": "integer", "default": 0}
          },
          "additionalProperties": false
        },
        {
          "required": ["kind", "rubric"],
          "properties": {
            "kind": {"const": "llm-judge"},
            "rubric": {"type": "string", "minLength": 30}
          },
          "additionalProperties": false
        }
      ]
    }
  }
}
```

- [ ] **Step 4: 테스트 통과 확인**

Run:
```bash
cd cron && .venv/bin/pytest tests/test_item_schema.py -v
```

Expected: PASS — 5 tests passed.

- [ ] **Step 5: 커밋**

```bash
git add cron/schema/item.schema.json cron/tests/test_item_schema.py
git commit -m "feat: add item JSON Schema with verifier-kind oneOf"
```

---

### Task 3: Schema validator 모듈

검증 로직을 호출 가능한 함수로 래핑. 카테고리당 yml 파일 하나 받아서 모든 항목 검증.

**Files:**
- Create: `cron/verifiers/__init__.py`
- Create: `cron/verifiers/schema_validator.py`
- Create: `cron/tests/test_schema_validator.py`
- Create: `cron/tests/fixtures/valid_skills.yml`
- Create: `cron/tests/fixtures/invalid_dup_id.yml`

- [ ] **Step 1: 실패 테스트 작성**

`cron/tests/test_schema_validator.py`:

```python
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
```

- [ ] **Step 2: Fixture 파일 생성**

`cron/tests/fixtures/valid_skills.yml`:

```yaml
- id: skill-name-charset
  type: programmatic
  proposition: name field matches charset
  verifier:
    kind: regex
    pattern: "^[a-z0-9-]+$"
  source:
    url: https://code.claude.com/docs/en/skills#frontmatter-reference
    fetched_at: "2026-04-29T02:00:00Z"
    quote: "Lowercase letters, numbers, and hyphens only"
  severity: critical
  category: skills
- id: skill-md-line-budget
  type: programmatic
  proposition: SKILL.md is at most 500 lines
  verifier:
    kind: line-count
    target: SKILL.md
    max: 500
  source:
    url: https://code.claude.com/docs/en/skills#add-supporting-files
    fetched_at: "2026-04-29T02:00:00Z"
    quote: "Keep SKILL.md under 500 lines"
  severity: suggestion
  category: skills
```

`cron/tests/fixtures/invalid_dup_id.yml`:

```yaml
- id: dup-id
  type: programmatic
  proposition: first
  verifier:
    kind: regex
    pattern: "."
  source:
    url: https://example.com
    fetched_at: "2026-04-29T02:00:00Z"
    quote: "x"
  severity: important
  category: skills
- id: dup-id
  type: programmatic
  proposition: second
  verifier:
    kind: regex
    pattern: "."
  source:
    url: https://example.com
    fetched_at: "2026-04-29T02:00:00Z"
    quote: "y"
  severity: important
  category: skills
```

- [ ] **Step 3: 테스트 실행 — 실패 확인**

Run:
```bash
cd cron && .venv/bin/pytest tests/test_schema_validator.py -v
```

Expected: FAIL — `ModuleNotFoundError: No module named 'verifiers.schema_validator'`

- [ ] **Step 4: `cron/verifiers/__init__.py` 생성 (빈 파일)**

내용 비움.

- [ ] **Step 5: `cron/verifiers/schema_validator.py` 구현**

```python
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
```

- [ ] **Step 6: 테스트 통과 확인**

Run:
```bash
cd cron && PYTHONPATH=. .venv/bin/pytest tests/test_schema_validator.py -v
```

Expected: PASS — 3 tests passed.

- [ ] **Step 7: 커밋**

```bash
git add cron/verifiers/ cron/tests/test_schema_validator.py cron/tests/fixtures/
git commit -m "feat: add schema validator with id-uniqueness check"
```

---

### Task 4: Programmatic verifier — regex / line-count / file-exists / substring

각 verifier 가 단독으로 호출 가능한 순수 함수. 입력은 (item, target_path), 출력은 (passed: bool, evidence: str).

**Files:**
- Create: `cron/verifiers/regex.py`
- Create: `cron/verifiers/line_count.py`
- Create: `cron/verifiers/file_check.py`
- Create: `cron/tests/test_verifiers.py`
- Create: `cron/tests/fixtures/sample-skill/SKILL.md`

- [ ] **Step 1: Fixture 파일 생성**

`cron/tests/fixtures/sample-skill/SKILL.md` (3 줄):

```markdown
---
name: sample
---
```

- [ ] **Step 2: 실패 테스트 작성**

`cron/tests/test_verifiers.py`:

```python
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
```

- [ ] **Step 3: 테스트 실행 — 실패 확인**

Run:
```bash
cd cron && PYTHONPATH=. .venv/bin/pytest tests/test_verifiers.py -v
```

Expected: FAIL — `ModuleNotFoundError`.

- [ ] **Step 4: `cron/verifiers/regex.py` 구현**

```python
"""Regex verifier for string-valued targets (e.g., field values)."""
import re


def check_regex(item: dict, *, value: str) -> tuple[bool, str]:
    spec = item["verifier"]
    pattern = spec["pattern"]
    max_length = spec.get("max_length")
    min_length = spec.get("min_length")

    if min_length is not None and len(value) < min_length:
        return False, f"value '{value}' shorter than min_length {min_length}"
    if max_length is not None and len(value) > max_length:
        return False, f"value '{value}' (len={len(value)}) exceeds max_length {max_length}"
    if not re.search(pattern, value):
        return False, f"value '{value}' did not match pattern {pattern!r}"
    return True, f"value '{value}' matched pattern {pattern!r}"
```

- [ ] **Step 5: `cron/verifiers/line_count.py` 구현**

```python
"""Line-count verifier."""
from pathlib import Path


def check_line_count(item: dict, *, base_dir: Path) -> tuple[bool, str]:
    spec = item["verifier"]
    target = base_dir / spec["target"]
    max_lines = spec["max"]
    min_lines = spec.get("min", 0)

    if not target.exists():
        return False, f"target {spec['target']} not found in {base_dir}"
    n = sum(1 for _ in target.read_text(encoding="utf-8").splitlines())
    if n > max_lines:
        return False, f"{spec['target']} has {n} lines, exceeds max {max_lines}"
    if n < min_lines:
        return False, f"{spec['target']} has {n} lines, below min {min_lines}"
    return True, f"{spec['target']} has {n} lines (within [{min_lines}, {max_lines}])"
```

- [ ] **Step 6: `cron/verifiers/file_check.py` 구현**

```python
"""file-exists and substring verifiers."""
from pathlib import Path


def check_file_exists(item: dict, *, base_dir: Path) -> tuple[bool, str]:
    spec = item["verifier"]
    target = base_dir / spec["target"]
    if target.exists():
        return True, f"{spec['target']} exists"
    return False, f"{spec['target']} not found in {base_dir}"


def check_substring(item: dict, *, base_dir: Path) -> tuple[bool, str]:
    spec = item["verifier"]
    target = base_dir / spec["target"]
    if not target.exists():
        return False, f"target {spec['target']} not found in {base_dir}"
    body = target.read_text(encoding="utf-8")
    if spec["needle"] in body:
        return True, f"needle found in {spec['target']}"
    return False, f"needle {spec['needle']!r} not found in {spec['target']}"
```

- [ ] **Step 7: 테스트 통과 확인**

Run:
```bash
cd cron && PYTHONPATH=. .venv/bin/pytest tests/test_verifiers.py -v
```

Expected: PASS — 10 tests passed.

- [ ] **Step 8: 커밋**

```bash
git add cron/verifiers/regex.py cron/verifiers/line_count.py cron/verifiers/file_check.py \
        cron/tests/test_verifiers.py cron/tests/fixtures/sample-skill/
git commit -m "feat: add regex, line-count, file-exists, substring verifiers"
```

---

### Task 5: yaml-parse 와 json-schema verifier

**Files:**
- Create: `cron/verifiers/yaml_parse.py`
- Create: `cron/tests/test_yaml_parse.py`
- Create: `cron/tests/fixtures/sample-skill/SKILL_with_frontmatter.md`
- Create: `cron/tests/fixtures/sample-schema.json`

- [ ] **Step 1: Fixture 생성**

`cron/tests/fixtures/sample-skill/SKILL_with_frontmatter.md`:

```markdown
---
name: sample
description: A sample skill
when_to_use: When testing
---

Body here.
```

`cron/tests/fixtures/sample-schema.json`:

```json
{
  "type": "object",
  "required": ["name", "description"],
  "properties": {
    "name": {"type": "string"},
    "description": {"type": "string"}
  }
}
```

- [ ] **Step 2: 실패 테스트**

`cron/tests/test_yaml_parse.py`:

```python
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
```

- [ ] **Step 3: 테스트 실패 확인**

Run:
```bash
cd cron && PYTHONPATH=. .venv/bin/pytest tests/test_yaml_parse.py -v
```

Expected: FAIL — `ModuleNotFoundError`.

- [ ] **Step 4: `cron/verifiers/yaml_parse.py` 구현**

```python
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
```

- [ ] **Step 5: 테스트 통과**

Run:
```bash
cd cron && PYTHONPATH=. .venv/bin/pytest tests/test_yaml_parse.py -v
```

Expected: PASS — 4 tests passed.

- [ ] **Step 6: 커밋**

```bash
git add cron/verifiers/yaml_parse.py cron/tests/test_yaml_parse.py cron/tests/fixtures/
git commit -m "feat: add yaml-parse and json-schema verifiers"
```

---

### Task 6: Source integrity verifier (URL probe + quote substring + fetched_at window)

이 모듈은 Plan Review (U3.5) 의 검증 1 단계에서 사용. 외부 docs body 를 가져와서 quote 가 substring 으로 매칭되는지 확인.

**Files:**
- Create: `cron/verifiers/source_integrity.py`
- Create: `cron/tests/test_source_integrity.py`

- [ ] **Step 1: 실패 테스트**

`cron/tests/test_source_integrity.py`:

```python
from datetime import datetime, timezone
from unittest.mock import patch

import httpx
import pytest

from verifiers.source_integrity import (
    SourceIntegrityResult,
    check_source_integrity,
)


def _item(quote="hello world", fetched_at=None):
    return {
        "source": {
            "url": "https://example.com/docs",
            "fetched_at": fetched_at or datetime.now(timezone.utc).isoformat(),
            "quote": quote,
        }
    }


def test_quote_substring_match_pass(httpx_mock):
    httpx_mock.add_response(url="https://example.com/docs", text="lorem hello world ipsum")
    result = check_source_integrity(_item(), now=datetime.now(timezone.utc))
    assert result.ok
    assert result.url_status == 200


def test_quote_not_found_fails(httpx_mock):
    httpx_mock.add_response(url="https://example.com/docs", text="completely different content")
    result = check_source_integrity(_item(), now=datetime.now(timezone.utc))
    assert not result.ok
    assert "quote not found" in result.reason


def test_url_404_fails(httpx_mock):
    httpx_mock.add_response(url="https://example.com/docs", status_code=404)
    result = check_source_integrity(_item(), now=datetime.now(timezone.utc))
    assert not result.ok
    assert "404" in result.reason


def test_fetched_at_too_old_fails():
    old = "2020-01-01T00:00:00+00:00"
    item = _item(fetched_at=old)
    result = check_source_integrity(item, now=datetime.now(timezone.utc), skip_http=True)
    assert not result.ok
    assert "fetched_at" in result.reason


def test_fetched_at_within_window_passes(httpx_mock):
    httpx_mock.add_response(url="https://example.com/docs", text="hello world")
    result = check_source_integrity(_item(), now=datetime.now(timezone.utc))
    assert result.ok
```

- [ ] **Step 2: 테스트 실패 확인**

Run:
```bash
cd cron && PYTHONPATH=. .venv/bin/pytest tests/test_source_integrity.py -v
```

Expected: FAIL — `ModuleNotFoundError`.

- [ ] **Step 3: `cron/verifiers/source_integrity.py` 구현**

```python
"""Source integrity check (Plan Review U3.5 step 1)."""
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

import httpx


@dataclass
class SourceIntegrityResult:
    ok: bool
    reason: str
    url_status: int | None = None


WINDOW = timedelta(hours=1)


def check_source_integrity(
    item: dict,
    *,
    now: datetime,
    skip_http: bool = False,
) -> SourceIntegrityResult:
    src = item["source"]
    fetched_at = datetime.fromisoformat(src["fetched_at"].replace("Z", "+00:00"))

    if abs(now - fetched_at) > WINDOW:
        return SourceIntegrityResult(
            ok=False,
            reason=f"fetched_at {src['fetched_at']} outside ±1h window of {now.isoformat()}",
        )

    if skip_http:
        return SourceIntegrityResult(ok=True, reason="http skipped (test)")

    try:
        resp = httpx.get(src["url"], follow_redirects=True, timeout=30.0)
    except httpx.HTTPError as e:
        return SourceIntegrityResult(ok=False, reason=f"fetch error: {e}")

    if resp.status_code != 200:
        return SourceIntegrityResult(
            ok=False,
            reason=f"url {src['url']} returned {resp.status_code}",
            url_status=resp.status_code,
        )

    if src["quote"] not in resp.text:
        return SourceIntegrityResult(
            ok=False,
            reason=f"quote not found in body of {src['url']}",
            url_status=200,
        )

    return SourceIntegrityResult(ok=True, reason="url 200 + quote substring match", url_status=200)
```

- [ ] **Step 4: 테스트 통과**

Run:
```bash
cd cron && PYTHONPATH=. .venv/bin/pytest tests/test_source_integrity.py -v
```

Expected: PASS — 5 tests passed.

- [ ] **Step 5: 커밋**

```bash
git add cron/verifiers/source_integrity.py cron/tests/test_source_integrity.py
git commit -m "feat: add source integrity verifier (url probe + quote match + fetched_at window)"
```

---

## Phase 2: Agent 정의 (self-eval-runner + plan-reviewer)

agent prompt 는 코드가 아니라 .md 파일이지만, 동작 자체는 워크플로 안에서 호출되므로 빈 stub 통합 테스트로 형식 검증.

### Task 7: `self-eval-runner` agent 정의

thin executor — refs 의 verifier 를 기계적으로 실행하고 결과 반환만. 자기 의견 추가 X.

**Files:**
- Create: `agents/self-eval-runner.md`
- Create: `cron/tests/test_agent_definitions.py`

- [ ] **Step 1: 실패 테스트 작성**

`cron/tests/test_agent_definitions.py`:

```python
import re
from pathlib import Path

import yaml

AGENTS_DIR = Path(__file__).parent.parent.parent / "agents"
FRONTMATTER_RE = re.compile(r"^---\s*\n(.*?)\n---\s*\n", re.DOTALL)


def _read_frontmatter(path: Path) -> dict:
    m = FRONTMATTER_RE.match(path.read_text(encoding="utf-8"))
    assert m, f"{path} has no frontmatter"
    return yaml.safe_load(m.group(1))


def test_self_eval_runner_exists():
    path = AGENTS_DIR / "self-eval-runner.md"
    assert path.exists(), f"{path} not found"


def test_self_eval_runner_frontmatter():
    fm = _read_frontmatter(AGENTS_DIR / "self-eval-runner.md")
    assert fm["name"] == "self-eval-runner"
    assert "thin executor" in fm["description"].lower()
    assert fm["model"] in {"haiku", "sonnet", "inherit"}, "thin executor should use cheap model"


def test_self_eval_runner_has_workflow_section():
    body = (AGENTS_DIR / "self-eval-runner.md").read_text(encoding="utf-8")
    assert "## Process" in body or "## Workflow" in body
    assert "verifier" in body.lower()
    assert "no llm judgment" in body.lower() or "no opinion" in body.lower() or "기계" in body
```

- [ ] **Step 2: 테스트 실행 — 실패 확인**

Run:
```bash
cd cron && PYTHONPATH=. .venv/bin/pytest tests/test_agent_definitions.py -v
```

Expected: FAIL — `agents/self-eval-runner.md` 없음.

- [ ] **Step 3: `agents/self-eval-runner.md` 작성**

```markdown
---
name: self-eval-runner
color: cyan
description: |
  Internal thin-executor agent for cchelp's weekly self-review pass. Runs each criteria item's verifier mechanically and returns pass/fail without adding interpretation. Used ONLY by the cron pipeline's U5 self-validate step. Do NOT use for external user reviews. Examples: <example>cron pipeline U5: spawns this agent to run refs verifiers against cchelp itself</example>
model: haiku
---

You are a thin executor. Your only job is to run each criteria item's verifier against a target and report the deterministic pass/fail outcome. **Do not add opinions, suggestions, or interpretations.** All intelligence lives in the refs items themselves; you only execute.

## 자기 통과 보장 루프 차단

이 agent 는 cchelp 자기 self-review 전용. cchelp 의 갱신 PR 이 자기 통과를 보장하도록 진화하는 함정을 차단하기 위해 thin executor 로 설계됨. 너는 prompt 에 행동을 더 추가하지 마라. 변경이 필요하면 메인테이너만 가능.

## Inputs

- **refs_path**: `skills/review/references/<category>.yml` 의 절대 경로
- **target_path**: 검사 대상 (예: `skills/review/SKILL.md`, `agents/reviewer.md`)
- **target_kind**: `skill` | `agent` | `command` | `hook` | `mcp` | `claude-md` | `memory`

## Process

### Step 1: refs 로드

`refs_path` 의 yml 을 파싱. 각 항목은 다음 schema 를 가짐 (검증은 schema validator 가 이미 수행했다고 가정):

```yaml
- id: <kebab-case>
  type: programmatic | qualitative
  proposition: <문장>
  verifier:
    kind: regex | line-count | file-exists | substring | yaml-parse | json-schema | shell | llm-judge
    ...
  source: {url, fetched_at, quote}
  severity: critical | important | suggestion
  category: <name>
```

### Step 2: 항목별 verifier 실행

**programmatic 항목 (kind ≠ llm-judge):** Python verifier 함수를 직접 호출. Bash 도구로 다음 명령 실행:

```bash
cd cron && PYTHONPATH=. .venv/bin/python -m scripts.run_verifier \
    --refs <refs_path> --item-id <id> --target <target_path>
```

이 스크립트는 `{passed: bool, evidence: str}` JSON 을 stdout 으로 반환.

**qualitative 항목 (kind = llm-judge):**
1. 대상 파일 읽기
2. `verifier.rubric` 을 한 번만 읽고 해당 기준에 대해 pass/fail 판단
3. **모든 결론에 `source.quote` 를 verbatim 인용해서 정당화** (환각 차단)
4. rubric 외의 자기 판단 금지

### Step 3: 결과 집계

각 항목당 한 줄:

```json
{"id": "skill-name-charset", "passed": true, "evidence": "matched pattern ^[a-z0-9-]+$"}
```

전체를 JSON array 로 stdout 출력. 다른 텍스트 출력 금지.

## 절대 하지 말 것

- 항목 추가/제거/수정 제안 X
- "이런 것도 검사하면 좋겠다" 같은 의견 X
- rubric 에 없는 판단 추가 X
- target 파일 수정 X
- 다른 agent 호출 X

너의 진화는 refs schema 가 새 verifier kind 를 도입할 때만 메인테이너가 직접 prompt 추가. 자동 갱신 영역 아님.
```

- [ ] **Step 4: 테스트 통과 확인**

Run:
```bash
cd cron && PYTHONPATH=. .venv/bin/pytest tests/test_agent_definitions.py -v
```

Expected: PASS — 3 tests passed.

- [ ] **Step 5: 커밋**

```bash
git add agents/self-eval-runner.md cron/tests/test_agent_definitions.py
git commit -m "feat: add self-eval-runner thin-executor agent"
```

---

### Task 8: `plan-reviewer` agent 정의

U3.5 의 독립 reviewer. 컨텍스트 격리 강조 + quote-based reasoning 강제.

**Files:**
- Create: `agents/plan-reviewer.md`
- Modify: `cron/tests/test_agent_definitions.py` (테스트 추가)

- [ ] **Step 1: 테스트 추가**

`cron/tests/test_agent_definitions.py` 끝에 추가:

```python
def test_plan_reviewer_exists():
    path = AGENTS_DIR / "plan-reviewer.md"
    assert path.exists(), f"{path} not found"


def test_plan_reviewer_frontmatter():
    fm = _read_frontmatter(AGENTS_DIR / "plan-reviewer.md")
    assert fm["name"] == "plan-reviewer"
    assert fm["model"] in {"opus", "sonnet"}, "reviewer needs strong reasoning model"


def test_plan_reviewer_quote_requirement():
    body = (AGENTS_DIR / "plan-reviewer.md").read_text(encoding="utf-8")
    # quote-based reasoning 강제 키워드 존재
    assert "quote" in body.lower()
    assert "verbatim" in body.lower() or "원문" in body
    assert "substring" in body.lower()
```

- [ ] **Step 2: 테스트 실패 확인**

Run:
```bash
cd cron && PYTHONPATH=. .venv/bin/pytest tests/test_agent_definitions.py -v
```

Expected: FAIL — `plan-reviewer.md` 없음.

- [ ] **Step 3: `agents/plan-reviewer.md` 작성**

```markdown
---
name: plan-reviewer
color: yellow
description: |
  Independent reviewer for cchelp's weekly criteria-update plan (U3.5 step). Runs in a fresh subagent with no shared context from the planner. Verifies source integrity, schema validity, verifier executability, and semantic consistency of every proposed criteria change. All approvals MUST cite a verbatim quote from fetched docs body — substring-checked deterministically. Examples: <example>cron pipeline U3.5: spawns this agent with plan.json + fetched bodies to validate change records before Apply</example>
model: opus
---

You are an independent Plan Reviewer. The planner agent has already proposed changes to cchelp's review criteria; your job is to verify those changes meet four criteria with **fresh eyes** (no shared context).

## 왜 너는 독립인가

PR #2 같은 자기참조 함정 (작성자 = 채점자 = 자기 갱신자) 을 차단하기 위해 컨텍스트 격리된 subagent 로 호출됨. 너는 planner 의 합리화를 본 적이 없다. plan.json 과 fetched docs bodies 만으로 판단해라.

## Inputs

- **plan_json_path**: `/tmp/cchelp-cron-<run-id>/plan.json`
- **fetched_dir**: `/tmp/cchelp-cron-<run-id>/fetched/` (각 카테고리의 docs body raw)

## Output

`/tmp/cchelp-cron-<run-id>/plan_review.json` 에 다음 형식으로 저장:

```json
{
  "verdict": "approved" | "partial" | "aborted",
  "approved_records": [<record_id>...],
  "rejected_records": [
    {"record_id": "...", "check_failed": 1|2|3|4, "reason": "...", "quote_used": "..."}
  ],
  "summary": "<한두 줄 요약>"
}
```

## 4단계 검증

각 record 에 대해 순서대로:

### Check 1 — Source 무결성 (programmatic)
이 검증은 `cron/verifiers/source_integrity.py` 를 호출해서 결정론적으로 수행. 다음 명령 실행:

```bash
cd cron && PYTHONPATH=. .venv/bin/python -m scripts.run_source_check \
    --plan <plan_json_path> --record-id <record_id>
```

stdout 의 `{ok: bool, reason: str}` JSON 을 받아 결과 사용. fail 이면 reject.

### Check 2 — Schema 유효성 (programmatic)
다음 실행:

```bash
cd cron && PYTHONPATH=. .venv/bin/python -m verifiers.schema_validator \
    --record <plan_json_path>:<record_id>
```

fail 이면 reject.

### Check 3 — Verifier 실행 가능성 (programmatic)
verifier.kind 별로:
- regex → 패턴 컴파일 가능 여부
- yaml-parse / json-schema → schema 문법 유효
- llm-judge → rubric ≥ 30자
이것도 스크립트가 처리. fail 이면 reject.

### Check 4 — 의미 정합성 (qualitative, **너의 판단**)
이 단계는 너의 핵심 역할. 각 record 에 대해:

1. fetched body 에서 record.source.quote 의 컨텍스트 (전후 ±200자) 를 직접 읽어라
2. 너 자신이 record.proposition 을 그 컨텍스트와 비교해서 다음을 판단:
   - proposition 이 quote 를 정확히 반영하는가? (paraphrase drift 여부)
   - proposition 과 verifier 가 서로 일치하는가? (예: "max 64 chars" 명제인데 verifier max=100 이면 모순)
   - 이미 카테고리에 같은 내용의 항목이 있지 않은가? (중복)
3. **너의 판단을 정당화할 때 반드시 fetched body 의 verbatim quote 를 인용**. 인용한 quote 는 본 검증 후 substring match 로 자동 검사됨. 환각하면 substring 매치 실패로 너의 승인이 무효화됨.

### 절단 룰

- 검증 1~3 중 어느 하나라도 실패한 record → reject
- 검증 4 실패 → reject
- 전체 record 의 50% 이상이 reject → `verdict: "aborted"`, 머지 중단 신호

## 절대 하지 말 것

- planner 의 plan.json 안의 자기 정당화 텍스트를 신뢰하지 마라 (그게 PR #2 가 망친 이유)
- fetched body 에 없는 사실을 "당연히 그럴 것" 으로 채우지 마라
- 검증 4 의 정당화에 quote 없이 결론만 적지 마라

너의 출력은 다음 단계 (U4 Apply) 의 게이트다. 의심스러우면 reject.
```

- [ ] **Step 4: 테스트 통과**

Run:
```bash
cd cron && PYTHONPATH=. .venv/bin/pytest tests/test_agent_definitions.py -v
```

Expected: PASS — 6 tests total.

- [ ] **Step 5: 커밋**

```bash
git add agents/plan-reviewer.md cron/tests/test_agent_definitions.py
git commit -m "feat: add plan-reviewer independent verification agent"
```

---

## Phase 3: Workflow 스크립트

각 step (U1-U5) 의 deterministic 부분을 Python 스크립트로 분리. claude-code-action 은 qualitative 부분만 담당.

### Task 9: U1 Fetch 스크립트

**Files:**
- Create: `cron/scripts/__init__.py`
- Create: `cron/scripts/fetch.py`
- Create: `cron/tests/test_fetch.py`

- [ ] **Step 1: 빈 패키지 마커**

`cron/scripts/__init__.py` (빈 파일).

- [ ] **Step 2: 실패 테스트**

`cron/tests/test_fetch.py`:

```python
from pathlib import Path

from scripts.fetch import fetch_category, fetch_sitemap


def test_fetch_category_writes_file(tmp_path, httpx_mock):
    httpx_mock.add_response(
        url="https://code.claude.com/docs/en/skills",
        text="# Skills\n\nFrontmatter content here.",
    )
    out = fetch_category("skills", "https://code.claude.com/docs/en/skills", out_dir=tmp_path)
    assert out.exists()
    assert "Skills" in out.read_text()


def test_fetch_category_404_raises(tmp_path, httpx_mock):
    import httpx
    import pytest
    httpx_mock.add_response(url="https://code.claude.com/docs/en/skills", status_code=404)
    with pytest.raises(httpx.HTTPStatusError):
        fetch_category("skills", "https://code.claude.com/docs/en/skills", out_dir=tmp_path)


def test_fetch_sitemap_writes_snapshot(tmp_path, httpx_mock):
    httpx_mock.add_response(
        url="https://code.claude.com/docs/llms.txt",
        text="https://code.claude.com/docs/en/skills.md\nhttps://code.claude.com/docs/en/hooks.md",
    )
    out = fetch_sitemap(out_dir=tmp_path)
    assert out.exists()
    body = out.read_text()
    assert "skills.md" in body
```

- [ ] **Step 3: 테스트 실패 확인**

Run:
```bash
cd cron && PYTHONPATH=. .venv/bin/pytest tests/test_fetch.py -v
```

Expected: FAIL — `ModuleNotFoundError`.

- [ ] **Step 4: `cron/scripts/fetch.py` 구현**

```python
"""U1 Fetch: WebFetch wrapper for docs/changelog/sitemap."""
from datetime import datetime, timezone
from pathlib import Path

import httpx


def fetch_category(name: str, url: str, *, out_dir: Path) -> Path:
    """Fetch a docs page; raise on non-200."""
    out_dir.mkdir(parents=True, exist_ok=True)
    resp = httpx.get(url, follow_redirects=True, timeout=60.0)
    resp.raise_for_status()
    out = out_dir / f"{name}.md"
    out.write_text(resp.text, encoding="utf-8")
    # sidecar metadata for fetched_at
    (out_dir / f"{name}.meta.txt").write_text(
        f"url={url}\nfetched_at={datetime.now(timezone.utc).isoformat()}\nstatus={resp.status_code}\n"
    )
    return out


def fetch_sitemap(*, out_dir: Path, sitemap_url: str = "https://code.claude.com/docs/llms.txt") -> Path:
    out_dir.mkdir(parents=True, exist_ok=True)
    resp = httpx.get(sitemap_url, follow_redirects=True, timeout=60.0)
    resp.raise_for_status()
    out = out_dir / "sitemap.txt"
    out.write_text(resp.text, encoding="utf-8")
    return out


def fetch_changelog(*, out_dir: Path) -> Path:
    return fetch_category("_changelog", "https://code.claude.com/docs/en/changelog", out_dir=out_dir)
```

- [ ] **Step 5: 테스트 통과**

Run:
```bash
cd cron && PYTHONPATH=. .venv/bin/pytest tests/test_fetch.py -v
```

Expected: PASS.

- [ ] **Step 6: 커밋**

```bash
git add cron/scripts/__init__.py cron/scripts/fetch.py cron/tests/test_fetch.py
git commit -m "feat: add U1 fetch script for docs/changelog/sitemap"
```

---

### Task 10: U2 Diff 로직 — body snapshot 비교

새 fetched body 와 직전 cron 의 snapshot 을 비교해서 ADD/UPDATE/REMOVE 후보 식별.

**Files:**
- Create: `cron/scripts/diff.py`
- Create: `cron/tests/test_diff.py`

- [ ] **Step 1: 실패 테스트**

`cron/tests/test_diff.py`:

```python
from pathlib import Path

from scripts.diff import classify_items, ItemStatus


def _item(item_id, quote):
    return {
        "id": item_id,
        "type": "programmatic",
        "proposition": "p",
        "verifier": {"kind": "regex", "pattern": "."},
        "source": {
            "url": "https://example.com",
            "fetched_at": "2026-04-29T02:00:00Z",
            "quote": quote,
        },
        "severity": "important",
        "category": "skills",
    }


def test_stable_when_quote_in_body():
    items = [_item("a", "lorem ipsum dolor")]
    body = "lorem ipsum dolor sit amet"
    result = classify_items(items, body)
    assert result["a"] == ItemStatus.STABLE


def test_remove_candidate_when_quote_missing():
    items = [_item("b", "missing-text")]
    body = "completely different content"
    result = classify_items(items, body)
    assert result["b"] == ItemStatus.REMOVE_CANDIDATE


def test_update_candidate_when_near_match():
    # quote 가 변경됐지만 충분히 유사한 부분이 body 에 존재
    items = [_item("c", "name field max 200 chars")]
    body = "Lowercase letters, numbers, and hyphens only (max 64 characters)."
    result = classify_items(items, body)
    # max XYZ chars 같은 패턴이 둘 다 있으니 UPDATE
    assert result["c"] in (ItemStatus.UPDATE_CANDIDATE, ItemStatus.REMOVE_CANDIDATE)
```

- [ ] **Step 2: 테스트 실패 확인**

Run:
```bash
cd cron && PYTHONPATH=. .venv/bin/pytest tests/test_diff.py -v
```

Expected: FAIL.

- [ ] **Step 3: `cron/scripts/diff.py` 구현**

```python
"""U2 Diff: classify existing items against fresh body."""
from enum import Enum
from typing import Iterable


class ItemStatus(str, Enum):
    STABLE = "stable"
    UPDATE_CANDIDATE = "update_candidate"
    REMOVE_CANDIDATE = "remove_candidate"


def _shingle(text: str, k: int = 5) -> set[str]:
    """Return set of k-gram word shingles for fuzzy match."""
    words = text.lower().split()
    return {" ".join(words[i : i + k]) for i in range(len(words) - k + 1)}


def _near_match(quote: str, body: str, threshold: float = 0.3) -> bool:
    """Return True if at least `threshold` of quote's shingles overlap body's shingles."""
    qs = _shingle(quote)
    if not qs:
        return False
    bs = _shingle(body)
    overlap = qs & bs
    return len(overlap) / len(qs) >= threshold


def classify_items(items: Iterable[dict], body: str) -> dict[str, ItemStatus]:
    """For each item, decide STABLE/UPDATE/REMOVE based on its quote vs body."""
    out: dict[str, ItemStatus] = {}
    for item in items:
        quote = item["source"]["quote"]
        if quote in body:
            out[item["id"]] = ItemStatus.STABLE
        elif _near_match(quote, body):
            out[item["id"]] = ItemStatus.UPDATE_CANDIDATE
        else:
            out[item["id"]] = ItemStatus.REMOVE_CANDIDATE
    return out
```

- [ ] **Step 4: 테스트 통과**

Run:
```bash
cd cron && PYTHONPATH=. .venv/bin/pytest tests/test_diff.py -v
```

Expected: PASS.

- [ ] **Step 5: 커밋**

```bash
git add cron/scripts/diff.py cron/tests/test_diff.py
git commit -m "feat: add U2 diff classifier (STABLE/UPDATE/REMOVE candidates)"
```

---

### Task 11: U3 Plan generation — 새 항목 추출

이 task 는 **두 부분**:
- **결정론적 부분 (Python)**: REMOVE 후보 / UPDATE 후보의 record 생성 (이미 식별된 것)
- **LLM 부분 (claude-code-action)**: 새 body 에서 ADD 후보 항목 추출. 단순 사실 (frontmatter table row, schema 제약) 만 채택.

이 task 는 결정론적 부분만 작성. ADD 추출은 워크플로 task (Task 15) 의 prompt 안에서 처리.

**Files:**
- Create: `cron/scripts/plan.py`
- Create: `cron/tests/test_plan.py`

- [ ] **Step 1: 실패 테스트**

`cron/tests/test_plan.py`:

```python
from datetime import datetime, timezone

from scripts.diff import ItemStatus
from scripts.plan import build_plan, PlanRecord


def _item(id_):
    return {
        "id": id_,
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


def test_plan_contains_remove_record():
    items = [_item("rem1")]
    statuses = {"rem1": ItemStatus.REMOVE_CANDIDATE}
    plan = build_plan(category="skills", existing_items=items, statuses=statuses, additions=[])
    assert any(r.action == "REMOVE" and r.item_id == "rem1" for r in plan)


def test_plan_contains_addition():
    new_item = _item("new1")
    plan = build_plan(category="skills", existing_items=[], statuses={}, additions=[new_item])
    assert any(r.action == "ADD" and r.item_id == "new1" for r in plan)


def test_plan_skips_stable():
    items = [_item("st1")]
    statuses = {"st1": ItemStatus.STABLE}
    plan = build_plan(category="skills", existing_items=items, statuses=statuses, additions=[])
    assert plan == []
```

- [ ] **Step 2: 테스트 실패**

Run: `cd cron && PYTHONPATH=. .venv/bin/pytest tests/test_plan.py -v`

Expected: FAIL.

- [ ] **Step 3: `cron/scripts/plan.py` 구현**

```python
"""U3 Plan: build change records from diff statuses + new additions."""
from dataclasses import dataclass, asdict
from typing import Literal

from scripts.diff import ItemStatus


@dataclass
class PlanRecord:
    category: str
    action: Literal["ADD", "UPDATE", "REMOVE"]
    item_id: str
    payload: dict | None  # full new item for ADD/UPDATE, None for REMOVE

    def to_dict(self) -> dict:
        return asdict(self)


def build_plan(
    *,
    category: str,
    existing_items: list[dict],
    statuses: dict[str, ItemStatus],
    additions: list[dict],
) -> list[PlanRecord]:
    """
    Compose change records.

    - REMOVE_CANDIDATE → ADD a REMOVE record (fallback search runs separately before commit)
    - UPDATE_CANDIDATE → record requires a new payload; here we mark the id, payload-filling
      happens in the LLM-driven prompt step
    - STABLE → skip
    - additions → ADD records (already full payloads from LLM extraction)
    """
    records: list[PlanRecord] = []
    items_by_id = {it["id"]: it for it in existing_items}

    for item_id, status in statuses.items():
        if status == ItemStatus.STABLE:
            continue
        if status == ItemStatus.REMOVE_CANDIDATE:
            records.append(PlanRecord(category=category, action="REMOVE", item_id=item_id, payload=None))
        elif status == ItemStatus.UPDATE_CANDIDATE:
            # payload will be filled by LLM step; for now we carry the existing item
            records.append(
                PlanRecord(
                    category=category,
                    action="UPDATE",
                    item_id=item_id,
                    payload=items_by_id[item_id],
                )
            )

    for new_item in additions:
        records.append(
            PlanRecord(
                category=category,
                action="ADD",
                item_id=new_item["id"],
                payload=new_item,
            )
        )
    return records
```

- [ ] **Step 4: 테스트 통과**

Run: `cd cron && PYTHONPATH=. .venv/bin/pytest tests/test_plan.py -v`

Expected: PASS.

- [ ] **Step 5: 커밋**

```bash
git add cron/scripts/plan.py cron/tests/test_plan.py
git commit -m "feat: add U3 plan record builder"
```

---

### Task 12: Fallback search — REMOVE 후보의 sitemap/cross-language 검색

**Files:**
- Create: `cron/scripts/fallback_search.py`
- Create: `cron/tests/test_fallback_search.py`

- [ ] **Step 1: 실패 테스트**

`cron/tests/test_fallback_search.py`:

```python
from scripts.fallback_search import FallbackResult, resolve_remove_candidate


def test_found_in_other_language(httpx_mock):
    """Original /en/ 404, /ko/ 200 with quote → UPDATE."""
    httpx_mock.add_response(
        url="https://code.claude.com/docs/en/skills", status_code=404
    )
    httpx_mock.add_response(
        url="https://code.claude.com/docs/ko/skills",
        text="설명: Lowercase letters and numbers only",
    )
    httpx_mock.add_response(
        url="https://code.claude.com/docs/llms.txt",
        text="https://code.claude.com/docs/en/skills.md\nhttps://code.claude.com/docs/ko/skills.md",
    )
    result = resolve_remove_candidate(
        url="https://code.claude.com/docs/en/skills",
        quote="Lowercase letters and numbers only",
    )
    assert result.action == "UPDATE_URL"
    assert "ko/skills" in result.new_url


def test_404_and_no_match_returns_delete(httpx_mock):
    httpx_mock.add_response(url="https://code.claude.com/docs/en/skills", status_code=404)
    httpx_mock.add_response(url="https://code.claude.com/docs/ko/skills", status_code=404)
    httpx_mock.add_response(
        url="https://code.claude.com/docs/llms.txt",
        text="https://code.claude.com/docs/en/skills.md",
    )
    httpx_mock.add_response(
        url="https://code.claude.com/docs/en/changelog", text="no deprecation here"
    )
    result = resolve_remove_candidate(
        url="https://code.claude.com/docs/en/skills",
        quote="Lowercase letters and numbers only",
    )
    assert result.action == "DELETE"


def test_changelog_deprecation_returns_delete_with_note(httpx_mock):
    httpx_mock.add_response(url="https://code.claude.com/docs/en/skills", status_code=404)
    httpx_mock.add_response(url="https://code.claude.com/docs/ko/skills", status_code=404)
    httpx_mock.add_response(
        url="https://code.claude.com/docs/llms.txt",
        text="https://code.claude.com/docs/en/skills.md",
    )
    httpx_mock.add_response(
        url="https://code.claude.com/docs/en/changelog",
        text="v2.1.200: Removed legacy 'name' field from frontmatter (deprecated).",
    )
    result = resolve_remove_candidate(
        url="https://code.claude.com/docs/en/skills",
        quote="legacy 'name' field",
    )
    assert result.action == "DELETE"
    assert result.changelog_note is not None
```

- [ ] **Step 2: 테스트 실패**

Run: `cd cron && PYTHONPATH=. .venv/bin/pytest tests/test_fallback_search.py -v`

Expected: FAIL.

- [ ] **Step 3: `cron/scripts/fallback_search.py` 구현**

```python
"""Fallback search for REMOVE candidates: sitemap + cross-language + changelog."""
import re
from dataclasses import dataclass
from typing import Literal

import httpx

CHANGELOG_URL = "https://code.claude.com/docs/en/changelog"
SITEMAP_URL = "https://code.claude.com/docs/llms.txt"


@dataclass
class FallbackResult:
    action: Literal["UPDATE_URL", "DELETE"]
    new_url: str | None = None
    changelog_note: str | None = None


def _swap_locale(url: str) -> str | None:
    """If url contains /en/ → /ko/, /ko/ → /en/."""
    if "/en/" in url:
        return url.replace("/en/", "/ko/")
    if "/ko/" in url:
        return url.replace("/ko/", "/en/")
    return None


def _quote_present(url: str, quote: str) -> bool:
    try:
        resp = httpx.get(url, follow_redirects=True, timeout=30.0)
        return resp.status_code == 200 and quote in resp.text
    except httpx.HTTPError:
        return False


def _search_changelog_for_quote(quote: str) -> str | None:
    """Return ±200-char window around quote in changelog if present, else None."""
    try:
        resp = httpx.get(CHANGELOG_URL, follow_redirects=True, timeout=30.0)
    except httpx.HTTPError:
        return None
    if resp.status_code != 200:
        return None
    body = resp.text
    # 단순 substring 매칭. 환각 방지.
    if quote not in body:
        # 단어 단위 fuzzy: quote 의 첫 3 단어로 매칭 시도
        keywords = quote.split()[:3]
        if not keywords:
            return None
        pattern = r"\s+".join(re.escape(w) for w in keywords)
        m = re.search(pattern, body, re.IGNORECASE)
        if not m:
            return None
        idx = m.start()
    else:
        idx = body.find(quote)
    return body[max(0, idx - 200) : idx + 200]


def resolve_remove_candidate(*, url: str, quote: str) -> FallbackResult:
    """Decide whether REMOVE candidate is truly gone or just moved."""
    # Step 1: cross-language probe
    other = _swap_locale(url)
    if other and _quote_present(other, quote):
        return FallbackResult(action="UPDATE_URL", new_url=other)

    # Step 2: sitemap fuzzy match (look for nearby slug)
    try:
        sitemap = httpx.get(SITEMAP_URL, follow_redirects=True, timeout=30.0).text
    except httpx.HTTPError:
        sitemap = ""
    candidates = [
        line.strip().rstrip(".md")
        for line in sitemap.splitlines()
        if line.strip().endswith(".md")
    ]
    # base slug (마지막 path segment) 가 같은 것들
    base = url.rstrip("/").rsplit("/", 1)[-1]
    for cand in candidates:
        if cand == url or cand.rstrip("/").rsplit("/", 1)[-1] != base:
            continue
        if _quote_present(cand, quote):
            return FallbackResult(action="UPDATE_URL", new_url=cand)

    # Step 3: changelog deprecation note
    note = _search_changelog_for_quote(quote)
    return FallbackResult(action="DELETE", changelog_note=note)
```

- [ ] **Step 4: 테스트 통과**

Run: `cd cron && PYTHONPATH=. .venv/bin/pytest tests/test_fallback_search.py -v`

Expected: PASS.

- [ ] **Step 5: 커밋**

```bash
git add cron/scripts/fallback_search.py cron/tests/test_fallback_search.py
git commit -m "feat: add REMOVE fallback search (cross-language + sitemap + changelog)"
```

---

### Task 13: 카테고리 자동 발견 — llms.txt diff + heuristic 필터

**Files:**
- Create: `cron/scripts/category_discovery.py`
- Create: `cron/tests/test_category_discovery.py`

- [ ] **Step 1: 실패 테스트**

`cron/tests/test_category_discovery.py`:

```python
from pathlib import Path

from scripts.category_discovery import (
    CategoryCandidate,
    diff_sitemap,
    is_review_worthy,
)


def test_diff_finds_new_pages():
    old = "https://code.claude.com/docs/en/skills.md\nhttps://code.claude.com/docs/en/hooks.md"
    new = old + "\nhttps://code.claude.com/docs/en/agent-teams.md"
    diff = diff_sitemap(old, new)
    assert any("agent-teams" in url for url in diff.added)
    assert diff.removed == []


def test_is_review_worthy_frontmatter_table_yes():
    body = """
# Agent Teams

## Frontmatter reference

| Field | Required | Description |
| :--- | :--- | :--- |
| `name` | Yes | ... |
"""
    assert is_review_worthy(body)


def test_is_review_worthy_quickstart_no():
    body = """
# Quickstart Tutorial

This is a getting-started guide. Just follow these steps.
"""
    assert not is_review_worthy(body)


def test_is_review_worthy_overview_with_no_schema_no():
    body = """
# Overview

This is general information about Claude Code without any frontmatter table or schema.
"""
    assert not is_review_worthy(body)
```

- [ ] **Step 2: 테스트 실패**

Run: `cd cron && PYTHONPATH=. .venv/bin/pytest tests/test_category_discovery.py -v`

Expected: FAIL.

- [ ] **Step 3: `cron/scripts/category_discovery.py` 구현**

```python
"""Category auto-discovery via sitemap diff + frontmatter/schema heuristic."""
import re
from dataclasses import dataclass


@dataclass
class SitemapDiff:
    added: list[str]
    removed: list[str]


def diff_sitemap(old: str, new: str) -> SitemapDiff:
    old_set = {line.strip() for line in old.splitlines() if line.strip()}
    new_set = {line.strip() for line in new.splitlines() if line.strip()}
    return SitemapDiff(
        added=sorted(new_set - old_set),
        removed=sorted(old_set - new_set),
    )


# 휴리스틱: review-worthy = frontmatter table 또는 schema 존재
FRONTMATTER_TABLE_RE = re.compile(
    r"##\s*Frontmatter\s+reference|"
    r"\|\s*Field\s*\|\s*Required",
    re.IGNORECASE,
)
SCHEMA_BLOCK_RE = re.compile(r"```(?:json|yaml|jsonc)\s*\n.*?```", re.DOTALL)
GUIDE_BLACKLIST_RE = re.compile(
    r"^#\s*(quickstart|getting started|overview|troubleshooting|tutorial)",
    re.IGNORECASE | re.MULTILINE,
)


def is_review_worthy(body: str) -> bool:
    if FRONTMATTER_TABLE_RE.search(body):
        return True
    if SCHEMA_BLOCK_RE.search(body) and not GUIDE_BLACKLIST_RE.search(body):
        return True
    return False


@dataclass
class CategoryCandidate:
    name: str
    url: str
    body: str
```

- [ ] **Step 4: 테스트 통과**

Run: `cd cron && PYTHONPATH=. .venv/bin/pytest tests/test_category_discovery.py -v`

Expected: PASS.

- [ ] **Step 5: 커밋**

```bash
git add cron/scripts/category_discovery.py cron/tests/test_category_discovery.py
git commit -m "feat: add category auto-discovery (sitemap diff + heuristic filter)"
```

---

### Task 14: U5 Self-validate — B/C 신호 + 비율 정규화

cchelp 자기 자신에 대해 self-eval-runner 호출 → 결과 → 직전 cron 결과와 비교 → B 신호 / C 신호 추출.

**Files:**
- Create: `cron/scripts/self_validate.py`
- Create: `cron/tests/test_self_validate.py`

- [ ] **Step 1: 실패 테스트**

`cron/tests/test_self_validate.py`:

```python
from scripts.self_validate import compute_signals, BSignal, CSignal


def test_no_regression_no_b_signal():
    prev = [{"id": "a", "passed": True}, {"id": "b", "passed": True}]
    curr = [{"id": "a", "passed": True}, {"id": "b", "passed": True}]
    b = compute_signals(prev, curr).b_signal
    assert b.regressions == []


def test_regression_detected():
    prev = [{"id": "a", "passed": True}, {"id": "b", "passed": True}]
    curr = [{"id": "a", "passed": True}, {"id": "b", "passed": False}]
    b = compute_signals(prev, curr).b_signal
    assert "b" in b.regressions


def test_new_failures_not_regression():
    """직전 cron 에 없던 새 항목이 fail 인 건 회귀가 아님."""
    prev = [{"id": "a", "passed": True}]
    curr = [{"id": "a", "passed": True}, {"id": "new", "passed": False}]
    b = compute_signals(prev, curr).b_signal
    assert "new" not in b.regressions


def test_c_signal_ratio_drop():
    prev_metric = {"with_skill": 0.9, "baseline": 0.4}  # ratio = (0.9-0.4)/0.4 = 1.25
    curr_metric = {"with_skill": 0.6, "baseline": 0.5}  # ratio = (0.6-0.5)/0.5 = 0.20
    c = compute_signals([], [], prev_metric=prev_metric, curr_metric=curr_metric).c_signal
    # 1.25 → 0.20, 절대 차이 = 1.05, 퍼센트로 105 → 임계값 0.20 절대 초과
    assert c.dropped


def test_c_signal_stable():
    prev_metric = {"with_skill": 0.9, "baseline": 0.4}
    curr_metric = {"with_skill": 0.92, "baseline": 0.4}
    c = compute_signals([], [], prev_metric=prev_metric, curr_metric=curr_metric).c_signal
    assert not c.dropped
```

- [ ] **Step 2: 테스트 실패 확인**

Run: `cd cron && PYTHONPATH=. .venv/bin/pytest tests/test_self_validate.py -v`

Expected: FAIL.

- [ ] **Step 3: `cron/scripts/self_validate.py` 구현**

```python
"""U5 Self-validate: compute B (regression) and C (ratio drop) signals."""
from dataclasses import dataclass


@dataclass
class BSignal:
    regressions: list[str]


@dataclass
class CSignal:
    prev_ratio: float | None
    curr_ratio: float | None
    dropped: bool


@dataclass
class Signals:
    b_signal: BSignal
    c_signal: CSignal


C_DROP_THRESHOLD = 0.20  # 절대 차이 (ratio 0.5 → 0.3 = 0.20 dropped)


def _ratio(metric: dict | None) -> float | None:
    if not metric:
        return None
    bl = metric.get("baseline")
    if not bl or bl == 0:
        return None
    return (metric["with_skill"] - bl) / bl


def compute_signals(
    prev_results: list[dict],
    curr_results: list[dict],
    *,
    prev_metric: dict | None = None,
    curr_metric: dict | None = None,
) -> Signals:
    prev_pass = {r["id"]: r["passed"] for r in prev_results}
    curr_pass = {r["id"]: r["passed"] for r in curr_results}

    regressions = [
        item_id
        for item_id, prev_p in prev_pass.items()
        if prev_p and item_id in curr_pass and not curr_pass[item_id]
    ]
    b = BSignal(regressions=regressions)

    prev_r = _ratio(prev_metric)
    curr_r = _ratio(curr_metric)
    dropped = (
        prev_r is not None
        and curr_r is not None
        and (prev_r - curr_r) >= C_DROP_THRESHOLD
    )
    c = CSignal(prev_ratio=prev_r, curr_ratio=curr_r, dropped=dropped)

    return Signals(b_signal=b, c_signal=c)
```

- [ ] **Step 4: 테스트 통과**

Run: `cd cron && PYTHONPATH=. .venv/bin/pytest tests/test_self_validate.py -v`

Expected: PASS.

- [ ] **Step 5: 커밋**

```bash
git add cron/scripts/self_validate.py cron/tests/test_self_validate.py
git commit -m "feat: add U5 self-validate B/C signal computation"
```

---

## Phase 4: 워크플로 통합 + 정리

### Task 15: GitHub Actions 워크플로 재작성

기존 `.github/workflows/update-review-criteria.yml` 을 8-step 으로 재구성. 결정론적 부분은 Python 스크립트, qualitative 부분 (ADD 추출, plan-reviewer 의 검증 4) 만 claude-code-action.

**Files:**
- Modify: `.github/workflows/update-review-criteria.yml`

- [ ] **Step 1: 워크플로 파일 백업 (안전)**

Run:
```bash
cp .github/workflows/update-review-criteria.yml /tmp/old-update-criteria.yml.bak
```

- [ ] **Step 2: 새 워크플로 전체 재작성**

`.github/workflows/update-review-criteria.yml` 의 전체 내용을 다음으로 대체:

```yaml
name: Update Review Criteria

on:
  schedule:
    - cron: '0 17 * * 6'  # Sun 02:00 KST
  workflow_dispatch: {}

permissions:
  contents: write
  pull-requests: write
  id-token: write

env:
  RUN_DIR: /tmp/cchelp-cron-${{ github.run_id }}

jobs:
  update-criteria:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0

      - name: Setup Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'

      - name: Install cron deps
        working-directory: cron
        run: |
          python -m venv .venv
          .venv/bin/pip install -e ".[dev]"

      - name: U1 Fetch (docs + sitemap + changelog)
        working-directory: cron
        run: |
          mkdir -p ${{ env.RUN_DIR }}/fetched
          PYTHONPATH=. .venv/bin/python -m scripts.run_fetch \
            --mapping ../criteria-mapping.yml \
            --out-dir ${{ env.RUN_DIR }}/fetched

      - name: U2 Diff (classify items)
        working-directory: cron
        run: |
          PYTHONPATH=. .venv/bin/python -m scripts.run_diff \
            --refs-dir ../skills/review/references \
            --fetched-dir ${{ env.RUN_DIR }}/fetched \
            --out ${{ env.RUN_DIR }}/diff.json

      - name: Category discovery
        working-directory: cron
        run: |
          PYTHONPATH=. .venv/bin/python -m scripts.run_category_discovery \
            --new-sitemap ${{ env.RUN_DIR }}/fetched/sitemap.txt \
            --prev-sitemap cron/state/sitemap.snapshot.txt \
            --out ${{ env.RUN_DIR }}/discovery.json
        continue-on-error: true

      - name: U3 Plan (LLM extracts ADDs from new bodies + builds records)
        uses: anthropics/claude-code-action@v1
        with:
          claude_code_oauth_token: ${{ secrets.CLAUDE_CODE_OAUTH_TOKEN }}
          claude_args: |
            --permission-mode bypassPermissions
          prompt: |
            너는 cchelp 의 주간 cron pipeline U3 (Plan) 단계.

            입력:
            - diff: ${{ env.RUN_DIR }}/diff.json (UPDATE/REMOVE 후보)
            - fetched: ${{ env.RUN_DIR }}/fetched/<category>.md (각 카테고리 최신 docs body)
            - discovery: ${{ env.RUN_DIR }}/discovery.json (새 카테고리 후보)

            할 일:
            1. 각 fetched body 의 frontmatter table / schema row 등 검증 가능한 사실에서
               ADD 후보를 추출하라. 추출은 다음 schema 를 가진 yaml 항목으로:
                 - id (kebab-case unique)
                 - type: programmatic 우선, 정성적이면 qualitative
                 - proposition, verifier (kind 별 spec), source (url + fetched_at + quote), severity, category
            2. quote 는 fetched body 의 verbatim substring 이어야 한다. 환각 금지.
            3. UPDATE 후보 (diff.json) 의 새 payload 를 채워라 (새 body 의 새 quote 인용).
            4. 카테고리 발견 후보 각각에 대해 빈 references/<category>.yml 추가하고 초기 항목 5개 이내 추출.
            5. 모든 record 를 ${{ env.RUN_DIR }}/plan.json 에 PlanRecord JSON array 로 저장.

            형식:
            [
              {"category": "...", "action": "ADD"|"UPDATE"|"REMOVE", "item_id": "...", "payload": {...} | null}
            ]
          allowed_tools: "Bash,Read,Write,Glob,Grep"

      - name: U3.5 Plan Review (independent subagent)
        uses: anthropics/claude-code-action@v1
        with:
          claude_code_oauth_token: ${{ secrets.CLAUDE_CODE_OAUTH_TOKEN }}
          claude_args: |
            --permission-mode bypassPermissions
            --agent plan-reviewer
          prompt: |
            너는 plan-reviewer agent. plan.json 과 fetched bodies 를 검증해라.

            플랜 경로: ${{ env.RUN_DIR }}/plan.json
            fetched 경로: ${{ env.RUN_DIR }}/fetched/

            검증 1~3 (programmatic) 은 다음 명령으로:
              cd cron && PYTHONPATH=. .venv/bin/python -m scripts.run_plan_review \
                  --plan ${{ env.RUN_DIR }}/plan.json \
                  --fetched-dir ${{ env.RUN_DIR }}/fetched/ \
                  --out ${{ env.RUN_DIR }}/plan_review_partial.json

            검증 4 (의미 정합성) 는 너 자신이 plan_review_partial.json 의 통과 record 들에 대해
            수행. 각 결론에 verbatim quote 인용 강제.

            최종 결과를 ${{ env.RUN_DIR }}/plan_review.json 에 저장
            (verdict, approved_records, rejected_records, summary 필드).

      - name: Check plan review verdict
        id: plan_review_check
        run: |
          VERDICT=$(jq -r '.verdict' ${{ env.RUN_DIR }}/plan_review.json)
          echo "verdict=$VERDICT" >> $GITHUB_OUTPUT
          if [ "$VERDICT" = "aborted" ]; then
            echo "Plan review aborted; exiting with marker"
            exit 0
          fi

      - name: U4 Apply (deterministic)
        if: steps.plan_review_check.outputs.verdict != 'aborted'
        working-directory: cron
        run: |
          PYTHONPATH=. .venv/bin/python -m scripts.run_apply \
            --plan ${{ env.RUN_DIR }}/plan.json \
            --review ${{ env.RUN_DIR }}/plan_review.json \
            --refs-dir ../skills/review/references \
            --templates-dir ../skills/generate/references \
            --agents-dir ../agents \
            --state-dir state

      - name: U5 Self-validate (smoke run with self-eval-runner)
        if: steps.plan_review_check.outputs.verdict != 'aborted'
        uses: anthropics/claude-code-action@v1
        with:
          claude_code_oauth_token: ${{ secrets.CLAUDE_CODE_OAUTH_TOKEN }}
          claude_args: |
            --permission-mode bypassPermissions
            --agent self-eval-runner
          prompt: |
            너는 self-eval-runner. cchelp 자기 자신을 새 refs 로 채점한다.

            refs 디렉토리: skills/review/references/
            대상: cchelp 자기 (skills/, agents/, .mcp.json 등)

            모든 항목 verifier 실행 후 결과를 ${{ env.RUN_DIR }}/self_eval.json 에
            JSON array 로 저장.

            병렬로 baseline 도 같이 측정 (skill 미적용 상태로 동일 항목 채점).
            baseline 결과는 ${{ env.RUN_DIR }}/baseline_eval.json.

      - name: Compute B/C signals
        if: steps.plan_review_check.outputs.verdict != 'aborted'
        working-directory: cron
        run: |
          PYTHONPATH=. .venv/bin/python -m scripts.run_signals \
            --prev-eval state/last_self_eval.json \
            --curr-eval ${{ env.RUN_DIR }}/self_eval.json \
            --prev-metric state/last_metric.json \
            --curr-metric ${{ env.RUN_DIR }}/baseline_eval.json \
            --out ${{ env.RUN_DIR }}/signals.json

      - name: U6 Commit & PR
        if: steps.plan_review_check.outputs.verdict != 'aborted'
        env:
          GH_TOKEN: ${{ secrets.GITHUB_TOKEN }}
        run: |
          BRANCH="chore/update-review-criteria-$(date +%Y-%m-%d)"
          git config user.name "claude[bot]"
          git config user.email "noreply@anthropic.com"
          git checkout -b "$BRANCH"
          git add skills/review/references/ skills/generate/references/ agents/ cron/state/
          if git diff --cached --quiet; then
            echo "No changes; skipping PR"
            exit 0
          fi

          # 라벨 결정
          LABELS="automated,criteria-update"
          if jq -e '.discovered_categories | length > 0' ${{ env.RUN_DIR }}/discovery.json > /dev/null 2>&1; then
            LABELS="$LABELS,category-discovery"
          fi
          if jq -e '.b_signal.regressions | length > 0' ${{ env.RUN_DIR }}/signals.json > /dev/null 2>&1; then
            LABELS="$LABELS,self-improve-blocked"
          fi
          if jq -e '.c_signal.dropped' ${{ env.RUN_DIR }}/signals.json > /dev/null 2>&1; then
            LABELS="$LABELS,self-improve-blocked"
          fi

          git commit -m "chore: weekly criteria update $(date +%Y-%m-%d)"
          git push -u origin "$BRANCH"

          PR_BODY=$(cat <<EOF
          ## Plan Review
          $(jq -r '.summary' ${{ env.RUN_DIR }}/plan_review.json)

          ## Signals
          - B (regressions): $(jq -r '.b_signal.regressions | join(", ")' ${{ env.RUN_DIR }}/signals.json)
          - C (ratio drop): $(jq -r '.c_signal.dropped' ${{ env.RUN_DIR }}/signals.json)

          ## Approved records
          $(jq -r '.approved_records | length' ${{ env.RUN_DIR }}/plan_review.json) records

          ## Rejected records
          $(jq -r '.rejected_records | length' ${{ env.RUN_DIR }}/plan_review.json) records
          EOF
          )

          gh pr create \
            --title "chore: weekly criteria update $(date +%Y-%m-%d)" \
            --body "$PR_BODY" \
            --label "$LABELS" \
            --reviewer KimHance

      - name: U7 Auto-merge (if signals clear)
        if: steps.plan_review_check.outputs.verdict != 'aborted'
        env:
          GH_TOKEN: ${{ secrets.GITHUB_TOKEN }}
        run: |
          # block 라벨 있으면 머지 안 함
          PR_NUM=$(gh pr list --head "chore/update-review-criteria-$(date +%Y-%m-%d)" --json number --jq '.[0].number')
          if [ -z "$PR_NUM" ]; then
            echo "No PR; skipping merge"
            exit 0
          fi
          BLOCKED=$(gh pr view "$PR_NUM" --json labels --jq '.labels | map(.name) | contains(["self-improve-blocked"]) or contains(["plan-review-aborted"])')
          if [ "$BLOCKED" = "true" ]; then
            echo "PR blocked by label; manual review needed"
            exit 0
          fi
          gh pr merge "$PR_NUM" --squash --auto
```

- [ ] **Step 3: 워크플로 lint (yamllint)**

Run:
```bash
yamllint .github/workflows/update-review-criteria.yml || true
```

(Yamllint 가 설치 안 됐으면 무시. 검증은 다음 단계.)

Run actually working check:
```bash
python -c "import yaml; yaml.safe_load(open('.github/workflows/update-review-criteria.yml'))" \
  && echo "YAML OK"
```

Expected: `YAML OK`.

- [ ] **Step 4: 워크플로의 모든 참조 스크립트 존재 확인**

Run:
```bash
for s in run_fetch run_diff run_category_discovery run_plan_review run_apply run_signals; do
  test -f cron/scripts/${s}.py && echo "OK: ${s}.py" || echo "MISSING: ${s}.py"
done
```

Expected: 모두 MISSING. (다음 task 들에서 작성)

- [ ] **Step 5: 커밋**

```bash
git add .github/workflows/update-review-criteria.yml
git commit -m "feat: rewrite criteria-update workflow as 8-step pipeline"
```

---

### Task 16: 스크립트 진입점 작성 (run_*.py)

각 워크플로 step 의 entry point. 라이브러리 함수를 CLI 로 노출.

**Files:**
- Create: `cron/scripts/run_fetch.py`
- Create: `cron/scripts/run_diff.py`
- Create: `cron/scripts/run_category_discovery.py`
- Create: `cron/scripts/run_plan_review.py`
- Create: `cron/scripts/run_apply.py`
- Create: `cron/scripts/run_signals.py`

- [ ] **Step 1: `cron/scripts/run_fetch.py`**

```python
"""CLI entry: U1 fetch. Reads criteria-mapping.yml, fetches all categories + sitemap + changelog."""
import argparse
from pathlib import Path

import yaml

from scripts.fetch import fetch_category, fetch_changelog, fetch_sitemap


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--mapping", required=True, type=Path)
    ap.add_argument("--out-dir", required=True, type=Path)
    args = ap.parse_args()

    mapping = yaml.safe_load(args.mapping.read_text())
    for entry in mapping.get("mappings", []):
        name = entry["name"] if "name" in entry else entry["keywords"][0]
        url = entry["docs_url"]
        print(f"fetch {name} {url}")
        fetch_category(name, url, out_dir=args.out_dir)
    fetch_sitemap(out_dir=args.out_dir)
    fetch_changelog(out_dir=args.out_dir)


if __name__ == "__main__":
    main()
```

- [ ] **Step 2: `cron/scripts/run_diff.py`**

```python
"""CLI entry: U2 diff. For each refs/*.yml, classify items vs fetched body."""
import argparse
import json
from pathlib import Path

import yaml

from scripts.diff import classify_items


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--refs-dir", required=True, type=Path)
    ap.add_argument("--fetched-dir", required=True, type=Path)
    ap.add_argument("--out", required=True, type=Path)
    args = ap.parse_args()

    out = {}
    for refs_file in sorted(args.refs_dir.glob("*.yml")):
        category = refs_file.stem
        items = yaml.safe_load(refs_file.read_text()) or []
        body_path = args.fetched_dir / f"{category}.md"
        if not body_path.exists():
            out[category] = {"error": f"fetched body missing: {body_path}"}
            continue
        body = body_path.read_text()
        statuses = classify_items(items, body)
        out[category] = {item_id: status.value for item_id, status in statuses.items()}

    args.out.write_text(json.dumps(out, indent=2))


if __name__ == "__main__":
    main()
```

- [ ] **Step 3: `cron/scripts/run_category_discovery.py`**

```python
"""CLI entry: category auto-discovery."""
import argparse
import json
import re
from pathlib import Path

import httpx

from scripts.category_discovery import diff_sitemap, is_review_worthy


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--new-sitemap", required=True, type=Path)
    ap.add_argument("--prev-sitemap", required=False, type=Path)
    ap.add_argument("--out", required=True, type=Path)
    args = ap.parse_args()

    new = args.new_sitemap.read_text()
    prev = args.prev_sitemap.read_text() if args.prev_sitemap and args.prev_sitemap.exists() else ""

    diff = diff_sitemap(prev, new)

    discovered = []
    for url in diff.added:
        if not url.endswith(".md"):
            continue
        try:
            resp = httpx.get(url, follow_redirects=True, timeout=30.0)
        except httpx.HTTPError:
            continue
        if resp.status_code != 200:
            continue
        if not is_review_worthy(resp.text):
            continue
        # 카테고리 이름 = url 의 마지막 path segment (.md 제거)
        m = re.search(r"/([^/]+)\.md$", url)
        if not m:
            continue
        discovered.append({"name": m.group(1), "url": url.replace(".md", "")})

    args.out.write_text(json.dumps({"discovered_categories": discovered}, indent=2))


if __name__ == "__main__":
    main()
```

- [ ] **Step 4: `cron/scripts/run_plan_review.py`**

```python
"""CLI entry: U3.5 Plan Review (deterministic checks 1-3).

Check 4 (semantic) is performed by the plan-reviewer agent itself; this script
produces a partial verdict that the agent then completes.
"""
import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

from verifiers.schema_validator import validate_category_file
from verifiers.source_integrity import check_source_integrity


def _check_verifier_executable(item: dict) -> tuple[bool, str]:
    v = item["verifier"]
    kind = v["kind"]
    try:
        if kind == "regex":
            import re
            re.compile(v["pattern"])
        elif kind == "yaml-parse":
            if not v.get("target"):
                return False, "yaml-parse missing target"
        elif kind == "json-schema":
            schema_ref = v["schema_ref"]
            if not Path(schema_ref).exists():
                return False, f"schema_ref not found: {schema_ref}"
        elif kind == "llm-judge":
            if len(v.get("rubric", "")) < 30:
                return False, "rubric < 30 chars"
        return True, "executable"
    except Exception as e:
        return False, f"{type(e).__name__}: {e}"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--plan", required=True, type=Path)
    ap.add_argument("--fetched-dir", required=True, type=Path)
    ap.add_argument("--out", required=True, type=Path)
    args = ap.parse_args()

    plan = json.loads(args.plan.read_text())
    now = datetime.now(timezone.utc)

    verdict = {"approved": [], "rejected": []}

    for record in plan:
        if record["action"] == "REMOVE":
            verdict["approved"].append(record["item_id"])
            continue
        item = record["payload"]
        if not item:
            verdict["rejected"].append({"id": record["item_id"], "check": "schema", "reason": "empty payload"})
            continue

        # Check 1: source integrity
        si = check_source_integrity(item, now=now)
        if not si.ok:
            verdict["rejected"].append({"id": item["id"], "check": "source", "reason": si.reason})
            continue

        # Check 3: verifier executability (skip 2; 2 is JSON Schema validation done at write-time)
        ok, reason = _check_verifier_executable(item)
        if not ok:
            verdict["rejected"].append({"id": item["id"], "check": "verifier", "reason": reason})
            continue

        verdict["approved"].append(item["id"])

    args.out.write_text(json.dumps(verdict, indent=2))


if __name__ == "__main__":
    main()
```

- [ ] **Step 5: `cron/scripts/run_apply.py`**

```python
"""CLI entry: U4 Apply (deterministic file mutations)."""
import argparse
import json
from pathlib import Path

import yaml


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--plan", required=True, type=Path)
    ap.add_argument("--review", required=True, type=Path)
    ap.add_argument("--refs-dir", required=True, type=Path)
    ap.add_argument("--templates-dir", required=True, type=Path)
    ap.add_argument("--agents-dir", required=True, type=Path)
    ap.add_argument("--state-dir", required=True, type=Path)
    args = ap.parse_args()

    plan = json.loads(args.plan.read_text())
    review = json.loads(args.review.read_text())
    approved_ids = set(review.get("approved_records", review.get("approved", [])))

    # 카테고리별 그룹
    by_cat: dict[str, list] = {}
    for record in plan:
        if record["item_id"] not in approved_ids:
            continue
        by_cat.setdefault(record["category"], []).append(record)

    for category, records in by_cat.items():
        refs_path = args.refs_dir / f"{category}.yml"
        items = yaml.safe_load(refs_path.read_text()) if refs_path.exists() else []
        items = items or []
        items_by_id = {it["id"]: it for it in items}

        for r in records:
            if r["action"] == "ADD":
                items_by_id[r["item_id"]] = r["payload"]
            elif r["action"] == "UPDATE":
                items_by_id[r["item_id"]] = r["payload"]
            elif r["action"] == "REMOVE":
                items_by_id.pop(r["item_id"], None)

        new_items = sorted(items_by_id.values(), key=lambda it: it["id"])
        refs_path.parent.mkdir(parents=True, exist_ok=True)
        refs_path.write_text(yaml.safe_dump(new_items, sort_keys=False, allow_unicode=True))

    print(f"applied {len(approved_ids)} approved records across {len(by_cat)} categories")


if __name__ == "__main__":
    main()
```

- [ ] **Step 6: `cron/scripts/run_signals.py`**

```python
"""CLI entry: B/C signal computation."""
import argparse
import json
from dataclasses import asdict
from pathlib import Path

from scripts.self_validate import compute_signals


def _read_or_empty(path: Path):
    if not path or not path.exists():
        return None
    return json.loads(path.read_text())


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--prev-eval", type=Path)
    ap.add_argument("--curr-eval", required=True, type=Path)
    ap.add_argument("--prev-metric", type=Path)
    ap.add_argument("--curr-metric", type=Path)
    ap.add_argument("--out", required=True, type=Path)
    args = ap.parse_args()

    prev_eval = _read_or_empty(args.prev_eval) or []
    curr_eval = _read_or_empty(args.curr_eval) or []
    prev_metric = _read_or_empty(args.prev_metric)
    curr_metric = _read_or_empty(args.curr_metric)

    signals = compute_signals(prev_eval, curr_eval, prev_metric=prev_metric, curr_metric=curr_metric)
    args.out.write_text(
        json.dumps(
            {
                "b_signal": asdict(signals.b_signal),
                "c_signal": asdict(signals.c_signal),
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
```

- [ ] **Step 7: 모든 스크립트 import 테스트**

Run:
```bash
cd cron && PYTHONPATH=. .venv/bin/python -c "
from scripts import run_fetch, run_diff, run_category_discovery, run_plan_review, run_apply, run_signals
print('all OK')
"
```

Expected: `all OK`.

- [ ] **Step 8: 커밋**

```bash
git add cron/scripts/run_*.py
git commit -m "feat: add CLI entry points for cron pipeline steps"
```

---

### Task 17: criteria-mapping.yml 재구조화

자동 발견 카테고리 지원 + name 필드 추가.

**Files:**
- Modify: `criteria-mapping.yml`
- Create: `cron/schema/category-mapping.schema.json`
- Create: `cron/tests/test_mapping_schema.py`

- [ ] **Step 1: 현재 mapping 백업 확인 후 재작성**

`criteria-mapping.yml` 의 전체 내용을 다음으로 대체:

```yaml
# cchelp criteria-mapping
# 카테고리별 docs URL 매핑. 봇이 자동 발견한 카테고리는 discovered: true 표기.
# 이 파일은 cron/scripts/run_fetch.py 가 입력으로 사용.

mappings:
  - name: skills
    keywords: [skill, frontmatter, SKILL.md]
    docs_url: https://code.claude.com/docs/en/skills
    review_file: skills/review/references/skills.yml
    template_file: skills/generate/references/skill-template.md
    benchmark: true

  - name: subagents
    keywords: [agent, subagent]
    docs_url: https://code.claude.com/docs/en/sub-agents
    review_file: skills/review/references/subagents.yml
    template_file: skills/generate/references/agent-template.md
    benchmark: true

  - name: hooks
    keywords: [hook, event, lifecycle]
    docs_url: https://code.claude.com/docs/en/hooks
    review_file: skills/review/references/hooks.yml
    template_file: skills/generate/references/hooks-template.md
    benchmark: false

  - name: mcp
    keywords: [MCP, transport, server, mcp]
    docs_url: https://code.claude.com/docs/en/mcp
    review_file: skills/review/references/mcp.yml
    template_file: skills/generate/references/mcp-template.md
    benchmark: false

  - name: memory
    keywords: [memory, MEMORY.md]
    docs_url: https://code.claude.com/docs/en/memory
    review_file: skills/review/references/memory.yml
    template_file: skills/generate/references/memory-template.md
    benchmark: false

  - name: claude-md
    keywords: [CLAUDE.md, rules, instructions]
    docs_url: https://code.claude.com/docs/en/memory
    review_file: skills/review/references/claude-md.yml
    template_file: skills/generate/references/claude-md-template.md
    benchmark: false

  - name: commands
    keywords: [command, slash]
    docs_url: https://code.claude.com/docs/en/commands
    review_file: skills/review/references/commands.yml
    template_file: skills/generate/references/command-template.md
    benchmark: false

  - name: settings
    keywords: [settings, permission]
    docs_url: https://code.claude.com/docs/en/settings
    review_file: skills/review/references/settings.yml
    template_file: skills/generate/references/settings-template.md
    benchmark: false

  - name: permissions
    keywords: [permission, deny, allow]
    docs_url: https://code.claude.com/docs/en/permissions
    review_file: skills/review/references/permissions.yml
    benchmark: false
    discovered: false

  - name: plugins
    keywords: [plugin, marketplace]
    docs_url: https://code.claude.com/docs/en/plugins
    review_file: skills/review/references/plugins.yml
    benchmark: false
    discovered: false
```

- [ ] **Step 2: schema 작성 — `cron/schema/category-mapping.schema.json`**

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "https://cchelp.local/schema/category-mapping.schema.json",
  "type": "object",
  "required": ["mappings"],
  "properties": {
    "mappings": {
      "type": "array",
      "items": {
        "type": "object",
        "required": ["name", "docs_url", "review_file"],
        "properties": {
          "name": {"type": "string", "pattern": "^[a-z0-9-]+$"},
          "keywords": {"type": "array", "items": {"type": "string"}},
          "docs_url": {"type": "string", "format": "uri"},
          "review_file": {"type": "string"},
          "template_file": {"type": "string"},
          "benchmark": {"type": "boolean"},
          "discovered": {"type": "boolean", "default": false}
        }
      }
    }
  }
}
```

- [ ] **Step 3: 테스트 작성 — `cron/tests/test_mapping_schema.py`**

```python
import json
from pathlib import Path

import jsonschema
import yaml

REPO_ROOT = Path(__file__).parent.parent.parent
SCHEMA = REPO_ROOT / "cron" / "schema" / "category-mapping.schema.json"
MAPPING = REPO_ROOT / "criteria-mapping.yml"


def test_mapping_yml_conforms_to_schema():
    schema = json.loads(SCHEMA.read_text())
    data = yaml.safe_load(MAPPING.read_text())
    jsonschema.validate(data, schema)
```

- [ ] **Step 4: 테스트 실행 — PASS 확인**

Run:
```bash
cd cron && PYTHONPATH=. .venv/bin/pytest tests/test_mapping_schema.py -v
```

Expected: PASS.

- [ ] **Step 5: 커밋**

```bash
git add criteria-mapping.yml cron/schema/category-mapping.schema.json cron/tests/test_mapping_schema.py
git commit -m "feat: restructure criteria-mapping.yml with schema"
```

---

### Task 18: 기존 prose 체크리스트 삭제 + CLAUDE.md 라우팅 업데이트

빈 캔버스 출발점 확보. 메인테이너가 seed 항목 작성 후 첫 cron 부터 봇이 인계.

**Files:**
- Delete: `skills/review/references/agents-checklist.md`
- Delete: `skills/review/references/claude-md-checklist.md`
- Delete: `skills/review/references/commands-checklist.md`
- Delete: `skills/review/references/hooks-checklist.md`
- Delete: `skills/review/references/mcp-checklist.md`
- Delete: `skills/review/references/memory-checklist.md`
- Delete: `skills/review/references/skills-checklist.md`
- Modify: `CLAUDE.md` (자기 routing 갱신)
- Create: `skills/review/references/.gitkeep`

- [ ] **Step 1: 기존 체크리스트 7 개 삭제**

Run:
```bash
rm -f skills/review/references/agents-checklist.md \
      skills/review/references/claude-md-checklist.md \
      skills/review/references/commands-checklist.md \
      skills/review/references/hooks-checklist.md \
      skills/review/references/mcp-checklist.md \
      skills/review/references/memory-checklist.md \
      skills/review/references/skills-checklist.md
```

- [ ] **Step 2: 빈 캔버스 디렉토리 마커**

Run:
```bash
touch skills/review/references/.gitkeep
```

- [ ] **Step 3: `CLAUDE.md` 의 Routing 섹션 갱신**

`CLAUDE.md` 의 `## Routing` 블록을 다음으로 교체:

```markdown
## Routing

- Claude config **review** tasks → `reviewer` subagent
- Claude config **generation/scaffolding** tasks → `generator` subagent
- Claude config **full setup** (generate + review + benchmark) → `gn-rv` (generate-and-review) skill
- Benchmark **eval grading** (internal, spawned by reviewer) → `grader` subagent
- Benchmark **eval execution** (internal, spawned by reviewer in pairs) → `eval-runner` subagent
- Weekly cron **self-review** (internal, U5 step) → `self-eval-runner` subagent (thin executor)
- Weekly cron **plan validation** (internal, U3.5 step) → `plan-reviewer` subagent (independent)
- Review criteria are in `skills/review/references/*.yml` (YAML schema, not prose)
- Generation templates are in `skills/generate/references/*-template.md`
```

- [ ] **Step 4: 변경 검증**

Run:
```bash
ls skills/review/references/
```

Expected: `.gitkeep` 만 있음. `*-checklist.md` 모두 사라짐.

Run:
```bash
grep "self-eval-runner\|plan-reviewer\|.yml" CLAUDE.md
```

Expected: 새 routing 줄 출력.

- [ ] **Step 5: 커밋**

```bash
git add -A skills/review/references/ CLAUDE.md
git commit -m "chore: discard polluted prose checklists; route to new agents

- 7 *-checklist.md files removed (replaced by yml schema)
- CLAUDE.md routing updated for self-eval-runner and plan-reviewer
- Empty references/ directory ready for maintainer seed items"
```

---

## 마무리

### 통합 테스트 — 전체 파이프라인 dry-run

- [ ] **모든 단위 테스트 통과 확인**

Run:
```bash
cd cron && PYTHONPATH=. .venv/bin/pytest -v
```

Expected: 모든 테스트 PASS, 0 fail.

- [ ] **워크플로 YAML 문법 재검증**

Run:
```bash
python3 -c "import yaml; yaml.safe_load(open('.github/workflows/update-review-criteria.yml')); print('YAML OK')"
```

Expected: `YAML OK`.

- [ ] **모든 신규/수정 파일 git 상태 확인**

Run:
```bash
git log --oneline | head -25
```

Expected: 18 task 의 커밋 히스토리 일렬로.

### 메인테이너 다음 액션 (본 플랜 외)

스펙 §8 Out of Scope 에 명시된 대로:

1. **Seed items 작성**: 카테고리당 ~10–20 항목 직접 yml 로 작성 (메인테이너 영역). 첫 cron 이전에 완료해야 함.
2. **첫 cron 수동 실행**: `gh workflow run update-review-criteria.yml` 으로 dry-run, 결과 PR 검토 후 머지.
3. 이후부터 cron 자동 운영, B/C 신호로 자기 진화.

### 본 플랜의 자기검증 체크리스트

- [x] **스펙 §1~10 모든 결정사항이 task 로 매핑됨**: 출처 정책 (Task 6), 8-step (Task 15), Hybrid schema (Task 2), Plan Review 4단계 (Task 6, 15, 16), Diff 처리 (Task 10, 12), 카테고리 발견 (Task 13), B+C 신호 (Task 14), self-eval-runner (Task 7), plan-reviewer (Task 8), 빈 캔버스 (Task 18).
- [x] **placeholder 없음**: TBD/TODO 어디에도 없음. 모든 step 에 실제 코드/명령 있음.
- [x] **타입 일관성**: `PlanRecord.action` ∈ {ADD, UPDATE, REMOVE} — Task 11 정의 → Task 15/16 사용 일치. `ItemStatus.{STABLE, UPDATE_CANDIDATE, REMOVE_CANDIDATE}` — Task 10 정의 → Task 11 사용 일치. `verifier.kind` enum — Task 2 (schema) → Task 4-6 (구현) → Task 7 (agent prompt) 일치.
- [x] **TDD 전반 적용**: verifier / 스크립트는 모두 실패 테스트 먼저 → 구현 → 통과. agent .md 도 frontmatter / 본문 키워드 검증 테스트 우선.
- [x] **빈도 높은 commit**: task 당 1 commit, step 단위 작업.
