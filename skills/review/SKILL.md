---
name: review
description: Use when reviewing or auditing Claude Code configuration files for quality. Evaluates CLAUDE.md, memory, skills, agents, commands, hooks, and MCP against best-practice checklists with optional parallel benchmark eval.
---

# Claude Config Review

Evaluation criteria for reviewing Claude Code configuration files in the user's current project. 평가 기준표는 플러그인이 내부적으로 관리하며 공식 Claude Code 문서와 동기화된다 (구현 디테일).

**작동 원칙:** 리뷰 대상은 항상 사용자 cwd 의 파일들이다. 플러그인 디렉토리는 리뷰 대상이 아니라 평가 기준표의 저장소일 뿐이다.

## Modes

- **Total** (`/review`): Scan all 7 categories in user cwd, benchmark all discovered skills/agents
- **Target** (`/review <path>`): Review and benchmark only the specified path in user cwd

> 리뷰 대상은 7 카테고리 전체. 벤치마크 가능한 카테고리는 그중 Skills/Subagents 둘뿐이다 — 다른 카테고리는 정적 평가만.

## Workflow

1. **Scan** — Total: user cwd 에서 7 카테고리 전체 탐색. Target: 지정 경로만.
2. **Categorize** — 발견된 파일을 7 카테고리 중 어디에 속하는지 판정. 미발견 카테고리는 N/A 행을 유지하면서 표시.
3. **Evaluate** — 각 카테고리의 평가 기준을 내부 저장소에서 로드해 cwd 의 대상 파일을 네 섹션 (Fundamentals / Advanced / Recommended / Anti-patterns) 별로 검토. 항목당 pass/warn/fail.
4. **Cross-validate** — cwd 내부의 파일 간 참조 정합성 검사.
5. **Benchmark** — Skills 와 Subagents 에 한해 `eval-runner` × 2 + `grader` 로 객관 측정. agent-spawn 불가 환경이면 N/A.
6. **Grade** — 카테고리별 A/B/C/D/F. 평가 기준 준수도 + 벤치마크 결과 종합.
7. **Report** — 터미널 요약 표 + `docs/claude-config-review-report.md` 상세 보고서 (사용자 cwd 에 작성).

## Categories

| # | Category  | Files to Check (cwd 기준)                              |
|---|-----------|--------------------------------------------------------|
| 1 | CLAUDE.md | `CLAUDE.md`, `**/CLAUDE.md`                            |
| 2 | Memory    | `.claude/memory/**`, `~/.claude/projects/*/memory/**`  |
| 3 | Skills    | `skills/**/SKILL.md`, `.claude/skills/**/SKILL.md`     |
| 4 | Subagents | `agents/*.md`, `.claude/agents/*.md`                   |
| 5 | Commands  | `commands/*.md`, `.claude/commands/*.md`               |
| 6 | Hooks     | `hooks/hooks.json`, `.claude/hooks.json`               |
| 7 | MCP       | `.mcp.json`                                            |

> 각 카테고리의 평가 기준은 플러그인 내부에서 자동 로드된다. 사용자가 평가 기준 파일 위치를 알 필요는 없다.
> 추가로 permissions/plugins/settings 도 cross-validation 단계에서 cross-cutting 룰로 활용됨 (별도 카테고리는 아님).

## Cross-Validation Checks

After category reviews, verify:
- CLAUDE.md references to skills/agents actually exist
- Memory file references point to valid paths
- No orphaned agents/skills (defined but never discoverable)

## Benchmark Eval (Skills & Subagents)

When reviewing Skills or Subagents, run a parallel benchmark to measure quality objectively.

- **Full eval process**: `references/eval-process.md` (8 steps: prepare → parallel run → timing → grade → aggregate → analyst → report → cleanup)
- **Assertion design**: `references/grading-rubric.md`
- **Output formats**: `references/benchmark-template.md`

## Grading Scale

- **A** — All checklist items pass, follows best practices
- **B** — Minor issues (1-2 suggestions)
- **C** — Several issues (3+ important items)
- **D** — Significant problems affecting functionality
- **F** — Critical issues, fundamentally broken

## Description Optimization (Optional)

After review is satisfactory, offer to optimize skill/agent `description` fields for trigger accuracy. See `references/trigger-test-template.md` for the full process:

1. Generate 20 test queries (10 should-trigger, 10 should-not-trigger)
2. Split 60% train / 40% test
3. Evaluate current description (3 runs per query)
4. Propose improvements, re-evaluate, iterate up to 5 times
5. Select best by test score, present before/after comparison
