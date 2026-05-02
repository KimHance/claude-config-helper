# Docs 위임 아키텍처 — 디자인 스펙

**작성일:** 2026-05-02
**작성자:** KimHance (cchelp 메인테이너)
**상태:** Draft
**범위:** cchelp 의 review 항목 추출을 Anthropic 공식 docs 의 nav 구조에 위임하는 병렬 sub-agent 아키텍처.

---

## 1. 목표

cchelp 의 weekly cron pipeline 에서 **review 항목과 reference 의 source of truth** 를 메인테이너 큐레이션 mapping 에서 **Anthropic 공식 docs 의 nav 구조** 로 전환한다:

1. Source of truth = Mintlify `docsConfig` (nav: tabs > groups > pages).
2. cron 마다 nav 자동 fetch → page list 자동 갱신 (메인테이너의 `docs_url` 큐레이션 폐기).
3. Group 단위로 sub-agent 병렬 dispatch → page-level 사실 추출.
4. Aggregator 가 cross-group dedup + cchelp 카테고리별 binding.
5. 기존 U3.5+ pipeline (Plan Review / Apply / Self-validate / PR / Auto-merge) 입출력 계약 보존.

외부 사용자 가치: cchelp 가 docs 변경에 즉시 반영, 메인테이너 손이 더 줄어들고, 하나의 사실이 여러 page 에서 등장해도 cross-reference (`additional_sources`) 로 풍부한 컨텍스트 보존.

## 2. Non-Goals (이번 스펙 범위 밖)

- **9-step review orchestration 변경.** `/review` 의 9-step 골격은 안정 유지. 본 스펙은 cron 의 update workflow 변경에만 한정.
- **U3.5 Plan Review 의 검증 로직 변경.** 4 단계 검증 그대로.
- **U4 Apply / U5 Self-validate / U6 Commit & PR / U7 Auto-merge.** 입출력 계약 (plan.json schema) 만 보존하면 본문 변경 X.
- **Mintlify hydrate 형식 reverse-engineering 의 안정성 보장.** Mintlify 가 형식 바꾸면 hard fail (메인테이너 복구 영역).
- **Agent SDK / What's New / Resources 탭 처리.** `excluded_tabs` 로 통째 제외, 본 phase 에서는 review 대상 아님.

## 3. 핵심 결정사항 (브레인스토밍 결과)

| # | 영역 | 결정 |
|---|---|---|
| 1 | 병렬화 단위 | Group 단위 sub-agent (~15 개) |
| 2 | category_hint 결정 | Hybrid: mapping rules 우선 → LLM fallback → 매칭 실패는 "discovered" |
| 3 | Sub-agent 보고 형식 | Flat records + meta (status, empty_pages, errors, suspicious) |
| 4 | Aggregator dedup | Reference 우선 + `additional_sources[]` 로 모든 quote 보존 |
| 5 | Sub-agent dispatch | GitHub Actions matrix; Job 1 (fetch) / Job 2 (분석 matrix) / Job 3 (aggregate) 분리 |
| 6 | Sub-agent 격리 | Fresh context + 카테고리 list / mapping rules 만 공유 |
| 7 | Priority 순서 | Reference > Configuration > Administration > Build |
| 8 | Fallback (nav 추출 실패) | Hard fail (cron abort + GitHub issue) |
| 9 | Cache | No cache, fresh fetch + artifact 14일 보관 |
| 10 | Observability | Hybrid: 간결 PR body + `<details>` collapsed sections |

## 4. 아키텍처

### 4.1 Job 시퀀스 (전체 흐름)

