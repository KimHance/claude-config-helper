# 판단 기준 파이프라인 재설계 — 디자인 스펙

**작성일:** 2026-04-29
**작성자:** KimHance (cchelp 메인테이너)
**상태:** Draft
**범위:** cchelp 의 리뷰 판단 항목 작성 / 검증 / 자기개선 파이프라인 전면 재구축.

---

## 1. 목표

cchelp 의 자동 판단 기준 갱신 파이프라인을 **자체 면역 시스템 (self-improving immune system)** 으로 재구축한다:

1. 판단 항목의 출처를 Claude Code 공식 docs 와 changelog 로만 한정 (모델 사전지식 reject).
2. 완전 자동 운영 (메인테이너의 주간 사이클 개입 0).
3. 판단 항목뿐 아니라 cchelp 자기 자신의 리뷰 행동 (reviewer agent prompt, 오케스트레이션 내용) 도 시간이 지나며 진화.
4. PR #2 의 구조적 결함 종식 (출처 위조, 자기 채점 함정, prose 를 체크리스트로 위장, drift, 좀비 항목).

외부 사용자는 메인테이너가 손대지 않아도 매주 더 정확해지는 review/generate 결과물을 받는다.

## 2. Non-Goals (이번 스펙 범위 밖)

- **Layer 4 (업데이트 워크플로 자체) 의 진화.** 봇은 `.github/workflows/update-review-criteria.yml` 을 수정하지 않는다. 메인테이너가 플러그인이 이상하다고 느끼거나 일관되지 않다고 느낄 때만 직접 수정.
- **Review 9-step 골격의 구조 변경.** `/review` 의 9-step (Scan → Categorize → Load Criteria → Evaluate → Cross-validate → Benchmark → Grade → Report → Post-review) 은 안정 골격, 메인테이너만 구조 변경. 봇은 각 step 의 *내용* 만 진화.
- **기존 references checklist 마이그레이션.** 현재 `skills/review/references/*-checklist.md` 는 오염된 것으로 간주, 폐기 후 빈 캔버스에서 재시작.
- **기존 generate templates 의 전면 폐기.** `skills/generate/references/*-template.md` 는 재사용 가능한 부분이 있어 통째 폐기는 안 함. 봇이 새 references 와 일관되게 만들기 위해 부분 수정만.

## 3. 핵심 결정사항 (브레인스토밍 결과)

| # | 영역 | 결정 |
|---|---|---|
| 1 | 출처 정책 | docs + changelog 둘 다 1차 출처. 모델 사전지식 reject. 누락은 다음 cron 에서 catch-up. |
| 2 | 운영 모델 | 완전 자동화 (메인테이너 개입 0). |
| 3 | 마이그레이션 | references checklists 는 폐기 후 새로 작성. templates 는 재사용 가능 부분 유지하며 보정. |
| 4 | 봇 권한 범위 | Layer 1 (refs) + Layer 2 (agents) + Layer 3 (orchestration 내용). Layer 4 는 메인테이너 영역. |
| 5 | Review 9-step | 안정 골격, 메인테이너 영역. |
| 6 | Update workflow | 8-step: Fetch → Diff → Plan → **Plan Review (독립 subagent)** → Apply → Self-validate → Commit & PR → Auto-merge. |
| 7 | 항목 형식 | Hybrid: 항목마다 `type: programmatic | qualitative` 명시. |
| 8 | Plan Review 검증 | Source 무결성 + Schema + Verifier 실행성 + 의미 정합성 (quote-based reasoning 필수). |
| 9 | Diff 처리 | ADD/UPDATE/REMOVE 모두 즉시. REMOVE 는 fallback 검색 후 결정. |
| 10 | Fallback 검색 | same-domain sitemap (`llms.txt`) → cross-language → changelog deprecate 언급 → 못 찾으면 삭제. |
| 11 | 카테고리 자동 발견 | 휴리스틱 (frontmatter/schema 페이지만) + PR 라벨 `category-discovery`. |
| 12 | Generate templates | references 와 templates 둘 다 자동 갱신, 동일 PR 에 atomic 머지. |
| 13 | Layer 2/3 진화 트리거 | A (mandatory propagation) + B (self-review 회귀, 위임) + C (benchmark delta drop, 정규화). |
| 14 | B 신호 처리 | 별도 `self-eval-runner` thin-executor agent. snapshot/versioning 안 함. |
| 15 | C 신호 처리 | 매 cron 마다 with-skill 과 baseline 동시 측정 + delta 를 비율 해석. |

