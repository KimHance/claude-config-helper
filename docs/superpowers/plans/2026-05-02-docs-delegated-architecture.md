# Docs 위임 아키텍처 구현 플랜

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**스펙:** [docs/superpowers/specs/2026-05-02-docs-delegated-architecture-design.md](../specs/2026-05-02-docs-delegated-architecture-design.md)

**목표:** cchelp 의 weekly cron pipeline 의 source of truth 를 메인테이너 큐레이션 mapping 에서 Anthropic Mintlify docsConfig 로 전환. group 단위 sub-agent 병렬 dispatch + Aggregator dedup + cchelp 카테고리 binding.

**아키텍처:** Job1 (nav-fetch + page-fetch, Python) → Job2 (group-plan matrix, claude-code-action × ~15 병렬) → Job3 (aggregate, Python) → 기존 U3.5+ 그대로.

**Tech Stack:** Python 3.11 (httpx, pyyaml, jsonschema, pytest), GitHub Actions matrix strategy, anthropics/claude-code-action.

**한국어 작성:** 메인테이너 선호.

---

## 파일 구조 (전체)

### 신규 생성

| 경로 | 책임 |
|---|---|
| `cron/scripts/nav_fetch.py` | Mintlify hydrate parse + docsConfig 추출 + page .md 병렬 fetch |
| `cron/scripts/run_nav_fetch.py` | CLI entry — Job 1 호출 |
| `cron/scripts/aggregate.py` | Group results flatten + dedup (priority + sources merge) + cchelp 카테고리 binding |
| `cron/scripts/run_aggregate.py` | CLI entry — Job 3 호출 |
| `cron/scripts/validate_group_result.py` | Sub-agent 출력 검증 (schema) — Job 2 의 self-check 용 |
| `cron/schema/group-result.schema.json` | Sub-agent 보고 형식 |
| `cron/schema/category-binding.schema.json` | mapping yml 의 새 형식 (binding rules) |
| `cron/templates/group-prompt.md` | Sub-agent 통일 prompt template |

### 수정

| 경로 | 변경 |
|---|---|
| `.github/workflows/update-review-criteria.yml` | matrix strategy 도입, Job1/2/3 분리 |
| `.github/criteria-mapping.yml` | `docs_url` 폐기, `bind` (tab/group/page_filter) 룰로 재구성 |
| `cron/schema/category-mapping.schema.json` | 새 binding schema 로 교체 |
| `cron/schema/item.schema.json` | `additional_sources[]` 옵션 필드 추가 |
| `cron/scripts/run_apply.py` | `additional_sources` 도 yml 에 적재 |
| `cron/templates/pr-body.md` | `<details>` 섹션 추가 (sub-agent results / empty pages / suspicious / aggregator stats) |

### 폐기

| 경로 | 사유 |
|---|---|
| `cron/scripts/run_fetch.py` | Job 1 (run_nav_fetch) 으로 대체 |
| `cron/scripts/run_diff.py` | Aggregator 안으로 흡수 |
| `cron/scripts/run_category_discovery.py` | docsConfig nav diff 의 자연 byproduct |
| `cron/scripts/diff.py` | Aggregator 가 직접 처리 |
| `cron/scripts/category_discovery.py` | sitemap 기반 발견 폐기 (mintlify nav 가 풍부) |
| `cron/scripts/fallback_search.py` | 본 phase 에서 미사용 (REMOVE 처리는 다음 cron 에서 자연 dedup) |

---

## Phase 1 — Schema 확장 (item + group-result + category-binding)

### Task 1: `item.schema.json` 에 `additional_sources` 필드 추가

스펙 §6.3 에 따라 dedup 시 보존된 보조 source 들의 list 필드.

**Files:**
- Modify: `cron/schema/item.schema.json`
- Modify: `cron/tests/test_item_schema.py`

- [ ] **Step 1: 새 테스트 추가**

`cron/tests/test_item_schema.py` 끝에 append:

```python
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
```

- [ ] **Step 2: 테스트 실행 — 실패 확인**

Run:
```bash
cd cron && PYTHONPATH=. .venv/bin/pytest tests/test_item_schema.py -v
```

Expected: 새 3 테스트 FAIL (`additional_sources` 미지원).

- [ ] **Step 3: `item.schema.json` 의 `properties` 에 `additional_sources` 추가**

`cron/schema/item.schema.json` 의 `"properties"` 객체 안에 (다른 properties 와 같은 들여쓰기):

```json
"additional_sources": {
  "type": "array",
  "description": "Aggregator dedup 시 priority winner 가 아닌 record 의 source 들. 출처 다중 추적용.",
  "items": {
    "type": "object",
    "required": ["url", "fetched_at", "quote"],
    "additionalProperties": false,
    "properties": {
      "url": {"type": "string", "format": "uri"},
      "fetched_at": {"type": "string", "format": "date-time"},
      "quote": {"type": "string", "minLength": 5}
    }
  }
}
```

- [ ] **Step 4: 테스트 통과 확인**

Run:
```bash
cd cron && PYTHONPATH=. .venv/bin/pytest tests/test_item_schema.py -v
```

Expected: 모든 테스트 PASS (기존 5 + 신규 3 = 8 passed).

- [ ] **Step 5: 커밋**

```bash
git add cron/schema/item.schema.json cron/tests/test_item_schema.py
git commit -m "feat(schema): add additional_sources[] to item schema for dedup merge"
```

---

### Task 2: `group-result.schema.json` 생성

Sub-agent 의 출력 형식 강제. 스펙 §6.2.

**Files:**
- Create: `cron/schema/group-result.schema.json`
- Create: `cron/tests/test_group_result_schema.py`

- [ ] **Step 1: 실패 테스트 작성**

`cron/tests/test_group_result_schema.py`:

```python
import json
from pathlib import Path

import jsonschema
import pytest

SCHEMA_PATH = Path(__file__).parent.parent / "schema" / "group-result.schema.json"


@pytest.fixture
def schema():
    return json.loads(SCHEMA_PATH.read_text())


def test_minimal_ok_result_passes(schema):
    result = {
        "tab": "Build with Claude Code",
        "group": "Agents",
        "status": "ok",
        "records": [],
        "empty_pages": [],
        "errors": [],
    }
    jsonschema.validate(result, schema)


def test_full_result_passes(schema):
    result = {
        "tab": "Reference",
        "group": "Reference",
        "status": "partial",
        "records": [
            {
                "id": "hook-input-via-stdin",
                "type": "qualitative",
                "proposition": "...",
                "verifier": {"kind": "llm-judge", "rubric": "..." * 10},
                "source": {
                    "url": "https://code.claude.com/docs/en/hooks",
                    "fetched_at": "2026-05-02T02:00:00Z",
                    "quote": "Command hooks read stdin",
                },
                "severity": "critical",
                "category_hint": "hooks",
                "page": "en/hooks",
            }
        ],
        "empty_pages": [
            {
                "page": "en/troubleshoot-install",
                "reason": "high-level guide; no verifiable schema",
                "suspicious": False,
            }
        ],
        "errors": [
            {"page": "en/some-broken", "reason": "fetch failed: 404"}
        ],
    }
    jsonschema.validate(result, schema)


def test_invalid_status_fails(schema):
    result = {
        "tab": "Reference",
        "group": "Reference",
        "status": "weird-status",
        "records": [],
        "empty_pages": [],
        "errors": [],
    }
    with pytest.raises(jsonschema.ValidationError):
        jsonschema.validate(result, schema)


def test_record_missing_category_hint_fails(schema):
    result = {
        "tab": "Reference",
        "group": "Reference",
        "status": "ok",
        "records": [
            {
                "id": "x",
                "type": "programmatic",
                "proposition": "p",
                "verifier": {"kind": "regex", "pattern": "."},
                "source": {"url": "https://e.com", "fetched_at": "2026-05-02T02:00:00Z", "quote": "qqqqq"},
                "severity": "important",
                # category_hint 누락
                "page": "en/x",
            }
        ],
        "empty_pages": [],
        "errors": [],
    }
    with pytest.raises(jsonschema.ValidationError):
        jsonschema.validate(result, schema)
```

- [ ] **Step 2: 테스트 실행 — 실패 확인**

Run:
```bash
cd cron && PYTHONPATH=. .venv/bin/pytest tests/test_group_result_schema.py -v
```

Expected: FAIL — `FileNotFoundError: schema/group-result.schema.json`.