```
[Job 1] nav-fetch + page-fetch       ── Python, ~1분
   ├── Mintlify docsConfig 추출 (mint.json hydrate parse)
   ├── EN tabs 필터 (excluded_tabs 제외)
   ├── 모든 target page .md 병렬 fetch
   └── artifact: nav.json + fetched/*.md
        │
        ▼
[Job 2] group-plan (matrix, 병렬 ~15)  ── claude-code-action × N, ~3분
   ├── matrix: nav.json 의 groups[]
   ├── 각 sub-agent: 자기 group 의 pages 분석 + records 추출
   ├── 격리: 다른 group 결과 모름
   └── artifact: group-result-<slug>.json (sub-agent 별)
        │
        ▼
[Job 3] aggregate                     ── Python, ~10초
   ├── 모든 group-result-*.json 수집
   ├── flatten + dedup (priority + sources merge)
   ├── category_hint 별 그룹화 → cchelp 카테고리 binding
   └── plan.json (기존 U3.5 입력 형식 그대로)
        │
        ▼
[Job 4] U3.5 Plan Review              ── 기존 그대로
[Job 5] U4 Apply                      ── 기존 그대로
[Job 6] U5 Self-validate              ── 기존 그대로
[Job 7] Compute B/C signals            ── 기존 그대로
[Job 8] Save state                    ── 기존 그대로 (state/last_nav.json 추가)
[Job 9] Ensure labels                  ── 기존 그대로
[Job 10] U6 Commit & PR               ── PR template 만 갱신 (`<details>` 섹션 추가)
[Job 11] U7 Auto-merge                 ── 기존 그대로
```

### 4.2 데이터 흐름

```
docs.claude.com (Mintlify)
       │
       ├─── /docs/en/skills          (HTML SPA)
       │     └─ <script>self.__next_f.push(...docsConfig...)</script>
       │
       └─── /docs/en/<page>.md        (raw markdown, ~50-200KB)
                            │
                            ▼
              ┌─────────────────────────┐
              │  Job 1 (Python)          │
              │   1. Fetch HTML, parse   │
              │      __next_f chunks     │
              │   2. Extract docsConfig  │
              │      .navigation         │
              │   3. Filter EN, exclude  │
              │      tabs (Agent SDK,    │
              │      What's New)         │
              │   4. Flatten page list,  │
              │      parallel fetch .md  │
              └────────────┬────────────┘
                           │
                           ▼
            ┌──────────────────────────────┐
            │ artifact: docs-fetched/       │
            │   nav.json                    │
            │   fetched/                    │
            │     en__skills.md             │
            │     en__sub-agents.md         │
            │     en__hooks-guide.md        │
            │     en__hooks.md              │
            │     ...                       │
            └──────────────┬───────────────┘
                           │
                           ▼
            ┌──────────────────────────────┐
            │ Job 2 matrix (claude-code-action × N)
            │
            │  ┌─────────────────────────────┐
            │  │ sub-agent[Automation]       │
            │  │  - download artifact        │
            │  │  - read en__hooks-guide.md, │
            │  │         en__channels.md, ...│
            │  │  - extract records          │
            │  │  - emit                     │
            │  │    group-result-Automation.json
            │  └─────────────────────────────┘
            │  ┌─────────────────────────────┐
            │  │ sub-agent[Reference]        │
            │  │  - read en__hooks.md,       │
            │  │         en__cli-reference.md│
            │  │  - emit                     │
            │  │    group-result-Reference.json
            │  └─────────────────────────────┘
            │  (~15 jobs in parallel)         │
            └──────────────┬───────────────────┘
                           │
                           ▼
            ┌──────────────────────────────┐
            │ artifact: group-results/      │
            │   group-result-Agents.json    │
            │   group-result-Tools-and-...  │
            │   group-result-Automation...  │
            │   group-result-Reference...   │
            │   ... (~15 files)             │
            └──────────────┬───────────────┘
                           │
                           ▼
            ┌──────────────────────────────┐
            │ Job 3 (Python Aggregator)     │
            │  1. flatten 모든 records      │
            │  2. category_hint 별 그룹      │
            │  3. id 충돌 dedup:            │
            │     - priority 적용 (Reference│
            │       탭 우선)                 │
            │     - 비-winner quote 들 →     │
            │       additional_sources[]    │
            │  4. cchelp 카테고리 yml 로     │
            │     매핑 (mapping yml alias)   │
            │  5. plan.json 출력            │
            └──────────────┬───────────────┘
                           │
                           ▼
                  ┌─────────────────┐
                  │  plan.json      │  ← 기존 U3.5 입력 형식
                  │  (변경 없음)     │
                  └────────┬────────┘
                           │
                           ▼
                    기존 U3.5+ pipeline
```