## 4. 아키텍처

### 4.1 레이어 모델

```
Layer 1 — 판단 항목 (refs)
  skills/review/references/<category>.yml   (NEW: yml schema)
  봇: 읽기/쓰기              메인테이너: 읽기/쓰기

Layer 1.5 — 생성 템플릿 (refs 와 atomic 갱신)
  skills/generate/references/<category>-template.md  (기존 재사용 + 보정)
  봇: 읽기/쓰기              메인테이너: 읽기/쓰기

Layer 2 — Agents (review-time 행동)
  agents/reviewer.md         (기존, Layer 2 진화 대상)
  agents/self-eval-runner.md (신규 — thin executor)
  agents/grader.md
  agents/eval-runner.md
  봇: 읽기/쓰기 (U3 plan, U3.5 게이트 통과 후)
  메인테이너: 읽기/쓰기

Layer 3 — Orchestration 내용 (skill 본체, step 내용)
  skills/review/SKILL.md     (step 의 내용. 9-step 구조 X)
  skills/generate/SKILL.md
  봇: 읽기/쓰기 (게이트 통과 후)
  메인테이너: 읽기/쓰기

Layer 4 — Update workflow 자체
  .github/workflows/update-review-criteria.yml
  봇: 접근 불가              메인테이너 전용
```

### 4.2 두 reviewer agent 동시 운영 (자기참조 차단의 핵심)

```
reviewer (agent)
  - 외부 사용자의 /review, /generate 호출에 사용
  - Layer 2 진화 대상 — 봇이 prompt 재작성 가능
  - 풍부한 행동: cross-validation, qualitative judgment, 보고서 정리

self-eval-runner (agent)         ← 신규
  - 매주 self-review 패스에서만 사용
  - Thin executor: 각 ref 항목의 verifier 를 기계적으로 실행
  - programmatic 항목 → regex/parse/count 그대로, LLM 판단 X
  - qualitative 항목 → llm-judge + rubric + quote substring 확인만
  - Prompt 거의 정적 (지능이 refs 에 있지 agent 에 없음 → 봇이 자기 통과 보장하도록 진화시킬 동기 자체가 없음)
```

**왜 두 agent:** 같은 세션·같은 agent 가 self-review 하면 PR #2 의 함정 (채점자 = 작성자 = 자기 갱신자 → 자기 통과 보장 루프) 에 정확히 빠짐. 역할을 구조적으로 분리하면 차단됨. self-eval-runner 가 thin 이라 두 agent 가 따로 진화해서 drift 날 위험도 적음 (진화할 게 거의 없으니).

### 4.3 데이터 출처 매핑

2026-04-29 시점 모두 라이브 검증 완료:

| cchelp 카테고리 | docs URL |
|---|---|
| CLAUDE.md | https://code.claude.com/docs/en/memory |
| Memory | https://code.claude.com/docs/en/memory |
| Skills | https://code.claude.com/docs/en/skills |
| Subagents | https://code.claude.com/docs/en/sub-agents |
| Commands | https://code.claude.com/docs/en/commands |
| Hooks | https://code.claude.com/docs/en/hooks |
| MCP | https://code.claude.com/docs/en/mcp |
| Settings | https://code.claude.com/docs/en/settings |
| Permissions | https://code.claude.com/docs/en/permissions |
| Plugins | https://code.claude.com/docs/en/plugins |
| Changelog | https://code.claude.com/docs/en/changelog |

