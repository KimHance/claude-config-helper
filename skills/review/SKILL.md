---
name: review
description: Use when reviewing or auditing Claude Code configuration files for quality. Evaluates CLAUDE.md, memory, skills, agents, commands, hooks, and MCP against best-practice checklists with optional parallel benchmark eval.
---

# Claude Config Review

Evaluation criteria for reviewing Claude Code configuration files. Rules live in `docs/baseline/*.md` — one file per category, kept in sync with the official Claude Code docs by the `baseline-sync` workflow.

## Modes

- **Total** (`/review`): Scan all categories, benchmark all discovered skills/agents
- **Target** (`/review <path>`): Review and benchmark only the specified file or directory

## Workflow

1. **Scan** — Total: find all Claude-related files. Target: only the specified path.
2. **Categorize** — Determine which of the 7 categories are applicable (skip N/A)
3. **Evaluate** — For each category, load `docs/baseline/<category>.md` and check the target against every section (Fundamentals / Advanced / Recommended / Anti-patterns). Each bullet in the baseline = one check.
4. **Cross-validate** — Verify references between files are consistent
5. **Benchmark** — For Skills and Subagents, spawn `eval-runner` agents in pairs (with-skill + baseline). Skip if the agent-spawn tool is not available in the current environment and mark Benchmark as `N/A` in the report.
6. **Grade** — Assign A/B/C/D/F per category based on baseline compliance + benchmark results
7. **Report** — Terminal summary table + detailed `docs/claude-config-review-report.md`

## Categories

| # | Category | Files to Check | Rule Source |
|---|----------|---------------|-------------|
| 1 | CLAUDE.md | `CLAUDE.md`, `**/CLAUDE.md` | `docs/baseline/claude-md.md` |
| 2 | Memory | `~/.claude/projects/*/memory/` | `docs/baseline/claude-md.md` (claude-md baseline covers memory) |
| 3 | Skills | `skills/**/SKILL.md` | `docs/baseline/skills.md` |
| 4 | Subagents | `agents/*.md` | `docs/baseline/subagents.md` |
| 5 | Commands | `commands/*.md` | `docs/baseline/commands.md` |
| 6 | Hooks | `hooks/hooks.json`, hook scripts | `docs/baseline/hooks.md` |
| 7 | MCP | `.mcp.json` (project-level) | `docs/baseline/mcp.md` |

> Note: `docs/baseline/` also contains `permissions.md`, `plugins.md`, `settings.md`. Use them as cross-cutting rules during cross-validation.

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