- [ ] **Step 3: `cron/schema/group-result.schema.json` 작성**

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "https://cchelp.local/schema/group-result.schema.json",
  "title": "cchelp Group Sub-Agent Result",
  "type": "object",
  "required": ["tab", "group", "status", "records", "empty_pages", "errors"],
  "additionalProperties": false,
  "properties": {
    "tab": {"type": "string", "minLength": 2},
    "group": {"type": "string", "minLength": 2},
    "status": {"enum": ["ok", "partial", "failed"]},
    "records": {
      "type": "array",
      "items": {
        "type": "object",
        "required": ["id", "type", "proposition", "verifier", "source", "severity", "category_hint", "page"],
        "additionalProperties": false,
        "properties": {
          "id": {"type": "string", "pattern": "^[a-z0-9]+(-[a-z0-9]+)*$", "minLength": 3, "maxLength": 80},
          "type": {"enum": ["programmatic", "qualitative"]},
          "proposition": {"type": "string", "minLength": 5},
          "verifier": {"type": "object"},
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
          "severity": {"enum": ["critical", "important", "suggestion"]},
          "category_hint": {"type": "string", "minLength": 2},
          "page": {"type": "string", "minLength": 2}
        }
      }
    },
    "empty_pages": {
      "type": "array",
      "items": {
        "type": "object",
        "required": ["page", "reason"],
        "additionalProperties": false,
        "properties": {
          "page": {"type": "string"},
          "reason": {"type": "string", "minLength": 5},
          "suspicious": {"type": "boolean"},
          "patterns_found": {"type": "array", "items": {"type": "string"}},
          "diagnostic": {"type": "string"}
        }
      }
    },
    "errors": {
      "type": "array",
      "items": {
        "type": "object",
        "required": ["page", "reason"],
        "additionalProperties": false,
        "properties": {
          "page": {"type": "string"},
          "reason": {"type": "string"}
        }
      }
    }
  }
}
```

- [ ] **Step 4: 테스트 통과 확인**

Run:
```bash
cd cron && PYTHONPATH=. .venv/bin/pytest tests/test_group_result_schema.py -v
```

Expected: 4 passed.

- [ ] **Step 5: 커밋**

```bash
git add cron/schema/group-result.schema.json cron/tests/test_group_result_schema.py
git commit -m "feat(schema): add group-result schema for sub-agent output validation"
```

---

### Task 3: `category-binding.schema.json` 생성 + 기존 mapping schema 교체

스펙 §6.4 의 새 mapping yml 형식 강제.

**Files:**
- Create: `cron/schema/category-binding.schema.json`
- Modify: `cron/schema/category-mapping.schema.json` → 통째 새 형식 (legacy 용도 유지 안 함)
- Modify: `cron/tests/test_mapping_schema.py`

- [ ] **Step 1: 기존 테스트 갱신 + 새 테스트 추가**

`cron/tests/test_mapping_schema.py` 전체 교체:

```python
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
```

- [ ] **Step 2: 테스트 실행 — 실패 확인**

Run:
```bash
cd cron && PYTHONPATH=. .venv/bin/pytest tests/test_mapping_schema.py -v
```

Expected: FAIL — schema 파일 없음 + actual mapping 이 옛 형식.

- [ ] **Step 3: `cron/schema/category-binding.schema.json` 작성**

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "https://cchelp.local/schema/category-binding.schema.json",
  "type": "object",
  "required": ["categories"],
  "additionalProperties": false,
  "properties": {
    "categories": {
      "type": "array",
      "items": {
        "type": "object",
        "required": ["name", "bind", "review_file"],
        "additionalProperties": false,
        "properties": {
          "name": {"type": "string", "pattern": "^[a-z0-9-]+$"},
          "bind": {
            "type": "array",
            "minItems": 1,
            "items": {
              "type": "object",
              "required": ["tab", "group"],
              "additionalProperties": false,
              "properties": {
                "tab": {"type": "string"},
                "group": {"type": "string"},
                "page_filter": {"type": "string"}
              }
            }
          },
          "review_file": {"type": "string"},
          "template_file": {"type": "string"},
          "benchmark": {"type": "boolean"}
        }
      }
    },
    "excluded_tabs": {
      "type": "array",
      "items": {"type": "string"}
    },
    "priority": {
      "type": "object",
      "required": ["tabs"],
      "additionalProperties": false,
      "properties": {
        "tabs": {
          "type": "array",
          "items": {"type": "string"},
          "minItems": 1
        }
      }
    }
  }
}
```

- [ ] **Step 4: 옛 `category-mapping.schema.json` 폐기**

```bash
git rm cron/schema/category-mapping.schema.json
```

- [ ] **Step 5: Task 9 (mapping yml 재작성) 후 다시 테스트 실행 — 모든 5 테스트 통과**

본 task 단독으로는 `test_actual_mapping_yml_conforms` 만 fail 남음. 다른 4개 테스트 PASS 확인 후 commit.

Run:
```bash
cd cron && PYTHONPATH=. .venv/bin/pytest tests/test_mapping_schema.py -k "not actual" -v
```

Expected: 4 passed.

- [ ] **Step 6: 커밋**

```bash
git add cron/schema/category-binding.schema.json cron/tests/test_mapping_schema.py
git rm cron/schema/category-mapping.schema.json
git commit -m "feat(schema): replace category-mapping with category-binding (tab/group rules)"
```

---

## Phase 2 — nav-fetch (Job 1)

### Task 4: `nav_fetch.py` — Mintlify hydrate 추출 + page 병렬 fetch

**Files:**
- Create: `cron/scripts/nav_fetch.py`
- Create: `cron/tests/test_nav_fetch.py`
- Create: `cron/tests/fixtures/sample-hydrate.html`

- [ ] **Step 1: Fixture HTML 작성**

`cron/tests/fixtures/sample-hydrate.html` 작성 — 실제 Mintlify chunk 구조 simul:

```html
<!DOCTYPE html>
<html><body>
<script>self.__next_f.push([1,"0:hello"])</script>
<script>self.__next_f.push([1,"33:[\"$\",\"$L34\",null,{\"value\":{\"docsConfig\":{\"theme\":\"mint\",\"navigation\":{\"languages\":[{\"language\":\"en\",\"tabs\":[{\"tab\":\"Build with Claude Code\",\"groups\":[{\"group\":\"Agents\",\"pages\":[\"en/sub-agents\",\"en/agent-teams\"]}]},{\"tab\":\"Agent SDK\",\"groups\":[{\"group\":\"SDK\",\"pages\":[\"en/agent-sdk/overview\"]}]}]}]}}}}]"])</script>
</body></html>
```

- [ ] **Step 2: 실패 테스트 작성**

`cron/tests/test_nav_fetch.py`:

```python
from pathlib import Path

import pytest

from scripts.nav_fetch import (
    NavExtractError,
    extract_docs_config,
    extract_pages_to_fetch,
    fetch_page_md,
    slug_safe,
)

FIXTURES = Path(__file__).parent / "fixtures"


def test_extract_docs_config_from_sample_html():
    html = (FIXTURES / "sample-hydrate.html").read_text()
    nav = extract_docs_config(html)
    assert "languages" in nav
    en = next(l for l in nav["languages"] if l["language"] == "en")
    assert len(en["tabs"]) == 2


def test_extract_docs_config_raises_on_no_chunk():
    with pytest.raises(NavExtractError):
        extract_docs_config("<html><body>no chunks here</body></html>")


def test_extract_docs_config_raises_on_malformed_chunk():
    html = '<script>self.__next_f.push([1,"docsConfig but not json"])</script>'
    with pytest.raises(NavExtractError):
        extract_docs_config(html)


def test_extract_pages_excludes_tabs():
    nav = {
        "languages": [{
            "language": "en",
            "tabs": [
                {"tab": "Build with Claude Code", "groups": [
                    {"group": "Agents", "pages": ["en/sub-agents", "en/agent-teams"]}
                ]},
                {"tab": "Agent SDK", "groups": [
                    {"group": "SDK", "pages": ["en/agent-sdk/overview"]}
                ]},
            ]
        }]
    }
    out = extract_pages_to_fetch(nav, excluded_tabs=["Agent SDK"])
    assert out["tabs"][0]["tab"] == "Build with Claude Code"
    assert len(out["tabs"]) == 1
    pages = [p for tab in out["tabs"] for grp in tab["groups"] for p in grp["pages"]]
    assert "en/sub-agents" in pages
    assert "en/agent-sdk/overview" not in pages


def test_slug_safe():
    assert slug_safe("Build with Claude Code") == "build-with-claude-code"
    assert slug_safe("Tools and plugins") == "tools-and-plugins"
    assert slug_safe("Settings & Permissions!") == "settings-permissions"


def test_fetch_page_md_appends_md_suffix(tmp_path, httpx_mock):
    httpx_mock.add_response(
        url="https://code.claude.com/docs/en/skills.md",
        text="# Skills\n\nbody",
    )
    out = fetch_page_md("en/skills", tmp_path)
    assert out.name == "en__skills.md"
    assert "# Skills" in out.read_text()
```

- [ ] **Step 3: 테스트 실행 — 실패 확인**

Run:
```bash
cd cron && PYTHONPATH=. .venv/bin/pytest tests/test_nav_fetch.py -v
```

Expected: FAIL — `ModuleNotFoundError`.

- [ ] **Step 4: `cron/scripts/nav_fetch.py` 구현**

