# cchelp

Review and generate Claude Code configuration files (CLAUDE.md, skills, agents, memory, hooks, MCP, etc.).

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

## Constraints

- Do NOT review or modify user-level files (`~/.claude/settings.json`, `~/.claude/settings.local.json`)
- Do NOT review `.claude/settings.local.json` (gitignored, personal environment)