Sitemap (fallback 검색 대상): https://code.claude.com/docs/llms.txt

`criteria-mapping.yml` 은 자동 발견 카테고리 허용하도록 재구조화. 메인테이너 큐레이팅 매핑은 보존. 봇이 발견한 매핑은 `discovered: true` 표기 + PR 라벨 `category-discovery`.

## 5. 항목 Schema (Layer 1)

`skills/review/references/<category>.yml` 에 저장. 카테고리당 YAML 1 파일, 항목 list.

### 5.1 공통 필수 필드

```yaml
- id: kebab-case-unique-id          # 카테고리 내 globally unique
  type: programmatic | qualitative
  proposition: <한 문장 명제>         # 검사 대상에 대해 무엇을 주장하는가
  source:
    url: <docs URL, #anchor 가능 시 포함>
    fetched_at: <ISO 8601 timestamp>
    quote: <fetched docs 본문의 정확한 substring>
  severity: critical | important | suggestion
  category: <7+ 카테고리 중 하나>
```

### 5.2 Programmatic Verifier

```yaml
  verifier:
    kind: regex | yaml-parse | json-schema | file-exists | line-count | substring | shell
    spec: <kind 별 spec>
```

예시:

```yaml
- id: skill-name-charset
  type: programmatic
  proposition: "name 필드가 lowercase + 숫자 + 하이픈 패턴이며 길이 64 이하"
  verifier:
    kind: regex
    pattern: "^[a-z0-9-]+$"
    max_length: 64
  source:
    url: "https://code.claude.com/docs/en/skills#frontmatter-reference"
    fetched_at: "2026-04-29T02:00:00Z"
    quote: "Lowercase letters, numbers, and hyphens only (max 64 characters)"
  severity: critical
  category: skills

- id: skill-md-line-budget
  type: programmatic
  proposition: "SKILL.md 가 500 라인 이하"
  verifier:
    kind: line-count
    target: SKILL.md
    max: 500
  source:
    url: "https://code.claude.com/docs/en/skills#add-supporting-files"
    fetched_at: "2026-04-29T02:00:00Z"
    quote: "Keep SKILL.md under 500 lines"
  severity: suggestion
  category: skills
```

### 5.3 Qualitative Verifier

```yaml
  verifier:
    kind: llm-judge
    rubric: <자연어 pass/fail 기준>
```

예시:

```yaml
- id: skill-description-explains-when
  type: qualitative
  proposition: "description 이 WHEN (사용 시점) 을 설명하지 단순 WHAT 이 아님"
  verifier:
    kind: llm-judge
    rubric: |
      Pass: description 에 시점/트리거 어휘 포함 ("Use when...", "for tasks where...", 트리거 구문) 또는 호출 컨텍스트 예시 포함.
      Fail: skill 의 기능만 묘사 (예: "Reviews code"), 활성화 조건 표시 없음.
  source:
    url: "https://code.claude.com/docs/en/skills#frontmatter-reference"
    fetched_at: "2026-04-29T02:00:00Z"
    quote: "What the skill does and when to use it. Claude uses this to decide when to apply the skill."
  severity: important
  category: skills
```

### 5.4 Schema 제약 (U3.5 Plan Review 가 강제)

- `source.quote` 는 `source.url` fetched body 의 substring 이어야 함.
- `source.fetched_at` 은 현재 cron 실행 시점 ±1시간 이내.
- `id` 는 카테고리 내 unique.
- `type` 이 verifier 필수 필드 결정 (잉여 필드 금지).
- 모호한 항목 (programmatic / qualitative 둘 다 가능): 둘로 쪼개거나 programmatic 우선 채택, qualitative drop.
- **휴리스틱 항목 (docs 출처 없음) 은 reject.** 봇은 "common anti-pattern" prose 를 만들 수 없음.

## 6. 업데이트 워크플로 (8-Step)