```python
"""Mintlify hydrate parse + docsConfig 추출 + page .md 병렬 fetch."""
import json
import re
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from pathlib import Path

import httpx

DOCS_BASE = "https://code.claude.com/docs"
ENTRY_URL = f"{DOCS_BASE}/en/skills"  # hydrate chunk 가 들어있는 임의 page


class NavExtractError(Exception):
    """Mintlify hydrate 형식 변경 또는 추출 실패."""


def _decode_chunk(chunk: str) -> str:
    """Next.js push payload 의 escape 시퀀스 디코딩."""
    return chunk.encode().decode("unicode_escape")


def _extract_balanced_object(text: str, key_marker: str) -> str | None:
    """JSON 안의 특정 key 다음 balanced { ... } 객체 substring 반환."""
    idx = text.find(key_marker)
    if idx == -1:
        return None
    j = idx + len(key_marker)
    while j < len(text) and text[j] in " \n\t":
        j += 1
    if j >= len(text) or text[j] != "{":
        return None
    depth = 0
    start = j
    while j < len(text):
        c = text[j]
        if c == "{":
            depth += 1
        elif c == "}":
            depth -= 1
            if depth == 0:
                return text[start : j + 1]
        j += 1
    return None


def extract_docs_config(html: str) -> dict:
    """Streaming SSR chunks 에서 docsConfig.navigation 객체 추출."""
    chunks = re.findall(r'self\.__next_f\.push\(\[1,"(.*?)"\]\)', html, re.DOTALL)
    target = next((c for c in chunks if '"docsConfig"' in c), None)
    if target is None:
        raise NavExtractError("docsConfig chunk not found in hydrate stream")
    try:
        decoded = _decode_chunk(target)
    except UnicodeDecodeError as e:
        raise NavExtractError(f"chunk decode error: {e}")
    nav_str = _extract_balanced_object(decoded, '"navigation":')
    if nav_str is None:
        raise NavExtractError("navigation object not found in docsConfig")
    try:
        return json.loads(nav_str)
    except json.JSONDecodeError as e:
        raise NavExtractError(f"navigation JSON parse error: {e}")


def extract_pages_to_fetch(nav: dict, *, excluded_tabs: list[str], language: str = "en") -> dict:
    """nav 에서 excluded_tabs 제외 후 fetch 대상 구조 반환."""
    lang_entry = next((l for l in nav["languages"] if l["language"] == language), None)
    if lang_entry is None:
        raise NavExtractError(f"language '{language}' not found")
    excluded = set(excluded_tabs)
    out_tabs = []
    for tab in lang_entry["tabs"]:
        if tab["tab"] in excluded:
            continue
        out_tabs.append(tab)
    return {"language": language, "tabs": out_tabs, "excluded_tabs": list(excluded)}


def slug_safe(name: str) -> str:
    """group 이름을 파일명/artifact 안전한 slug 로 변환."""
    s = re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")
    return s or "unnamed"


def fetch_page_md(page_slug: str, out_dir: Path) -> Path:
    """page slug (예: en/skills) → .md fetch + 저장."""
    out_dir.mkdir(parents=True, exist_ok=True)
    url = f"{DOCS_BASE}/{page_slug}.md"
    resp = httpx.get(url, follow_redirects=True, timeout=60.0)
    resp.raise_for_status()
    fname = page_slug.replace("/", "__") + ".md"
    out = out_dir / fname
    out.write_text(resp.text, encoding="utf-8")
    return out


def fetch_all_pages(structure: dict, out_dir: Path, *, max_workers: int = 10) -> list[Path]:
    """structure 의 모든 page 병렬 fetch."""
    pages = [
        p
        for tab in structure["tabs"]
        for grp in tab["groups"]
        for p in _flatten_pages(grp.get("pages", []))
    ]
    paths: list[Path] = []
    with ThreadPoolExecutor(max_workers=max_workers) as ex:
        futures = {ex.submit(fetch_page_md, p, out_dir): p for p in pages}
        for fut in as_completed(futures):
            paths.append(fut.result())
    return paths


def _flatten_pages(pages: list) -> list[str]:
    """sub-group 의 nested pages 까지 flatten."""
    out: list[str] = []
    for p in pages:
        if isinstance(p, str):
            out.append(p)
        elif isinstance(p, dict) and "pages" in p:
            out.extend(_flatten_pages(p["pages"]))
    return out


def fetch_entry_html(*, url: str = ENTRY_URL) -> str:
    """hydrate chunk 가 박힌 entry page HTML fetch."""
    resp = httpx.get(url, follow_redirects=True, timeout=60.0)
    resp.raise_for_status()
    return resp.text


def write_nav_json(structure: dict, out_path: Path, *, source: str = ENTRY_URL) -> None:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "fetched_at": datetime.now(timezone.utc).isoformat(),
        "source": source,
        **structure,
    }
    out_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False))
```

- [ ] **Step 5: 테스트 통과 확인**

Run:
```bash
cd cron && PYTHONPATH=. .venv/bin/pytest tests/test_nav_fetch.py -v
```

Expected: 6 passed.

- [ ] **Step 6: 커밋**

```bash
git add cron/scripts/nav_fetch.py cron/tests/test_nav_fetch.py cron/tests/fixtures/sample-hydrate.html
git commit -m "feat: add nav_fetch (mintlify hydrate parse + page md fetch)"
```

---

### Task 5: `run_nav_fetch.py` — CLI entry

**Files:**
- Create: `cron/scripts/run_nav_fetch.py`
- Create: `cron/tests/test_run_nav_fetch.py`

- [ ] **Step 1: 테스트**

`cron/tests/test_run_nav_fetch.py`:

```python
from pathlib import Path

from scripts.nav_fetch import write_nav_json


def test_write_nav_json_minimal(tmp_path):
    structure = {
        "language": "en",
        "tabs": [
            {"tab": "Reference", "groups": [{"group": "R", "pages": ["en/r"]}]}
        ],
        "excluded_tabs": [],
    }
    out = tmp_path / "nav.json"
    write_nav_json(structure, out, source="https://x")
    import json
    data = json.loads(out.read_text())
    assert data["language"] == "en"
    assert data["source"] == "https://x"
    assert "fetched_at" in data
```

- [ ] **Step 2: `cron/scripts/run_nav_fetch.py` 구현**

```python
"""CLI entry: Job 1 — nav-fetch + page-fetch."""
import argparse
import sys
from pathlib import Path

import yaml

from scripts.nav_fetch import (
    NavExtractError,
    extract_docs_config,
    extract_pages_to_fetch,
    fetch_all_pages,
    fetch_entry_html,
    write_nav_json,
)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--mapping", required=True, type=Path)
    ap.add_argument("--out-nav", required=True, type=Path)
    ap.add_argument("--out-fetched", required=True, type=Path)
    args = ap.parse_args()

    mapping = yaml.safe_load(args.mapping.read_text()) or {}
    excluded_tabs = mapping.get("excluded_tabs", [])

    try:
        html = fetch_entry_html()
        nav = extract_docs_config(html)
    except NavExtractError as e:
        print(f"FATAL: nav extraction failed: {e}", file=sys.stderr)
        return 1
    except Exception as e:
        print(f"FATAL: entry html fetch failed: {e}", file=sys.stderr)
        return 1

    structure = extract_pages_to_fetch(nav, excluded_tabs=excluded_tabs)
    write_nav_json(structure, args.out_nav)

    paths = fetch_all_pages(structure, args.out_fetched)
    print(f"fetched {len(paths)} pages → {args.out_fetched}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```

- [ ] **Step 3: 테스트 통과 확인**

Run:
```bash
cd cron && PYTHONPATH=. .venv/bin/pytest tests/test_run_nav_fetch.py -v
```

Expected: 1 passed.

- [ ] **Step 4: 커밋**

```bash
git add cron/scripts/run_nav_fetch.py cron/tests/test_run_nav_fetch.py
git commit -m "feat: add run_nav_fetch CLI entry for Job 1"
```

---

## Phase 3 — Aggregator (Job 3)

### Task 6: `aggregate.py` — flatten + dedup + binding

**Files:**
- Create: `cron/scripts/aggregate.py`
- Create: `cron/tests/test_aggregate.py`

- [ ] **Step 1: 실패 테스트**

`cron/tests/test_aggregate.py`:

```python
from scripts.aggregate import (
    bind_to_categories,
    dedup_records,
    flatten_group_results,
    page_matches_filter,
)


def _record(id_, source_url, page, quote="some valid quote", category_hint="hooks"):
    return {
        "id": id_,
        "type": "qualitative",
        "proposition": "p" + id_,
        "verifier": {"kind": "llm-judge", "rubric": "rrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrr"},
        "source": {"url": source_url, "fetched_at": "2026-05-02T00:00:00Z", "quote": quote},
        "severity": "important",
        "category_hint": category_hint,
        "page": page,
    }


def test_flatten_collects_all_records():
    g1 = {
        "tab": "Build with Claude Code", "group": "Automation", "status": "ok",
        "records": [_record("a", "u1", "en/hooks-guide")],
        "empty_pages": [], "errors": [],
    }
    g2 = {
        "tab": "Reference", "group": "Reference", "status": "ok",
        "records": [_record("b", "u2", "en/hooks")],
        "empty_pages": [], "errors": [],
    }
    flat = flatten_group_results([g1, g2])
    assert len(flat) == 2
    assert {r["record"]["id"] for r in flat} == {"a", "b"}
    # tab/group meta 가 record 에 attach 됐는지
    a = next(r for r in flat if r["record"]["id"] == "a")
    assert a["tab"] == "Build with Claude Code"
    assert a["group"] == "Automation"


def test_dedup_priority_reference_wins():
    flat = [
        {"tab": "Build with Claude Code", "group": "Automation",
         "record": _record("hook-x", "https://docs/hooks-guide", "en/hooks-guide", quote="guide quote")},
        {"tab": "Reference", "group": "Reference",
         "record": _record("hook-x", "https://docs/hooks", "en/hooks", quote="reference quote")},
    ]
    priority_tabs = ["Reference", "Configuration", "Administration", "Build with Claude Code"]
    deduped = dedup_records(flat, priority_tabs=priority_tabs)
    assert len(deduped) == 1
    winner = deduped[0]
    assert winner["source"]["url"] == "https://docs/hooks"  # Reference 우선
    assert winner["additional_sources"][0]["url"] == "https://docs/hooks-guide"
    assert winner["additional_sources"][0]["quote"] == "guide quote"


def test_dedup_no_collision_passes_through():
    flat = [
        {"tab": "Reference", "group": "Reference",
         "record": _record("a", "u1", "en/x")},
        {"tab": "Reference", "group": "Reference",
         "record": _record("b", "u2", "en/y")},
    ]
    deduped = dedup_records(flat, priority_tabs=["Reference"])
    assert len(deduped) == 2
    assert all("additional_sources" not in r for r in deduped)


def test_page_matches_filter_glob():
    assert page_matches_filter("en/hooks-guide", "hooks*")
    assert page_matches_filter("en/hooks", "hooks*")
    assert not page_matches_filter("en/skills", "hooks*")
    assert page_matches_filter("en/skills", "skills")
    assert page_matches_filter("en/skills", None)  # filter 없으면 모두 매치


def test_bind_to_categories_with_rules():
    deduped = [
        {**_record("hook-x", "https://docs/hooks", "en/hooks", category_hint="hooks"),
         "_tab": "Reference", "_group": "Reference"},
        {**_record("skill-y", "https://docs/skills", "en/skills", category_hint="skills"),
         "_tab": "Build with Claude Code", "_group": "Tools and plugins"},
    ]
    binding = {
        "categories": [
            {"name": "hooks", "bind": [{"tab": "Reference", "group": "Reference", "page_filter": "hooks*"}], "review_file": "hooks.yml"},
            {"name": "skills", "bind": [{"tab": "Build with Claude Code", "group": "Tools and plugins", "page_filter": "skills"}], "review_file": "skills.yml"},
        ]
    }
    bound = bind_to_categories(deduped, binding)
    by_cat = {r["category"] for r in bound}
    assert by_cat == {"hooks", "skills"}
```

- [ ] **Step 2: 테스트 실행 — 실패 확인**

Run:
```bash
cd cron && PYTHONPATH=. .venv/bin/pytest tests/test_aggregate.py -v
```

Expected: FAIL.

- [ ] **Step 3: `cron/scripts/aggregate.py` 구현**

```python
"""Aggregator: group-result*.json flatten → dedup → cchelp 카테고리 binding."""
import fnmatch
from collections import OrderedDict


def flatten_group_results(group_results: list[dict]) -> list[dict]:
    """모든 group result 의 records 를 [{tab, group, record}] flat list 로 변환."""
    out: list[dict] = []
    for gr in group_results:
        if gr.get("status") == "failed":
            continue
        for rec in gr.get("records", []):
            out.append({"tab": gr["tab"], "group": gr["group"], "record": rec})
    return out


def _tab_priority(tab: str, priority_tabs: list[str]) -> int:
    try:
        return priority_tabs.index(tab)
    except ValueError:
        return len(priority_tabs)


def dedup_records(flat: list[dict], *, priority_tabs: list[str]) -> list[dict]:
    """
    같은 id 충돌 시 priority winner 선정 + 비-winner source → additional_sources[].

    Returns: list[record_with_meta] — record 자체 dict, _tab/_group 첨부.
    """
    by_id: OrderedDict[str, list[dict]] = OrderedDict()
    for entry in flat:
        rid = entry["record"]["id"]
        by_id.setdefault(rid, []).append(entry)

    deduped: list[dict] = []
    for rid, entries in by_id.items():
        if len(entries) == 1:
            e = entries[0]
            r = dict(e["record"])
            r["_tab"] = e["tab"]
            r["_group"] = e["group"]
            deduped.append(r)
            continue

        # priority 정렬 — 가장 우선 (lowest index) 가 winner
        entries_sorted = sorted(entries, key=lambda e: _tab_priority(e["tab"], priority_tabs))
        winner = entries_sorted[0]
        losers = entries_sorted[1:]

        winner_record = dict(winner["record"])
        winner_record["_tab"] = winner["tab"]
        winner_record["_group"] = winner["group"]
        winner_record["additional_sources"] = [
            {
                "url": l["record"]["source"]["url"],
                "fetched_at": l["record"]["source"]["fetched_at"],
                "quote": l["record"]["source"]["quote"],
            }
            for l in losers
        ]
        deduped.append(winner_record)

    return deduped


def page_matches_filter(page: str, page_filter: str | None) -> bool:
    """page slug 가 page_filter (glob) 매칭하는지. None 이면 모두 매치."""
    if page_filter is None:
        return True
    # page 는 'en/<slug>' 형식; 마지막 segment 만 비교
    last = page.rsplit("/", 1)[-1]
    return fnmatch.fnmatch(last, page_filter)


def _bind_record(record: dict, binding: dict) -> str | None:
    """record 의 (tab, group, page) 가 어느 cchelp 카테고리에 매칭하는지."""
    tab = record.get("_tab", "")
    group = record.get("_group", "")
    page = record.get("page", "")
    for cat in binding.get("categories", []):
        for rule in cat["bind"]:
            if rule["tab"] != tab:
                continue
            if rule["group"] != group:
                continue
            if not page_matches_filter(page, rule.get("page_filter")):
                continue
            return cat["name"]
    return None


def bind_to_categories(deduped: list[dict], binding: dict) -> list[dict]:
    """
    record list 를 binding rules 와 매칭 → category 결정.

    매칭 안 되면 record.category_hint 가 cchelp 카테고리 list 에 있는지 확인,
    있으면 그 카테고리 사용. 그래도 없으면 'discovered:<page-slug>'.
    """
    known_categories = {c["name"] for c in binding.get("categories", [])}
    out: list[dict] = []
    for rec in deduped:
        cat = _bind_record(rec, binding)
        if cat is None:
            hint = rec.get("category_hint", "")
            if hint in known_categories:
                cat = hint
            else:
                page = rec.get("page", "unknown").replace("/", "-")
                cat = f"discovered:{page}"
        # 정리: 내부 meta (_tab/_group) 제거하고 category 박기
        clean = {k: v for k, v in rec.items() if not k.startswith("_") and k != "category_hint"}
        clean["category"] = cat
        out.append(clean)
    return out


def build_plan_records(bound: list[dict]) -> list[dict]:
    """bound records → plan.json 형식 (action ADD record list)."""
    return [
        {
            "category": r["category"],
            "action": "ADD",
            "item_id": r["id"],
            "payload": {k: v for k, v in r.items() if k != "category"} | {"category": r["category"]},
        }
        for r in bound
    ]
```

- [ ] **Step 4: 테스트 통과 확인**

Run:
```bash
cd cron && PYTHONPATH=. .venv/bin/pytest tests/test_aggregate.py -v
```

Expected: 5 passed.

- [ ] **Step 5: 커밋**

```bash
git add cron/scripts/aggregate.py cron/tests/test_aggregate.py
git commit -m "feat: add aggregate (flatten + dedup priority + category binding)"
```

---

### Task 7: `run_aggregate.py` — CLI entry

**Files:**
- Create: `cron/scripts/run_aggregate.py`

- [ ] **Step 1: 구현**

