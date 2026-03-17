# cchelp

Review and generate Claude Code configuration files (CLAUDE.md, skills, agents, memory, hooks, MCP, etc.).

## Routing

- Claude config **review** tasks → `reviewer` subagent
- Claude config **generation/scaffolding** tasks → `generator` subagent
- Claude config **full setup** (generate + review) → `gn-rv` skill
- Review criteria are in the `review` skill
- Generation templates are in the `generate` skill

## Constraints

- Do NOT review or modify user-level files (`~/.claude/settings.json`, `~/.claude/settings.local.json`)
- Do NOT review `.claude/settings.local.json` (gitignored, personal environment)