매주 cron (일요일 02:00 KST) 에서 실행. 한 GitHub Actions job 안에 처리.

### U1. Fetch
- 각 1차 docs URL + sitemap (`llms.txt`) + changelog 를 WebFetch.
- raw body 를 `/tmp/cchelp-cron-<run-id>/fetched/<category>.md` 에 저장.
- 파일별 `fetched_at` ISO timestamp 기록.
- sitemap 을 직전 cron 의 스냅샷 (`.cron-state/sitemap.snapshot.txt`) 과 비교 → 새 페이지 = 카테고리 발견 후보.

### U2. Diff
- 카테고리별, 새 body vs 직전 cron 의 항목들이 참조하던 body (`.cron-state/<category>.body.snapshot.txt`) diff.
- 현재 `references/<category>.yml` 항목 분류:
  - **STABLE**: `source.quote` 가 새 body 에 substring → no change.
  - **UPDATE 후보**: quote 매칭 안 되지만 근사 표현 존재.
  - **REMOVE 후보**: quote 매칭 안 되고 근사 표현도 없음.
- ADD 후보 식별: 새 body 의 frontmatter 표 / schema row / behavior callout 에서 새 사실 추출.

### U3. Plan
diff 결과별로 변경 record 작성:
- ADD record (새 항목 full schema, 방금 fetch 한 body 의 quote 포함).
- UPDATE record (기존 항목의 quote / proposition / verifier 갱신).
- REMOVE record (삭제 대상, source URL 은 fallback 검색 큐로).
- Layer 2/3 propagation record (verifier.kind enum 또는 schema 필드 변경 시 agent prompt 의 mandatory 갱신).
- 카테고리 발견 record (새 `references/<category>.yml`, `discovered: true` 표기).

REMOVE 후보 fallback 처리는 여기서:
1. `source.url` HEAD 요청.
2. 200 + body 에 quote 없음 → 삭제 확정.
3. 404 / redirect → `llms.txt` 에서 인접 slug 검색 + cross-language 시도 (`/en/` ↔ `/ko/`) + changelog 의 deprecate 언급 검색.
4. 발견 → UPDATE 로 재작성 (새 url + 동일 proposition).
5. 못 찾음 → REMOVE 유지.

Plan 출력: 모든 record 의 full 제안 schema 를 담은 단일 `plan.json`.

### U3.5. Plan Review (독립 Subagent)
fresh `general-purpose` subagent 디스패치 (컨텍스트 공유 X), `plan.json` + fetched bodies 전달. 4단계 검증:

1. **Source 무결성** (programmatic, 결정론적):
   - 각 `source.url` HEAD 요청 → 200 필수.
   - 각 `source.quote` 가 fetched body 에 substring 매칭 필수.
   - `source.fetched_at` 이 현재 cron window 내인지 확인.

2. **Schema 유효성** (programmatic):
   - type 별 필수 필드 모두 존재.
   - `id` 카테고리 내 unique.
   - `severity`, `category` 가 valid enum.

3. **Verifier 실행성** (programmatic):
   - regex: 패턴 컴파일, 실패 시 reject.
   - yaml-parse / json-schema: schema 문법 유효.
   - line-count / file-exists / substring: target 명 well-formed.
   - llm-judge: rubric 비어있지 않음, ≥ 30자.

4. **의미 정합성** (qualitative, quote-based reasoning 강제):
   - reviewer 가 승인하는 모든 항목에 대해, fetched body 에서 verbatim quote 를 인용한 한 줄 정당화 생성 필수.
   - 그 정당화의 quote 가 fetched body 에 substring 매칭 안 되면 승인 무효.
   - 환각 / 의미 표류 / 기존 항목과 중복 차단.

Plan Review 실패 모드:
- 검증 1~3 중 하나 fail → 해당 record 만 reject, 나머지는 진행.
- 검증 4 fail → 해당 record reject.
- 전체 record 의 50% 이상 fail → cron 전체 abort, PR 라벨 `plan-review-aborted`, 머지 차단.

