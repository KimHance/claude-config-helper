# Benchmark Eval Process

Step-by-step procedure for running parallel benchmark evaluation on Skills and Subagents using `eval-runner` agents.

## Step 1: Prepare

- If updating an existing skill, snapshot the original first:
  ```bash
  cp -r <skill-path> /tmp/cchelp-eval-<skill-name>/skill-snapshot/
  ```
- Determine output directory: `/tmp/cchelp-eval-<skill-name>/iteration-<N>/eval-<name>/`

## Step 2: Spawn eval-runner Agents

**Critical: Launch both runs in the same turn simultaneously.**

In a single message, spawn two `eval-runner` agent calls with `run_in_background: true`:

- **With-skill eval-runner**:
  - `target_path`: path to the skill/agent being evaluated
  - `mode`: `with_skill`
  - `skill_path`: path to the skill (or snapshot for baseline comparison)
  - `output_dir`: `.../with_skill/outputs/`

- **Baseline eval-runner**:
  - `target_path`: same path
  - `mode`: `baseline`
  - `skill_path`: null (or old skill snapshot path)
  - `output_dir`: `.../without_skill/outputs/`

Each eval-runner will:
1. Read the target's description and workflow
2. Auto-generate 2-3 test prompts
3. Execute with or without the skill
4. Save outputs and `eval_metadata.json`

## Step 3: Collect Timing

When each eval-runner completes, **immediately** extract `total_tokens` and `duration_ms` from the completion notification and save to `timing.json` in the respective run directory. This data is only available in the notification — capture it right away.

```json
{ "total_tokens": 84852, "duration_ms": 23332, "total_duration_seconds": 23.3 }
```

## Step 4: Grade

Spawn the `grader` agent to compare outputs. The grader:
- Evaluates both runs against review checklists
- Drafts assertions if none exist in eval_metadata.json
- Produces `grading.json` with exact fields: `text`, `passed`, `evidence`
- Adds analyst notes (non-discriminating assertions, variance, patterns)

See `grading-rubric.md` for assertion design principles and examples.

## Step 5: Aggregate Benchmark

Collect all eval results and compute:
- Pass rate per run type (with_skill vs baseline)
- Mean and standard deviation for tokens and duration
- Delta comparisons

Save as `benchmark.json`. See `benchmark-template.md` for the exact format.

## Step 6: Analyst Pass

Review the benchmark data for hidden patterns:
- Assertions that always pass in both runs (non-discriminating — remove them)
- High-variance evals (possibly flaky — flag them)
- Token/time tradeoffs worth noting

## Step 7: Embed in Report

Add the benchmark results to the relevant category section in `docs/claude-config-review-report.md`. Use the table format from `benchmark-template.md`.

## Step 8: Cleanup

Delete the `/tmp/cchelp-eval-<skill-name>/` directory after results are embedded in the report.