```python
"""CLI entry: Job 3 — aggregate group-result-*.json → plan.json."""
import argparse
import json
from pathlib import Path

import yaml

from scripts.aggregate import (
    bind_to_categories,
    build_plan_records,
    dedup_records,
    flatten_group_results,
)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--group-results-dir", required=True, type=Path)
    ap.add_argument("--mapping", required=True, type=Path)
    ap.add_argument("--out", required=True, type=Path)
    args = ap.parse_args()

    binding = yaml.safe_load(args.mapping.read_text()) or {}
    priority_tabs = (binding.get("priority") or {}).get("tabs", [])

    group_results: list[dict] = []
    for f in sorted(args.group_results_dir.glob("group-result-*.json")):
        group_results.append(json.loads(f.read_text()))

    flat = flatten_group_results(group_results)
    deduped = dedup_records(flat, priority_tabs=priority_tabs)
    bound = bind_to_categories(deduped, binding)
    plan = build_plan_records(bound)

    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(plan, indent=2, ensure_ascii=False))
    print(f"aggregated {len(plan)} records → {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```

- [ ] **Step 2: smoke test**

Run:
```bash
cd cron && PYTHONPATH=. .venv/bin/python -c "from scripts import run_aggregate; print('imports OK')"
```

Expected: `imports OK`.

- [ ] **Step 3: 커밋**

```bash
git add cron/scripts/run_aggregate.py
git commit -m "feat: add run_aggregate CLI entry for Job 3"
```

---

### Task 8: `validate_group_result.py` — sub-agent self-check

**Files:**
- Create: `cron/scripts/validate_group_result.py`

- [ ] **Step 1: 구현**

```python
"""Sub-agent 가 자기 group-result-*.json 작성 후 schema 사전 검증 용 CLI."""
import argparse
import json
import sys
from pathlib import Path

import jsonschema

SCHEMA_PATH = Path(__file__).parent.parent / "schema" / "group-result.schema.json"
ITEM_SCHEMA_PATH = Path(__file__).parent.parent / "schema" / "item.schema.json"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--file", required=True, type=Path)
    args = ap.parse_args()

    schema = json.loads(SCHEMA_PATH.read_text())
    item_schema = json.loads(ITEM_SCHEMA_PATH.read_text())
    data = json.loads(args.file.read_text())

    try:
        jsonschema.validate(data, schema)
    except jsonschema.ValidationError as e:
        print(f"FAIL: group-result schema violation: {e.message}", file=sys.stderr)
        return 1

    # records 의 verifier 도 item.schema 의 verifier oneOf 로 추가 검증
    for idx, rec in enumerate(data.get("records", [])):
        # item.schema 와 일치하는 record subset 만 추출 (page/category_hint 제외)
        item_view = {k: v for k, v in rec.items() if k not in ("page", "category_hint")}
        item_view["category"] = rec["category_hint"]  # item.schema 는 category 필드 요구
        try:
            jsonschema.validate(item_view, item_schema)
        except jsonschema.ValidationError as e:
            print(f"FAIL: record[{idx}] item-schema violation: {e.message}", file=sys.stderr)
            return 1

    print(f"OK: group-result valid ({len(data.get('records', []))} records)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```

- [ ] **Step 2: smoke test (수동, valid sample 로)**

Run:
```bash
cd cron && \
cat > /tmp/valid-group-result.json <<'EOF'
{
  "tab": "Reference",
  "group": "Reference",
  "status": "ok",
  "records": [],
  "empty_pages": [],
  "errors": []
}
EOF
PYTHONPATH=. .venv/bin/python -m scripts.validate_group_result --file /tmp/valid-group-result.json
```

Expected: `OK: group-result valid (0 records)`.

- [ ] **Step 3: 커밋**

```bash
git add cron/scripts/validate_group_result.py
git commit -m "feat: add validate_group_result for sub-agent self-check"
```

---

## Phase 4 — mapping yml 재작성 + Sub-agent prompt template

### Task 9: `criteria-mapping.yml` 새 형식으로 재작성

**Files:**
- Modify: `.github/criteria-mapping.yml` (전체 교체)

- [ ] **Step 1: 새 mapping 작성**

`.github/criteria-mapping.yml` 전체 내용을 다음으로 교체:

```yaml
# cchelp criteria-mapping (binding rules 형식)
# 카테고리 → tab/group 매핑. page list 는 mintlify docsConfig 가 자동 갱신.
# Aggregator 가 record 의 (tab, group, page) 보고 카테고리 binding.

categories:
  - name: skills
    bind:
      - tab: "Build with Claude Code"
        group: "Tools and plugins"
        page_filter: "skills"
    review_file: skills/review/references/skills.yml
    template_file: skills/generate/references/skill-template.md
    benchmark: true

  - name: subagents
    bind:
      - tab: "Build with Claude Code"
        group: "Agents"
    review_file: skills/review/references/subagents.yml
    template_file: skills/generate/references/agent-template.md
    benchmark: true

  - name: hooks
    bind:
      - tab: "Build with Claude Code"
        group: "Automation"
        page_filter: "hooks*"
      - tab: "Reference"
        group: "Reference"
        page_filter: "hooks*"
    review_file: skills/review/references/hooks.yml
    template_file: skills/generate/references/hooks-template.md

  - name: mcp
    bind:
      - tab: "Build with Claude Code"
        group: "Tools and plugins"
        page_filter: "mcp"
    review_file: skills/review/references/mcp.yml
    template_file: skills/generate/references/mcp-template.md

  - name: memory
    bind:
      - tab: "Getting started"
        group: "Use Claude Code"
        page_filter: "memory"
    review_file: skills/review/references/memory.yml
    template_file: skills/generate/references/memory-template.md

  - name: claude-md
    bind:
      - tab: "Getting started"
        group: "Use Claude Code"
        page_filter: "memory"
    review_file: skills/review/references/claude-md.yml
    template_file: skills/generate/references/claude-md-template.md

  - name: commands
    bind:
      - tab: "Reference"
        group: "Reference"
        page_filter: "commands"
    review_file: skills/review/references/commands.yml
    template_file: skills/generate/references/command-template.md

  - name: settings
    bind:
      - tab: "Configuration"
        group: "Settings and permissions"
        page_filter: "settings"
    review_file: skills/review/references/settings.yml
    template_file: skills/generate/references/settings-template.md

  - name: permissions
    bind:
      - tab: "Configuration"
        group: "Settings and permissions"
        page_filter: "permissions"
    review_file: skills/review/references/permissions.yml

  - name: plugins
    bind:
      - tab: "Build with Claude Code"
        group: "Tools and plugins"
        page_filter: "plugins"
      - tab: "Build with Claude Code"
        group: "Tools and plugins"
        page_filter: "discover-plugins"
      - tab: "Reference"
        group: "Reference"
        page_filter: "plugins-reference"
      - tab: "Administration"
        group: "Plugin distribution"
        page_filter: "plugin-marketplaces"
    review_file: skills/review/references/plugins.yml

excluded_tabs:
  - "Agent SDK"
  - "What's New"
  - "Resources"

priority:
  tabs:
    - "Reference"
    - "Configuration"
    - "Administration"
    - "Build with Claude Code"
    - "Getting started"
```

- [ ] **Step 2: 새 schema 로 검증**

Run:
```bash
cd /Users/hancekim/claude-config-helper/cron && \
PYTHONPATH=. .venv/bin/pytest tests/test_mapping_schema.py -v
```

Expected: 5 passed (이제 actual mapping 도 통과).

- [ ] **Step 3: 커밋**

```bash
git add .github/criteria-mapping.yml
git commit -m "feat(mapping): rewrite criteria-mapping with bind rules (tab/group)"
```

---

### Task 10: `cron/templates/group-prompt.md` 작성

**Files:**
- Create: `cron/templates/group-prompt.md`

- [ ] **Step 1: 파일 작성**

```markdown
# Sub-Agent Prompt: Group Plan

너는 cchelp cron pipeline 의 group-plan sub-agent 다.
너의 작업 단위 = 단일 group ([${TAB}] 의 [${GROUP}]).

## STEP 0 — Schema 강제 (필수)

다음을 Read 도구로 읽어라:
- `cron/schema/item.schema.json` — 각 record payload 가 통과해야 할 schema
- `cron/schema/group-result.schema.json` — 너의 출력 형식

핵심 enum (위반 시 즉시 reject):
- `verifier.kind`: regex | line-count | file-exists | substring | yaml-parse | json-schema | shell | llm-judge
- `severity`: critical | important | suggestion
- `type`: programmatic | qualitative

## STEP 1 — 입력

artifact: `${RUN_DIR}/fetched/`
대상 page: `${PAGES}` (예: `en__hooks-guide.md`, `en__channels.md`)

binding rules (이 group 에 매칭되는 mapping yml 발췌):
```yaml
${MAPPING_RULES_FOR_THIS_GROUP}
```

cchelp 카테고리 list (LLM fallback hint 용):
`[skills, subagents, hooks, mcp, commands, memory, claude-md, settings, permissions, plugins]`

## STEP 2 — 페이지별 records 추출

각 page 에서:

1. **검증 가능한 사실** 추출 (frontmatter table row, schema 제약, 명시적 수치 한도, 동작 정의 등)
2. **quote 는 verbatim substring** 이어야 한다. paraphrase / 환각 금지.
3. **id**: kebab-case unique. 예: `hook-input-via-stdin`, `skill-name-charset`.
4. **category_hint** 결정 룰:
   1. mapping rules 의 binding 매칭 → 그 카테고리 사용
   2. 매칭 없음 → cchelp 카테고리 list 중 가장 적합한 것 선택
   3. 적합한 것 없음 → `discovered:<page-slug>` 사용

## STEP 3 — 빈 결과 처리

records 0 인 page 는 `empty_pages[]` 에 reason 명시:
- "high-level guide; no verifiable schema" (정상)
- "patterns_found: [...]" + `suspicious: true` (의심 — frontmatter table 있는데 추출 0)

의심 패턴 (있는데 0 records 면 suspicious=true):
- `## Frontmatter reference` 헤더
- `| Field | Required |` 표
- ` ```yaml ` / ` ```json ` 블록
- 명시적 수치 (`max 64`, `1,536 chars` 등)