### U4. Apply
- `references/<category>.yml` 수정 (Plan Review 통과한 record 의 add/update/remove).
- `templates/<category>-template.md` 도 refs 와 atomic 갱신 (결정 12, B 옵션).
  - 기존 templates 에서 재사용 가능한 부분은 유지, refs 의 새 필드/제약만 반영.
- Layer 2/3 propagation:
  - 새 `verifier.kind` enum 등장 시 reviewer / grader prompt 에 해석 가이드 추가.
  - self-eval-runner prompt 는 refs schema 의 enum 집합이 바뀔 때만 갱신 (드물게).
- 카테고리 발견: 발견된 docs 페이지에서 새 `references/<category>.yml` 작성.

### U5. Self-validate
- Plan Review 검증 1~3 을 실제 diff (plan 이 아니라) 에 재실행 — U4 구현 버그 최종 가드.
- cchelp 자기 자신에 대해 smoke `/review` 실행, **`self-eval-runner` 사용** (reviewer X).
- 수집:
  - 카테고리별 pass rate.
  - C-signal: with-skill 과 baseline 동시 측정, delta 를 비율로 계산 (`(with - baseline) / baseline × 100%`).
  - B-signal: 직전엔 통과했는데 이번 smoke run 에서 fail 한 refs 항목 list.
- Layer 2/3 deeper change 결정 룰:
  - B-signal 회귀 존재 → Layer 2/3 follow-up record 큐 → U3 → U3.5 → U4 → U5 사이클 1회 더 (최대 3회).
  - C-signal 비율이 직전 cron 대비 절대값 20% 이상 떨어짐 → 동일.
  - 3회 후에도 fail → PR 라벨 `self-improve-blocked`, 머지 차단.

### U6. Commit & PR
- 모든 파일 변경 (`references/*.yml`, `templates/*.md`, `agents/*.md` propagation 시, `.cron-state/*` 스냅샷) 한 브랜치에.
- PR body 필수 포함:
  - 변경된 카테고리 list.
  - 변경 record 별 `id`, action (ADD/UPDATE/REMOVE), `source.url`, `source.quote`.
  - Plan Review 요약 (통과 / reject 카운트).
  - Self-validate 요약 (B / C signal raw 수치).
  - 카테고리 발견 시 sitemap diff.
- 라벨:
  - `automated` (항상)
  - `criteria-update` (항상)
  - `category-discovery` (새 카테고리 발견 시)
  - `plan-review-aborted` / `self-improve-blocked` (해당 시, 머지 차단)

### U7. Auto-merge
- auto-merge 조건:
  - Plan Review 가 모든 record 통과 또는 부분 통과 수용.
  - Self-validate 의 B-signal 회귀 없음 AND C-signal 비율 20% 이상 안 떨어짐.
  - 차단 라벨 없음.
- 미충족 시 PR 그대로 열어두고 메인테이너 주의 대기. 봇은 자체적으로 더 escalate 하지 않음.

## 7. 자기개선 신호 파이프라인 (Layer 2/3 트리거)

| 트리거 | 출처 | 같은 세션에서? | 안전장치 |
|---|---|---|---|
| **A — Mandatory propagation** | refs 의 schema enum 변경 | Yes (refs 변경과 항상 동반) | 불필요, 결정론적 |
| **B — Self-review 회귀** | `self-eval-runner` 가 직전 통과 항목에 fail | **No** — 별도 subagent (`self-eval-runner`, `reviewer` 아님) | thin executor 설계로 자기 통과 보장 동기 자체 차단 |
| **C — Benchmark delta drop** | with-skill 비율이 baseline 대비 절대 20% 이상 하락 | Yes, 단 동시 측정 + 비율 정규화 | 동일 모델로 동시 측정, 비율이 모델 변동 흡수 |

A 는 항상 발동. B 와 C 는 조건부. 둘 다 U4 의 fresh refs 가 있어야 작동하므로, 한 cron 안의 순서:

