---
description: "Review Claude configuration files. Use `/review` for total review, or `/review <path>` to target a specific file or directory."
---

You are running in the MAIN session. This command orchestrates two parallel concerns:
- **Audit** — quality review of config files against `docs/baseline/*.md`. Done by the `reviewer` subagent.
- **Benchmark** — measured comparison of skill-on vs skill-off behavior. Done by `eval-runner` × 2 + `grader` for each target.

The benchmark step MUST run in the main session because subagents cannot spawn further subagents (`docs/baseline/subagents.md`). The reviewer is itself a subagent and therefore cannot dispatch eval-runners. Orchestration responsibility lives here.

**Mode detection:**
- `/review` (no args) → **Total mode**: all skills (`skills/**/SKILL.md`) and all agents (`agents/*.md`)
- `/review <path>` → **Target mode**: only the specified file or directory

## Steps

### 1. Discover targets

- **Total mode**: `Glob skills/**/SKILL.md`, `Glob agents/*.md`
- **Target mode**: only the path passed as argument; classify as skill / agent / command / other

### 2. Run benchmarks (parallel, main-session only)

For each skill/agent target found:

1. In a SINGLE message, dispatch BOTH eval-runner agents in parallel:
   - `Agent` (subagent_type=`cchelp:eval-runner`) with prompt: `mode=with_skill`, `skill_path=<target>`, `output_dir=/tmp/cchelp-eval-<name>/with_skill/`
   - `Agent` (subagent_type=`cchelp:eval-runner`) with prompt: `mode=baseline`, `skill_path=null`, `output_dir=/tmp/cchelp-eval-<name>/baseline/`
2. From each agent's response, parse the `<usage>` block to capture `total_tokens` and `duration_ms`.
3. Dispatch `cchelp:grader` to compare the two output dirs and emit `/tmp/cchelp-bench-results/<name>/grading.json`.
4. Aggregate token/duration deltas alongside the grader's pass-rate.

If the `Agent` tool is unavailable in this environment (deferred and not loaded after `ToolSearch`), skip benchmarks entirely. Set `bench_available=false` and proceed to Step 3.

### 3. Run audit (reviewer subagent)

Dispatch the `cchelp:reviewer` subagent with:
- mode: `total` or `target`
- target_path: (only in target mode)
- bench_results_path: `/tmp/cchelp-bench-results/` (if benchmarks ran) or the literal string `N/A` (if skipped)

The reviewer will:
- Audit each category against `docs/baseline/<cat>.md`
- Read benchmark grading.json files from `bench_results_path` and integrate into report
- Write `docs/claude-config-review-report.md`

### 4. Output to terminal

After the reviewer returns, **read `docs/claude-config-review-report.md` directly** and output:
1. Summary table (with Benchmark column)
2. Top 3 issues
3. Key observations (if present)
4. Report file path: `docs/claude-config-review-report.md`

Do NOT rely on the reviewer's return message — always read from the report file.

### 5. Cleanup (optional)

After the report is written and surfaced, remove `/tmp/cchelp-eval-*/` and `/tmp/cchelp-bench-results/` directories.