### 4.3 Mintlify hydrate 추출 메커니즘

```python
# nav_fetch.py 의 핵심
def extract_docs_config(html: str) -> dict:
    """Next.js streaming SSR chunks 에서 docsConfig 추출."""
    chunks = re.findall(r'self\.__next_f\.push\(\[1,"(.*?)"\]\)', html, re.DOTALL)
    target = next((c for c in chunks if '"docsConfig"' in c), None)
    if target is None:
        raise NavExtractError("docsConfig chunk not found — Mintlify format change?")
    decoded = target.encode().decode("unicode_escape")
    nav_str = _extract_balanced_object(decoded, '"navigation":')
    if nav_str is None:
        raise NavExtractError("navigation object not found")
    return json.loads(nav_str)
```

실패 모드:
- chunk 못 찾음 (Mintlify 가 hydrate 방식 변경)
- JSON 파싱 실패 (escape sequence 변동)
- navigation 키 위치 변경

→ 모두 `NavExtractError` 로 raise → Job 1 fail → cron abort + GitHub issue.

## 5. 새 / 변경 / 폐기 컴포넌트

### 5.1 신규

| 경로 | 책임 |
|---|---|
| `cron/scripts/nav_fetch.py` | Mintlify hydrate parse + docsConfig 추출 + page .md 병렬 fetch |
| `cron/scripts/run_nav_fetch.py` | CLI entry; Job 1 호출 |
| `cron/scripts/aggregate.py` | Group results flatten + dedup (priority + sources merge) + cchelp 카테고리 binding |
| `cron/scripts/run_aggregate.py` | CLI entry; Job 3 호출 |
| `cron/schema/group-result.schema.json` | Sub-agent 보고 형식 강제 |
| `cron/schema/category-binding.schema.json` | mapping yml 의 새 형식 (binding rules) |
| `cron/templates/group-prompt.md` | Sub-agent 통일 prompt template |

### 5.2 수정

| 경로 | 변경 |
|---|---|
| `.github/workflows/update-review-criteria.yml` | matrix strategy 도입, Job 1/2/3 분리, 기존 step 들 후속 job 으로 |
| `.github/criteria-mapping.yml` | `docs_url`/`docs_urls` 필드 폐기, `bind` (tab/group/page_filter) 룰로 재구성 |
| `cron/schema/category-mapping.schema.json` | 새 schema (bind rules) |
| `cron/schema/item.schema.json` | `additional_sources[]` 옵션 필드 추가 |
| `cron/scripts/run_apply.py` | `additional_sources` 도 yml 에 적재 |
| `cron/templates/pr-body.md` | `<details>` 섹션 추가 (sub-agent results, empty pages, suspicious, aggregator stats) |

### 5.3 폐기

| 경로 | 사유 |
|---|---|
| `cron/scripts/fetch.py` 의 `fetch_category` 단일 URL 모드 | nav_fetch 의 page-level fetch 로 대체 |
| `cron/scripts/run_fetch.py` | Job 1 (run_nav_fetch) 으로 대체 |
| `cron/scripts/run_diff.py` | Aggregator 안으로 흡수 (기존 refs vs 새 records 비교) |
| `cron/scripts/run_category_discovery.py` | docsConfig nav diff 로 자연 byproduct, 별도 step 불필요 |
| `cron/scripts/category_discovery.py` 의 sitemap 파싱 | mintlify nav 가 sitemap 보다 풍부 |

## 6. 데이터 schema

### 6.1 nav.json (Job 1 출력)

```json
{
  "fetched_at": "2026-05-02T...",
  "source": "https://code.claude.com/docs/en/skills",
  "tabs": [
    {
      "tab": "Build with Claude Code",
      "groups": [
        {
          "group": "Agents",
          "pages": ["en/sub-agents", "en/agent-teams"]
        },
        {
          "group": "Automation",
          "pages": ["en/hooks-guide", "en/channels", "en/scheduled-tasks", "en/headless"]
        }
      ]
    },
    {
      "tab": "Reference",
      "groups": [
        {
          "group": "Reference",
          "pages": ["en/cli-reference", "en/commands", "en/hooks", "en/plugins-reference", ...]
        }
      ]
    }
  ],
  "excluded_tabs": ["Agent SDK", "What's New", "Resources", "Getting started", "Administration"]
}
```

