---
description: "Review Claude configuration files. Use `/review` for total review, or `/review <path>` to target a specific file or directory."
---

You are running in the MAIN session. This command orchestrates two parallel concerns:
- **Audit** — quality review of config files against `docs/baseline/*.md`. Done by the `reviewer` subagent.
- **Benchmark** — measured comparison of skill-on vs skill-off behavior. Done by `eval-runner` × 2 + `grader` for each target, **passed inline as JSON** (no filesystem).

The benchmark step MUST run in the main session because subagents cannot spawn further subagents. The reviewer is itself a subagent and therefore cannot dispatch eval-runners. Orchestration responsibility lives here.

**In-memory pipeline:** eval-runner and grader return their results as fenced JSON in their final response. No file writes by subagents — this avoids permission prompts in user-local environments.

**Mode detection:**
- `/review` (no args) → **Total mode**: all skills (`skills/**/SKILL.md`) and all agents (`agents/*.md`)
- `/review <path>` → **Target mode**: only the specified file or directory

## Steps

### 1. Discover targets

- **Total mode**: `Glob skills/**/SKILL.md`, `Glob agents/*.md`
- **Target mode**: only the path passed as argument; classify as skill / agent / command / other

### 2. Run benchmarks (parallel, in-memory)

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

Dispatch the `cchelp:reviewer` subagent with:
- mode: `total` or `target`
- target_path: (only in target mode)
- bench_data: the collected grading list (inline JSON), or `[]` if unavailable

The reviewer will:
- Audit each category against `docs/baseline/<cat>.md`
- Use the inline `bench_data` to populate per-skill / per-agent benchmark sections in the report
- Write `docs/claude-config-review-report.md`

### 4. Output to terminal

After the reviewer returns, **read `docs/claude-config-review-report.md` directly** and output:
1. Summary table (with Benchmark column)
2. Top 3 issues
3. Key observations (if present)
4. Report file path: `docs/claude-config-review-report.md`

Do NOT rely on the reviewer's return message — always read from the report file.
