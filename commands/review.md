---
description: "Review Claude configuration files in the current project. Use `/review` for a full review of the 7 config categories, or `/review <path>` to target a specific file or directory."
---

You are running in the MAIN session, executing inside the **user's current working directory**. This command orchestrates two concerns over that cwd:

- **Audit** — quality review of the 7 Claude config categories found in cwd, against internal evaluation criteria. Done by the `reviewer` subagent.
- **Benchmark** — measured comparison of skill-on vs skill-off behavior for any Skills/Subagents found in cwd. Done by `eval-runner` × 2 + `grader` per target, **passed inline as JSON** (no filesystem).

**중요: 리뷰 대상은 항상 사용자 cwd 다.** 플러그인 설치 디렉토리를 리뷰 대상으로 잡으면 안 된다. cwd 에 Claude 설정이 전혀 없으면 빈 결과로 보고하고 종료한다 — 다른 디렉토리로 fallback 하거나 사용자에게 "어디를 리뷰할까요?" 라고 되묻지 말 것.

The benchmark step MUST run in the main session because subagents cannot spawn further subagents. The reviewer is itself a subagent and therefore cannot dispatch eval-runners. Orchestration responsibility lives here.

**In-memory pipeline:** eval-runner and grader return their results as fenced JSON in their final response. No file writes by subagents — this avoids permission prompts in user-local environments.

**Mode detection:**
- `/review` (no args) → **Total mode**: scan all 7 categories in cwd, benchmark every discovered skill/agent
- `/review <path>` → **Target mode**: only the specified path within cwd

## Steps

### 0. Progress tracking (MANDATORY)

Before Step 1, call `TaskCreate` to register the progress checkboxes the user will see in the UI. Create tasks with emoji-prefixed subjects.

**For Total mode** (7 categories in cwd), create 8 tasks in this order:

```
📋 Discover targets (7 categories in cwd)
🚀 Bench skills — eval-runner × N parallel
⚖️ Grade skills — grader × M
🚀 Bench agents — eval-runner × N parallel
⚖️ Grade agents — grader × M
🔍 Audit — reviewer subagent (7 categories)
🛡️ Verify (bench_data non-empty when targets exist)
📊 Read report + print summary
```

**For Target mode** (single path), create 5 tasks:

```
📋 Discover target
🚀 Bench target — eval-runner × 2 (or skip if non-skill/agent)
⚖️ Grade target — grader × 1 (or skip)
🔍 Audit — reviewer subagent
📊 Read report + print summary
```

Set each task's `activeForm` to a present-continuous form (e.g., "📋 Discovering targets") so the spinner shows it nicely when in_progress.

At the START of each subsequent Step (1, 2, 3, …), call `TaskUpdate(status=in_progress)` on the corresponding task. At the END, call `TaskUpdate(status=completed)`. The user sees a live checklist with checkboxes ticking off.

If any step fails (e.g., agent unavailable, C8 detects invalid deletion), leave that task `in_progress` and add a follow-up task explaining the failure rather than marking complete.

### 1. Discover targets (cwd 한정)

Mark task "📋 Discover ..." as `in_progress` at the start, then `completed` at the end.

- **Total mode**: 사용자 cwd 안에서 7 카테고리 글롭 — `CLAUDE.md`, `**/CLAUDE.md`, `skills/**/SKILL.md`, `agents/*.md`, `commands/*.md`, `hooks/hooks.json`, `.mcp.json`, `.claude/` 하위 변형들.
- **Target mode**: 인자로 받은 경로만. cwd 기준 상대경로 또는 절대경로 둘 다 허용. 카테고리 판정 (skill / agent / command / hook / mcp / claude-md / other).

발견 결과가 비어있어도 그게 정상 결과다. 다른 디렉토리로 자동 이동하거나 사용자에게 되묻지 말 것. 빈 결과는 빈 결과 그대로 reviewer 에게 넘긴다.

### 2. Run benchmarks (parallel, in-memory) — MANDATORY when targets exist