### 6.2 group-result-<slug>.json (Job 2 출력)

```json
{
  "tab": "Build with Claude Code",
  "group": "Automation",
  "status": "ok",
  "records": [
    {
      "id": "hook-input-via-stdin",
      "type": "qualitative",
      "proposition": "Command hooks read input from stdin as JSON",
      "verifier": {
        "kind": "llm-judge",
        "rubric": "..."
      },
      "source": {
        "url": "https://code.claude.com/docs/en/hooks-guide",
        "fetched_at": "2026-05-02T...",
        "quote": "For command hooks, input arrives on stdin as JSON..."
      },
      "severity": "critical",
      "category_hint": "hooks",
      "page": "en/hooks-guide"
    }
  ],
  "empty_pages": [
    {
      "page": "en/scheduled-tasks",
      "reason": "high-level guide, no verifiable schema",
      "suspicious": false
    }
  ],
  "errors": []
}
```

### 6.3 plan.json (Aggregator 출력 = U3.5 입력)

```json
[
  {
    "category": "hooks",
    "action": "ADD",
    "item_id": "hook-input-via-stdin",
    "payload": {
      "id": "hook-input-via-stdin",
      "type": "qualitative",
      "proposition": "...",
      "verifier": {...},
      "source": {
        "url": "...hooks.md",
        "quote": "Command hooks receive input via stdin",
        "fetched_at": "..."
      },
      "additional_sources": [
        {
          "url": "...hooks-guide.md",
          "quote": "For command hooks, input arrives on stdin as JSON..."
        }
      ],
      "severity": "critical",
      "category": "hooks"
    }
  }
]
```

### 6.4 criteria-mapping.yml (새 형식)

```yaml
# 카테고리 binding rules — page list 를 직접 박지 않고 tab/group 룰로 자동 binding
# nav.json 의 page 가 매칭되면 해당 cchelp 카테고리 yml 로 적재

categories:
  - name: skills
    bind:
      - tab: "Build with Claude Code"
        group: "Tools and plugins"
        page_filter: "skills"          # 정확 매칭 또는 glob
    review_file: skills/review/references/skills.yml
    template_file: skills/generate/references/skill-template.md
    benchmark: true

  - name: subagents
    bind:
      - tab: "Build with Claude Code"
        group: "Agents"
        # filter 없음 → group 의 모든 page
    review_file: skills/review/references/subagents.yml
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

  - name: mcp
    bind:
      - tab: "Build with Claude Code"
        group: "Tools and plugins"
        page_filter: "mcp"
    review_file: skills/review/references/mcp.yml

  # ... (memory, claude-md, commands, settings, permissions, plugins)

excluded_tabs:
  - "Agent SDK"
  - "What's New"
  - "Resources"
  - "Getting started"
  - "Administration"

priority:
  tabs:
    - "Reference"
    - "Configuration"
    - "Administration"
    - "Build with Claude Code"
```

## 7. Sub-agent prompt template

`cron/templates/group-prompt.md` (각 matrix job 의 prompt 통일):