## STEP 4 — 출력 + 자체 검증

`${RUN_DIR}/group-results/group-result-${SLUG}.json` 으로 저장.

bash 로 사전 검증:

```bash
cd cron && PYTHONPATH=. .venv/bin/python -m scripts.validate_group_result \
  --file ${RUN_DIR}/group-results/group-result-${SLUG}.json
```

`OK:` 출력 시 종료. `FAIL:` 시 record 수정 후 재시도.

## 절대 하지 말 것

- 다른 group 의 결과 참조 (격리 깨짐)
- mapping rules / cchelp 카테고리 list 외 카테고리 hint 사용 (단 `discovered:` prefix 는 OK)
- quote paraphrase / 환각
- empty_pages reason 누락
- group-result.schema 위반
```

- [ ] **Step 2: 파일 존재 확인**

Run:
```bash
ls -la /Users/hancekim/claude-config-helper/cron/templates/group-prompt.md
```

Expected: 파일 존재.

- [ ] **Step 3: 커밋**

```bash
git add cron/templates/group-prompt.md
git commit -m "feat(templates): add group-prompt for sub-agent matrix dispatch"
```

---

## Phase 5 — `run_apply.py` 수정 + PR template 갱신

### Task 11: `run_apply.py` 가 `additional_sources` 보존

**Files:**
- Modify: `cron/scripts/run_apply.py`
- Modify: `cron/tests/` (필요시 신규 테스트)

- [ ] **Step 1: 현재 run_apply 확인**

Run:
```bash
cat /Users/hancekim/claude-config-helper/cron/scripts/run_apply.py
```

→ 기존 코드는 record `payload` 를 그대로 yml 에 적재. payload 안에 `additional_sources` 가 있어도 yaml.safe_dump 가 자동으로 직렬화 → **추가 변경 불필요**.

- [ ] **Step 2: 검증 테스트 추가**

`cron/tests/test_run_apply_additional_sources.py`:

```python
import json
from pathlib import Path

import yaml


def test_run_apply_preserves_additional_sources(tmp_path):
    """run_apply 가 payload 의 additional_sources 를 yml 에 그대로 직렬화."""
    plan = [
        {
            "category": "hooks",
            "action": "ADD",
            "item_id": "hook-x",
            "payload": {
                "id": "hook-x",
                "type": "qualitative",
                "proposition": "p",
                "verifier": {"kind": "llm-judge", "rubric": "r" * 30},
                "source": {
                    "url": "https://docs/hooks",
                    "fetched_at": "2026-05-02T00:00:00Z",
                    "quote": "main quote here",
                },
                "additional_sources": [
                    {
                        "url": "https://docs/hooks-guide",
                        "fetched_at": "2026-05-02T00:00:00Z",
                        "quote": "extra guide quote",
                    }
                ],
                "severity": "critical",
                "category": "hooks",
            },
        }
    ]
    review = {"approved": ["hook-x"]}
    refs_dir = tmp_path / "refs"
    refs_dir.mkdir()

    plan_file = tmp_path / "plan.json"
    plan_file.write_text(json.dumps(plan))
    review_file = tmp_path / "review.json"
    review_file.write_text(json.dumps(review))

    import subprocess
    cron_dir = Path(__file__).parent.parent
    result = subprocess.run(
        ["python", "-m", "scripts.run_apply",
         "--plan", str(plan_file),
         "--review", str(review_file),
         "--refs-dir", str(refs_dir),
         "--state-dir", str(tmp_path / "state")],
        cwd=cron_dir,
        env={"PYTHONPATH": "."},
        capture_output=True, text=True,
    )
    assert result.returncode == 0, result.stderr

    hooks_yml = refs_dir / "hooks.yml"
    assert hooks_yml.exists()
    items = yaml.safe_load(hooks_yml.read_text())
    assert len(items) == 1
    assert items[0]["additional_sources"][0]["url"] == "https://docs/hooks-guide"
```

- [ ] **Step 3: 테스트 실행**

Run:
```bash
cd cron && PYTHONPATH=. .venv/bin/pytest tests/test_run_apply_additional_sources.py -v
```

Expected: PASS (run_apply 가 이미 generic 하게 payload dump 함).

만약 실패 — run_apply.py 가 hardcode 한 필드 list 로 dump 하면 generic dump 로 수정 필요. 현재 코드 `items_by_id[r["item_id"]] = r["payload"]` → `payload` 통째 적재라 OK 예상.

- [ ] **Step 4: 커밋**

```bash
git add cron/tests/test_run_apply_additional_sources.py
git commit -m "test: verify run_apply preserves additional_sources"
```

---

### Task 12: `pr-body.md` template 에 `<details>` 섹션 추가

**Files:**
- Modify: `cron/templates/pr-body.md`

- [ ] **Step 1: 파일 갱신**

`cron/templates/pr-body.md` 전체 교체:

```markdown
# Weekly Criteria Update — {DATE}

## Releases Referenced

{RELEASES_REFERENCED}

## Categories Updated

| Category | ADD | UPDATE | REMOVE | Why |
|---|---:|---:|---:|---|
{CATEGORIES_TABLE}

## Plan Review

{PLAN_REVIEW_SUMMARY}

- Approved records: **{APPROVED_N}**
- Rejected records: **{REJECTED_N}**

## Self-Validate Signals

| Signal | Value | Meaning |
|---|---|---|
| B (회귀) | {B_SIGNAL} | 직전 cron 통과 항목 중 이번 fail |
| C (비율 drop) | {C_SIGNAL} | with-skill / baseline 비율 직전 대비 20%p 이상 하락 여부 |

<details>
<summary>📋 Sub-agent results (group breakdown)</summary>

| Group | Tab | Pages | Records | Empty | Suspicious | Errors |
|---|---|---:|---:|---:|---:|---:|
{GROUP_BREAKDOWN_TABLE}

</details>

<details>
<summary>🚫 Empty pages (reasons)</summary>

{EMPTY_PAGES_LIST}

</details>

<details>
<summary>⚠️ Suspicious empty (extraction-suspicious)</summary>

{SUSPICIOUS_LIST}

</details>

<details>
<summary>🔄 Aggregator stats</summary>

- Total records before dedup: {TOTAL_BEFORE_DEDUP}
- Duplicates merged into additional_sources: {DEDUP_MERGED}
- Final records sent to Plan Review: {TOTAL_TO_REVIEW}

</details>

## Category Discovery

{DISCOVERY_SUMMARY}

## Version Bump

{VERSION_BUMP_HINT}