Mark task "🚀 Bench ..." as `in_progress` before dispatch, `completed` after all eval-runners return. Mark task "⚖️ Grade ..." as `in_progress` before dispatching graders, `completed` after grading dicts collected.

Do NOT skip Step 2. If Step 1 returned any **Skills or Subagents** targets, you MUST dispatch eval-runners + graders before proceeding to Step 3. Step 3's reviewer needs `bench_data` from this step.

(다른 5 카테고리 — CLAUDE.md, Memory, Commands, Hooks, MCP — 는 벤치마크 대상이 아니다. 정적 평가만으로 Step 3 으로 넘긴다.)

Skip is acceptable ONLY when:
- Step 1 returned 0 Skills/Subagents targets, OR
- The `Agent` tool is provably unavailable (verify via `ToolSearch select:Agent`).

"Save tokens", "looks complex", "user didn't ask explicitly" — NOT valid reasons to skip. The slash command's purpose is to run audit AND bench together; partial execution defeats the design.

For each skill/agent target found:

1. In a SINGLE message, dispatch BOTH eval-runner agents in parallel:
   - `Agent` (subagent_type=`cchelp:eval-runner`) prompt: `target_path=<path>` and `mode=with_skill`
   - `Agent` (subagent_type=`cchelp:eval-runner`) prompt: `target_path=<path>` and `mode=baseline`

2. From each agent's response, parse:
   - The fenced JSON block (contains `samples`)
   - The `<usage>` block (extract `total_tokens` and `duration_ms`)

3. Dispatch grader once per target:
   - `Agent` (subagent_type=`cchelp:grader`) with prompt: a fenced JSON object containing `{category, with_skill: {samples, usage}, baseline: {samples, usage}}` exactly per grader spec.
   - The grader returns `{category, aggregate}` JSON inline.

4. Collect the grading dicts in a list.

If the `Agent` tool is unavailable or any subagent fails, set `bench_available=false` and proceed to Step 3 with an empty list.

### 3. Run audit (reviewer subagent)

Mark task "🔍 Audit ..." as `in_progress` before dispatch, `completed` after reviewer returns.

Dispatch the `cchelp:reviewer` subagent with:
- mode: `total` or `target`
- target_path: (only in target mode)
- bench_data: the collected grading list (inline JSON), or `[]` if unavailable or if no Skills/Subagents existed in cwd

The reviewer will:
- Audit each of the 7 categories present in cwd against internal evaluation criteria (loaded from plugin install dir, transparent to user)
- Mark missing categories as N/A (rows preserved)
- Use the inline `bench_data` to populate per-skill / per-agent benchmark sections in the report
- Write `docs/claude-config-review-report.md` **into the user's cwd**

### 4. Pre-output verification (MANDATORY)

Mark task "🛡️ Verify ..." as `in_progress`. If passes, `completed`. If fails, leave `in_progress` and surface the gap.

Before reading the report, verify:
- Step 1 에서 발견된 Skills/Subagents 가 있었으면, `bench_data` 는 비어있으면 안 됨 — 그러면 Step 2 를 건너뛴 것이므로 돌아가서 dispatch.
- Skills/Subagents 가 0 개였으면 `bench_data` 가 `[]` 인 것이 정상.

Benchmark 컬럼은 "Skills/Subagents 가 cwd 에 존재했을 때" 만 숫자가 있어야 한다. 없을 때 N/A 는 정상.

### 5. Output to terminal

Mark task "📊 Read report ..." as `in_progress` before reading, `completed` after printing.

reviewer 가 cwd 의 `docs/claude-config-review-report.md` 에 보고서를 작성하므로, 이 경로를 cwd 기준으로 Read 한 뒤 다음을 터미널에 출력:

1. Summary table (7 카테고리 행 전부, 미발견 카테고리는 N/A. Benchmark 컬럼은 Skills/Subagents 에만 숫자)
2. Top 3 issues
3. Key observations (if present)
4. Report file path: `docs/claude-config-review-report.md` (cwd 기준)

Do NOT rely on the reviewer's return message — always read from the report file in cwd.