```
U1 → U2 → U3 → U3.5 → U4 (refs + templates + propagation) → U5 (B/C 측정) →
[B 또는 C 발동 시] U3' → U3.5' → U4' → U5' (Layer 2/3 deeper change 반복, ≤3회) →
U6 → U7
```

## 8. 본 스펙 범위 외

- **빈 캔버스 초기 seed 항목 작성.** 메인테이너가 카테고리당 최초 ~10–20 항목을 직접 bootstrap, 그 후 봇 인계. seeding 은 별도 task (수동 spec, 봇 작업 X).
- **GitHub Actions 워크플로 파일 재작성.** 본 spec 은 워크플로의 동작을 논리적으로 정의. 실제 YAML 편집은 implementation plan 단계.
- **기존 `docs/claude-config-review-report.md` 히스토리 마이그레이션.** 기존 보고서 그대로, 새 보고서부터 새 schema.
- **`reviewer` / `grader` / `eval-runner` 의 prompt 재작성.** 본 spec 은 신규 `self-eval-runner` 정의만. 기존 agent prompt 편집은 implementation plan 에서.
- **Phase 2: 단일 출처 모델 (브레인스토밍 결정 12 의 옵션 C).** templates 별도 파일 유지. C-style 동적 합성은 추후.
- **Templates atomic propagation 와 Layer 2/3 agent propagation 의 실 구현.** 본 phase 1 은 refs (YAML schema 항목) 자동 갱신만 구현. 결정 12 (templates atomic), 결정 13 의 A (mandatory propagation) 의 실제 코드 generation 은 별도 sub-spec 으로 분리. 인자/구조는 미리 자리 잡혀 있으니 phase 2 에서 채우면 됨.

## 9. 리스크 및 미해결 사항

1. **비용.** B+C 동시 측정으로 cron 당 eval 비용 2배. 일요일 02:00 KST 로 off-peak 라 OK 이지만 카테고리가 15개+ 로 늘면 토큰 폭주 모니터링 필요. 완화: 카테고리별 샘플링.

2. **Plan Review reviewer 환각.** U3.5 의 reviewer 도 LLM. quote substring 매칭이 결정론적 backstop 이지만, 검증 4 (의미 정합성) 의 "근사 표현" 판단은 reviewer 의견에 의존. 완화: Plan Review 의 record 별 결정을 PR body 에 로깅, 사후 audit 가능.

3. **Sitemap drift.** `llms.txt` 자체가 사라지거나 재구조화되면 fallback 깨짐. 완화: fallback 체인 마지막에 changelog. 모두 실패 시 `deprecated: pending` 으로 한 cron 더 보존 후 삭제.

4. **빠른 docs 변경.** 한 주 안에 추가됐다 사라지면 봇이 연속 cron 에 추가 후 삭제 — 좀비 없음. 허용 churn.

5. **Layer 4 drift.** 본 spec 은 메인테이너가 봇 행동을 보고 가끔 `update-review-criteria.yml` 을 튜닝한다고 가정. 봇은 Layer 4 자체에 피드백 메커니즘 없음. 결정 4 에 따라 수용.

## 10. 성공 기준

- 4 연속 cron 이후:
  - `references/*.yml` 의 모든 항목이 valid `source.quote` 보유, 라이브 docs body 에 substring 매칭.
  - `source: heuristic` 항목 0.
  - Self-review 의 pass rate 안정 (사이클간 저하 없음).
  - C-signal 비율이 1차 cron baseline 대비 ±10% 내 유지 (skill 품질 drift 없음).
- 메인테이너가 임의의 PR 을 열어 모든 추가/변경 항목을 docs URL + verbatim quote 로 30초 이내 추적 가능.
- `code.claude.com/docs/` 에 새 카테고리 페이지 추가 시, 1 cron 안에 자동 발견되고 통합. 메인테이너 손 안 댐.