---
🤖 Generated by cchelp weekly cron pipeline (delegated nav)
```

- [ ] **Step 2: 파일 갱신 확인**

Run:
```bash
grep -c "<details>" /Users/hancekim/claude-config-helper/cron/templates/pr-body.md
```

Expected: 4 (4개 details 섹션).

- [ ] **Step 3: 커밋**

```bash
git add cron/templates/pr-body.md
git commit -m "feat(templates): add details sections to PR body (sub-agent stats)"
```

---

## Phase 6 — Workflow YAML 재작성

### Task 13: `.github/workflows/update-review-criteria.yml` 통째 재작성

**Files:**
- Modify: `.github/workflows/update-review-criteria.yml`

- [ ] **Step 1: 백업**

Run:
```bash
cp /Users/hancekim/claude-config-helper/.github/workflows/update-review-criteria.yml /tmp/old-workflow.yml.bak
```

- [ ] **Step 2: 워크플로 전체 교체**

`.github/workflows/update-review-criteria.yml` 의 전체 내용을 다음으로 교체:

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
  nav-fetch:
    runs-on: ubuntu-latest
    outputs:
      groups: ${{ steps.extract.outputs.groups }}
    steps:
      - uses: actions/checkout@v4
        with: { fetch-depth: 0 }
      - uses: actions/setup-python@v5
        with: { python-version: '3.11' }
      - name: Install cron deps
        working-directory: cron
        run: |
          python -m venv .venv
          .venv/bin/pip install -e ".[dev]"
      - name: Job 1 — nav-fetch + page-fetch
        id: extract
        working-directory: cron
        run: |
          mkdir -p ${{ env.RUN_DIR }}
          PYTHONPATH=. .venv/bin/python -m scripts.run_nav_fetch \
            --mapping ../.github/criteria-mapping.yml \
            --out-nav ${{ env.RUN_DIR }}/nav.json \
            --out-fetched ${{ env.RUN_DIR }}/fetched
          # matrix 용 groups 펼치기
          groups=$(jq -c '[.tabs[] as $t | $t.groups[] | {tab: $t.tab, group: .group, pages: .pages}]' \
                       ${{ env.RUN_DIR }}/nav.json)
          echo "groups=$groups" >> $GITHUB_OUTPUT
      - uses: actions/upload-artifact@v4
        with:
          name: docs-fetched
          path: ${{ env.RUN_DIR }}
          retention-days: 14

  group-plan:
    needs: nav-fetch
    runs-on: ubuntu-latest
    strategy:
      fail-fast: false
      max-parallel: 15
      matrix:
        group: ${{ fromJson(needs.nav-fetch.outputs.groups) }}
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with: { python-version: '3.11' }
      - name: Install cron deps
        working-directory: cron
        run: |
          python -m venv .venv
          .venv/bin/pip install -e ".[dev]"
      - uses: actions/download-artifact@v4
        with:
          name: docs-fetched
          path: ${{ env.RUN_DIR }}
      - name: Job 2 — group-plan sub-agent
        uses: anthropics/claude-code-action@v1
        with:
          claude_code_oauth_token: ${{ secrets.CLAUDE_CODE_OAUTH_TOKEN }}
          claude_args: |
            --permission-mode bypassPermissions
          prompt: |
            너는 group-plan sub-agent 다.
            cron/templates/group-prompt.md 를 Read 하고 정확히 따라라.

            너의 group:
              tab: ${{ matrix.group.tab }}
              group: ${{ matrix.group.group }}
              pages: ${{ toJson(matrix.group.pages) }}

            artifact 위치: ${{ env.RUN_DIR }}/fetched/
            mapping: ../.github/criteria-mapping.yml (cchelp 카테고리 binding rules)

            출력 파일: ${{ env.RUN_DIR }}/group-results/group-result-<SLUG>.json
              SLUG = group 이름의 slugified 형 (예: "Tools and plugins" → "tools-and-plugins")
          allowed_tools: "Bash,Read,Write"
      - uses: actions/upload-artifact@v4
        if: always()
        with:
          name: group-result-${{ strategy.job-index }}
          path: ${{ env.RUN_DIR }}/group-results
          retention-days: 14
        continue-on-error: true

  aggregate:
    needs: group-plan
    if: always()
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with: { python-version: '3.11' }
      - name: Install cron deps
        working-directory: cron
        run: |
          python -m venv .venv
          .venv/bin/pip install -e ".[dev]"
      - uses: actions/download-artifact@v4
        with:
          pattern: group-result-*
          merge-multiple: true
          path: ${{ env.RUN_DIR }}/group-results
      - name: Job 3 — aggregate
        working-directory: cron
        run: |
          PYTHONPATH=. .venv/bin/python -m scripts.run_aggregate \
            --group-results-dir ${{ env.RUN_DIR }}/group-results \
            --mapping ../.github/criteria-mapping.yml \
            --out ${{ env.RUN_DIR }}/plan.json
      - uses: actions/upload-artifact@v4
        with:
          name: plan
          path: ${{ env.RUN_DIR }}/plan.json
          retention-days: 14

  plan-review:
    needs: aggregate
    runs-on: ubuntu-latest
    outputs:
      verdict: ${{ steps.check.outputs.verdict }}
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with: { python-version: '3.11' }
      - name: Install cron deps
        working-directory: cron
        run: |
          python -m venv .venv
          .venv/bin/pip install -e ".[dev]"
      - uses: actions/download-artifact@v4
        with: { name: plan, path: ${{ env.RUN_DIR }} }
      - uses: actions/download-artifact@v4
        with: { name: docs-fetched, path: ${{ env.RUN_DIR }} }
      - name: U3.5 Plan Review (independent subagent)
        uses: anthropics/claude-code-action@v1
        with:
          claude_code_oauth_token: ${{ secrets.CLAUDE_CODE_OAUTH_TOKEN }}
          claude_args: |
            --permission-mode bypassPermissions
            --agent plan-reviewer
          prompt: |
            너는 plan-reviewer agent.
            플랜: ${{ env.RUN_DIR }}/plan.json
            fetched: ${{ env.RUN_DIR }}/fetched/

            검증 1~3 (programmatic):
              cd cron && PYTHONPATH=. .venv/bin/python -m scripts.run_plan_review \
                  --plan ${{ env.RUN_DIR }}/plan.json \
                  --fetched-dir ${{ env.RUN_DIR }}/fetched/ \
                  --out ${{ env.RUN_DIR }}/plan_review_partial.json

            검증 4 (semantic, quote-based reasoning) 는 너 자신이 partial 통과 record 들에 수행.
            최종 결과 ${{ env.RUN_DIR }}/plan_review.json 저장.
      - name: Check verdict
        id: check
        run: |
          VERDICT=$(jq -r '.verdict // "approved"' ${{ env.RUN_DIR }}/plan_review.json)
          echo "verdict=$VERDICT" >> $GITHUB_OUTPUT
      - name: Notify on abort
        if: steps.check.outputs.verdict == 'aborted'
        env:
          GH_TOKEN: ${{ secrets.GITHUB_TOKEN }}
        run: |
          DATE=$(date +%Y-%m-%d)
          SUMMARY=$(jq -r '.summary // "(no summary)"' ${{ env.RUN_DIR }}/plan_review.json)
          gh issue create \
            --title "criteria cron aborted: plan review rejected ≥50% records ($DATE)" \
            --body "## Plan Review Aborted

          **Date:** $DATE
          **Run ID:** ${{ github.run_id }}

          ## Summary
          $SUMMARY" \
            --label "automated,plan-review-aborted"
      - uses: actions/upload-artifact@v4
        with:
          name: plan-review
          path: ${{ env.RUN_DIR }}/plan_review.json
          retention-days: 14

  apply-and-pr:
    needs: plan-review
    if: needs.plan-review.outputs.verdict != 'aborted'
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
        with: { fetch-depth: 0 }
      - uses: actions/setup-python@v5
        with: { python-version: '3.11' }
      - name: Install cron deps
        working-directory: cron
        run: |
          python -m venv .venv
          .venv/bin/pip install -e ".[dev]"
      - uses: actions/download-artifact@v4
        with: { name: plan, path: ${{ env.RUN_DIR }} }
      - uses: actions/download-artifact@v4
        with: { name: plan-review, path: ${{ env.RUN_DIR }} }
      - uses: actions/download-artifact@v4
        with: { name: docs-fetched, path: ${{ env.RUN_DIR }} }
      - name: U4 Apply
        working-directory: cron
        run: |
          PYTHONPATH=. .venv/bin/python -m scripts.run_apply \
            --plan ${{ env.RUN_DIR }}/plan.json \
            --review ${{ env.RUN_DIR }}/plan_review.json \
            --refs-dir ../skills/review/references \
            --state-dir state
      - name: U5 Self-validate (smoke run)
        uses: anthropics/claude-code-action@v1
        with:
          claude_code_oauth_token: ${{ secrets.CLAUDE_CODE_OAUTH_TOKEN }}
          claude_args: |
            --permission-mode bypassPermissions
            --agent self-eval-runner
          prompt: |
            너는 self-eval-runner. cchelp 자기 자신을 새 refs 로 채점.
            결과: ${{ env.RUN_DIR }}/self_eval.json
            baseline: ${{ env.RUN_DIR }}/baseline_eval.json
      - name: Compute B/C signals
        working-directory: cron
        run: |
          PYTHONPATH=. .venv/bin/python -m scripts.run_signals \
            --prev-eval state/last_self_eval.json \
            --curr-eval ${{ env.RUN_DIR }}/self_eval.json \
            --prev-metric state/last_metric.json \
            --curr-metric ${{ env.RUN_DIR }}/baseline_eval.json \
            --out ${{ env.RUN_DIR }}/signals.json
      - name: Save state
        working-directory: cron
        run: |
          PYTHONPATH=. .venv/bin/python -m scripts.run_save_state \
            --fetched-dir ${{ env.RUN_DIR }}/fetched \
            --curr-eval ${{ env.RUN_DIR }}/self_eval.json \
            --curr-metric ${{ env.RUN_DIR }}/baseline_eval.json \
            --state-dir state
      - name: Ensure required labels exist
        env:
          GH_TOKEN: ${{ secrets.GITHUB_TOKEN }}
        run: |
          set +e
          for L in automated criteria-update category-discovery self-improve-blocked plan-review-aborted extraction-suspicious; do
            gh label create "$L" --color ededed --description "auto-managed by criteria cron" 2>/dev/null
          done
          set -e
      - name: U6 Commit & PR (claude-code-action)
        uses: anthropics/claude-code-action@v1
        with:
          claude_code_oauth_token: ${{ secrets.CLAUDE_CODE_OAUTH_TOKEN }}
          claude_args: |
            --permission-mode bypassPermissions
          prompt: |
            너는 cron pipeline 의 U6 (Commit & PR) 단계.

            1. cron/templates/pr-body.md Read
            2. branch: chore/update-review-criteria-$(date +%Y-%m-%d)
            3. git config user.name "claude[bot]"; user.email "noreply@anthropic.com"
            4. add: skills/review/references/ skills/generate/references/ agents/ cron/state/
            5. 변경 없으면 "No changes; skipping PR" 후 종료
            6. commit + push (action 자체 인증)
            7. PR body 의 placeholder 채우기 (jq 로 plan_review.json / signals.json 등 추출):
               - {DATE}, {RELEASES_REFERENCED}, {CATEGORIES_TABLE}
               - {PLAN_REVIEW_SUMMARY}, {APPROVED_N}, {REJECTED_N}
               - {B_SIGNAL}, {C_SIGNAL}
               - {GROUP_BREAKDOWN_TABLE}, {EMPTY_PAGES_LIST}, {SUSPICIOUS_LIST}
               - {TOTAL_BEFORE_DEDUP}, {DEDUP_MERGED}, {TOTAL_TO_REVIEW}
               - {DISCOVERY_SUMMARY}, {VERSION_BUMP_HINT}
            8. 라벨: automated,criteria-update,
               + (discovered_categories>0)? category-discovery
               + (b_signal regressions OR c_signal dropped)? self-improve-blocked
               + (suspicious_empty>0)? extraction-suspicious
            9. gh pr create --title "chore: weekly criteria update $(date +%Y-%m-%d)"
                            --body "$BODY" --label "$LABELS"
          allowed_tools: "Bash,Read"

  auto-merge:
    needs: apply-and-pr
    if: needs.plan-review.outputs.verdict != 'aborted'
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: U7 Auto-merge if signals clear
        env:
          GH_TOKEN: ${{ secrets.GITHUB_TOKEN }}
        run: |
          BRANCH="chore/update-review-criteria-$(date +%Y-%m-%d)"
          PR_NUM=$(gh pr list --head "$BRANCH" --json number --jq '.[0].number')
          if [ -z "$PR_NUM" ]; then
            echo "No PR; skipping merge"
            exit 0
          fi
          BLOCKED=$(gh pr view "$PR_NUM" --json labels --jq '.labels | map(.name) | contains(["self-improve-blocked"]) or contains(["plan-review-aborted"])')
          if [ "$BLOCKED" = "true" ]; then
            echo "PR blocked by label"
            exit 0
          fi
          gh pr merge "$PR_NUM" --squash --auto
```