```markdown
너는 cchelp cron pipeline 의 group-plan sub-agent.
너의 작업 단위 = 단일 group ([${tab}] 의 [${group}]).

## STEP 0 — Schema 강제 (필수)

`cron/schema/item.schema.json` 을 Read 하라. 모든 record payload 는 이 schema 를 통과해야 한다.

핵심 enum:
- verifier.kind: regex | line-count | file-exists | substring | yaml-parse | json-schema | shell | llm-judge
- severity: critical | important | suggestion
- type: programmatic | qualitative

`cron/schema/group-result.schema.json` 도 Read 하라. 너의 출력 (group-result-<slug>.json) 은 이 schema 를 통과해야 한다.

## STEP 1 — 입력 확인

artifact: docs-fetched/
  - fetched/${page1}.md
  - fetched/${page2}.md
  - ...

mapping rules (binding):
  ${mapping_yaml_for_this_group}

cchelp 카테고리 list (LLM fallback hint 용):
  [skills, subagents, hooks, mcp, commands, memory, claude-md, settings, permissions, plugins]

## STEP 2 — Page 별 records 추출

각 page 에서:
1. frontmatter table / schema row / 명시적 수치 한도 등 검증 가능한 사실 추출
2. quote 는 fetched body 의 verbatim substring (≥5자)
3. category_hint 결정:
   - mapping rules 의 binding 매칭 → 그 카테고리 사용
   - 매칭 없음 → cchelp 카테고리 list 중 가장 적합한 것 LLM 선택
   - 적합한 것 없음 → "discovered:<page-slug>" 사용

## STEP 3 — 빈 결과 처리

records 0 인 page 는 empty_pages[] 에 reason 명시:
- "high-level guide, no verifiable schema" (정상)
- "patterns_found: ['frontmatter_table'], could not extract" + suspicious=true (의심)

## STEP 4 — 자체 schema 검증 후 출력

`group-result-${slug_safe(group_name)}.json` 으로 저장.

bash 로 사전 검증:
\`\`\`bash
cd cron && PYTHONPATH=. .venv/bin/python -m scripts.validate_group_result \
  --file ${RUN_DIR}/group-results/group-result-<slug>.json
\`\`\`

실패 시 record 수정 후 재시도. 통과 시 종료.

## 절대 하지 말 것
- 다른 group 의 결과 참조 (격리)
- mapping rules / cchelp 카테고리 list 외 카테고리 hint 사용
- quote paraphrase / 환각
- empty_pages reason 누락
```

## 8. 워크플로 변경 (yml)

```yaml
name: Update Review Criteria

on:
  schedule:
    - cron: '0 17 * * 6'
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
      - uses: actions/setup-python@v5
        with: { python-version: '3.11' }
      - working-directory: cron
        run: |
          python -m venv .venv && .venv/bin/pip install -e ".[dev]"
      - name: Job 1 — nav-fetch + page-fetch
        id: extract
        working-directory: cron
        run: |
          PYTHONPATH=. .venv/bin/python -m scripts.run_nav_fetch \
            --mapping ../.github/criteria-mapping.yml \
            --out-nav ${{ env.RUN_DIR }}/nav.json \
            --out-fetched ${{ env.RUN_DIR }}/fetched
          # matrix 용 groups 추출
          groups=$(jq -c '[.tabs[] | .groups[] | {tab: ..., group: ..., pages: ...}]' \
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
      - uses: actions/download-artifact@v4
        with: { name: docs-fetched, path: ${{ env.RUN_DIR }} }
      - uses: anthropics/claude-code-action@v1
        with:
          claude_code_oauth_token: ${{ secrets.CLAUDE_CODE_OAUTH_TOKEN }}
          claude_args: --permission-mode bypassPermissions
          prompt: |
            ${{ env.RUN_DIR }}/fetched/ 안의 page 들을 분석.
            너의 group: ${{ matrix.group.tab }} > ${{ matrix.group.group }}
            너의 pages: ${{ toJson(matrix.group.pages) }}
            
            cron/templates/group-prompt.md 를 Read 하고 정확히 따른다.
            출력: ${{ env.RUN_DIR }}/group-results/group-result-${slug}.json
          allowed_tools: "Bash,Read,Write"
      - uses: actions/upload-artifact@v4
        with:
          name: group-result-${{ strategy.job-index }}
          path: ${{ env.RUN_DIR }}/group-results/
          retention-days: 14

  aggregate:
    needs: group-plan
    if: always()
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with: { python-version: '3.11' }
      - working-directory: cron
        run: python -m venv .venv && .venv/bin/pip install -e ".[dev]"
      - uses: actions/download-artifact@v4
        with:
          pattern: group-result-*
          merge-multiple: true
          path: ${{ env.RUN_DIR }}/group-results
      - working-directory: cron
        run: |
          PYTHONPATH=. .venv/bin/python -m scripts.run_aggregate \
            --group-results-dir ${{ env.RUN_DIR }}/group-results \
            --mapping ../.github/criteria-mapping.yml \
            --out ${{ env.RUN_DIR }}/plan.json
      - uses: actions/upload-artifact@v4
        with: { name: plan, path: ${{ env.RUN_DIR }}/plan.json }

  # 이하 기존 jobs (U3.5 / U4 / U5 / signals / save-state / labels / U6 / U7) — 변경 없음
  # 단 input artifact 가 'plan' (Job 3 출력) 으로 바뀜
  ...
```