- [ ] **Step 3: YAML 검증**

Run:
```bash
cd /Users/hancekim/claude-config-helper && \
cron/.venv/bin/python -c "import yaml; yaml.safe_load(open('.github/workflows/update-review-criteria.yml')); print('YAML OK')"
```

Expected: `YAML OK`.

- [ ] **Step 4: 커밋**

```bash
git add .github/workflows/update-review-criteria.yml
git commit -m "feat(workflow): rewrite as nav-fetch / group-plan matrix / aggregate / U3.5+"
```

---

## Phase 7 — 폐기 cleanup

### Task 14: 폐기된 스크립트/모듈 제거

**Files:**
- Delete: `cron/scripts/run_fetch.py`
- Delete: `cron/scripts/fetch.py`
- Delete: `cron/scripts/run_diff.py`
- Delete: `cron/scripts/diff.py`
- Delete: `cron/scripts/run_category_discovery.py`
- Delete: `cron/scripts/category_discovery.py`
- Delete: `cron/scripts/fallback_search.py`
- Delete: `cron/tests/test_fetch.py`
- Delete: `cron/tests/test_diff.py`
- Delete: `cron/tests/test_category_discovery.py`
- Delete: `cron/tests/test_fallback_search.py`
- Modify: `cron/tests/fixtures/sample-skill/` 의 fetch 관련 fixture 그대로 유지 (다른 테스트 사용 가능)

- [ ] **Step 1: 폐기 파일 삭제**

Run:
```bash
cd /Users/hancekim/claude-config-helper && \
rm -f \
  cron/scripts/run_fetch.py \
  cron/scripts/fetch.py \
  cron/scripts/run_diff.py \
  cron/scripts/diff.py \
  cron/scripts/run_category_discovery.py \
  cron/scripts/category_discovery.py \
  cron/scripts/fallback_search.py \
  cron/tests/test_fetch.py \
  cron/tests/test_diff.py \
  cron/tests/test_category_discovery.py \
  cron/tests/test_fallback_search.py
```

- [ ] **Step 2: 전체 테스트 통과 확인**

Run:
```bash
cd /Users/hancekim/claude-config-helper/cron && \
PYTHONPATH=. .venv/bin/pytest 2>&1 | tail -5
```

Expected: 모든 테스트 PASS (폐기 모듈 import 없는 테스트만 남음).

만약 fail — 다른 테스트가 폐기 모듈을 import 하고 있으면 그 테스트도 함께 update / 삭제.

- [ ] **Step 3: 커밋**

```bash
git add -A cron/scripts/ cron/tests/
git commit -m "chore: remove deprecated fetch/diff/discovery/fallback scripts"
```

---

## 마무리

### 통합 검증

- [ ] **모든 단위 테스트 통과**

Run:
```bash
cd /Users/hancekim/claude-config-helper/cron && \
PYTHONPATH=. .venv/bin/pytest -v 2>&1 | tail -10
```

Expected: 모든 테스트 PASS.

- [ ] **Workflow YAML 문법 재검증**

Run:
```bash
cron/.venv/bin/python -c "import yaml; yaml.safe_load(open('.github/workflows/update-review-criteria.yml')); print('YAML OK')"
```

Expected: `YAML OK`.

- [ ] **Mapping yml schema 통과**

Run:
```bash
cd cron && PYTHONPATH=. .venv/bin/pytest tests/test_mapping_schema.py -v
```

Expected: 5 passed.

- [ ] **새 import path 모두 OK**

Run:
```bash
cd cron && PYTHONPATH=. .venv/bin/python -c "
from scripts import run_nav_fetch, run_aggregate, validate_group_result
from scripts.nav_fetch import NavExtractError, extract_docs_config, fetch_page_md
from scripts.aggregate import dedup_records, bind_to_categories, build_plan_records
print('all imports OK')
"
```

Expected: `all imports OK`.

### 메인테이너 다음 액션 (본 플랜 외)

1. **수동 트리거 dry-run**: `gh workflow run update-review-criteria.yml` — 새 nav 흐름 검증
2. **첫 PR 검토**: 새 형식의 PR body, `<details>` 섹션 확인
3. **Mintlify hydrate 추출 모니터링**: NavExtractError 발생 시 nav_fetch.py 의 정규식 / parsing 로직 점검 후 수정 (메인테이너 영역)

### Self-review 체크리스트

- [x] **Spec 모든 결정사항 → task 매핑**:
  - 결정 1 (병렬화 group 단위) → Task 13 의 matrix
  - 결정 2 (category_hint hybrid) → Task 6 의 `bind_to_categories`
  - 결정 3 (보고 형식 flat) → Task 2 (group-result schema)
  - 결정 4 (dedup priority + merge) → Task 6 의 `dedup_records`
  - 결정 5 (matrix dispatch + Job 분리) → Task 13
  - 결정 6 (sub-agent 격리) → Task 10 (group-prompt)
  - 결정 7 (Reference > Configuration > ... priority) → Task 9 의 mapping yml priority
  - 결정 8 (hard fail) → Task 4 의 NavExtractError + Task 5 의 sys.exit(1)
  - 결정 9 (no cache + artifact) → Task 13 의 retention-days: 14
  - 결정 10 (hybrid PR body) → Task 12

- [x] **placeholder 없음**: TBD/TODO 어디에도 없음.

- [x] **타입 일관성**:
  - `category_hint` 는 group-result.schema (Task 2) → aggregate.py (Task 6) → run_aggregate.py (Task 7) 모두 일치.
  - `additional_sources` schema (Task 1) → aggregate.py 의 dedup output (Task 6) → run_apply 적재 (Task 11) 일치.
  - `bind` 룰 schema (Task 3) → mapping yml (Task 9) → aggregate.py (Task 6) 의 `_bind_record` 일치.

- [x] **TDD 적용**: 모든 신규 모듈 (Tasks 1, 2, 3, 4, 5, 6, 7) 테스트 우선.

- [x] **Frequent commit**: task 당 1 commit.