## 9. 부분 실패 / 가용성

| 상황 | 처리 |
|---|---|
| nav-fetch fail | hard abort + GitHub issue |
| 1개 group sub-agent fail | `fail-fast: false` 로 다른 group 진행, aggregate 가 빈 group 인지 |
| 모든 sub-agent fail | aggregate 가 plan.json 빈 list → U3.5 가 0 record 처리 → PR 만들어지지만 변경 없음 |
| aggregate fail | hard abort + GitHub issue |
| 부분 records 만 dedup 충돌 | priority 룰 + sources merge 로 자동 해결 |

## 10. PR body template (10번 결정 반영)

`cron/templates/pr-body.md` 갱신:

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
| Signal | Value |
|---|---|
| B (regressions) | {B_SIGNAL} |
| C (ratio drop) | {C_SIGNAL} |

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

## 11. 본 스펙 범위 외 (Phase 2 후보)

- Sub-agent 가 docs frontmatter 의 `tab`/`group` 메타도 추출해서 nav 와 cross-check (현재는 nav.json 만 신뢰)
- group 결과의 confidence score (verifier kind 정밀도 / quote 길이 등) 기반 자동 우선순위 보정
- LLM 자율 분류 fallback 의 feedback loop (메인테이너가 잘못 분류 수정하면 mapping rules 자동 갱신 제안)
- description 최적화 후속 step (skill-creator 의 improve_description 차용)
- HTML 시각화 (skill-creator 의 eval-viewer 차용)
- whats-new weekly digest 인덱싱 (현재는 통째 제외)

## 12. 리스크

1. **Mintlify hydrate 형식 변경.** `__next_f.push` 추출은 reverse-engineering. 형식 바뀌면 hard fail. 메인테이너가 nav_fetch.py 의 정규식 / parsing 로직 수정 필요. 메모리에 fallback path (sitemap 으로 degraded mode) 가능하지만 본 phase 에서는 hard fail 로 단순화.

2. **병렬 sub-agent 비용.** Group ~15개 × 평균 LLM inference ~3분 → wall-clock 3분, 토큰 비용 ~15× 단일 LLM 호출. 일요일 02:00 KST off-peak 에 도는 한 acceptable, 단 카테고리 / group 수 늘면 모니터링 필요.

3. **GitHub Actions concurrent 한계.** Free tier 20 → 우리 ~15 안전. 단 Anthropic 의 docs 확장으로 group 25+ 되면 큐잉 발생, max-parallel 조정 필요.

4. **category_hint LLM fallback 오류.** mapping rules 매칭 안 되는 page 에서 LLM 이 잘못된 카테고리 hint 박을 수 있음. Plan Review (U3.5) 의 quote 검증으로 일부 잡힘. 빈번하면 mapping rules 보강 필요.

5. **Aggregator dedup 룰 오버랩.** 같은 사실이 미세히 다른 proposition 으로 추출되어 같은 id 안 잡힘 → cross-reference 깨짐. id 작성 가이드 (sub-agent prompt 의 STEP 2) 강화로 완화.

## 13. 성공 기준

- 4 연속 cron 실행 후:
  - 모든 group 의 sub-agent 결과 수집됨 (`fail-fast: false` 로 부분 실패 허용 하더라도)
  - Aggregator 가 plan.json 정상 출력
  - U3.5 의 schema/quote 검증 통과율 ≥ 80% (현재 ~23%, 옛 prompt 기준)
  - PR 의 `<details>` 섹션 모두 채워짐 (sub-agent results / empty pages / aggregator stats)
- 새 docs 페이지가 추가되면 다음 cron 에 자동 발견 (메인테이너의 mapping yml 수정 0)
- Mintlify hydrate 추출 실패는 GitHub issue 로 즉시 가시화
