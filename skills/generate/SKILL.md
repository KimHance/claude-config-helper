---
name: generate
description: Use when scaffolding or creating Claude Code configuration files from scratch. Provides templates for CLAUDE.md, memory, skills, agents, commands, hooks, settings, and MCP setup.
---

# Claude Config Generator

Templates and guidelines for scaffolding Claude Code configuration files. Each file type has a template in `references/`.

## Workflow

1. **Assess** — Read project structure to understand tech stack and conventions
2. **Plan** — Determine which config files are needed
3. **Generate** — Create files using templates from `references/`
4. **Tailor** — Customize generated files to the specific project
5. **Verify** — Self-check all generated files for consistency

## File Types

| # | Type | Template | Output Path |
|---|------|----------|-------------|
| 1 | CLAUDE.md | `references/claude-md-template.md` | `./CLAUDE.md` |
| 2 | Memory | `references/memory-template.md` | `~/.claude/projects/*/memory/` |
| 3 | Skills | `references/skill-template.md` | `./skills/<name>/SKILL.md` |
| 4 | Agents | `references/agent-template.md` | `./agents/<name>.md` |
| 5 | Commands | `references/command-template.md` | `./commands/<name>.md` |
| 6 | Hooks | `references/hooks-template.md` | `./hooks/hooks.json` |
| 7 | Settings | `references/settings-template.md` | `./.claude/settings.json` |
| 8 | MCP | `references/mcp-template.md` | `./.mcp.json` |

## Key Principles

- **Concise over comprehensive** — Context window is a shared resource
- **Imperative tone** — "Use X" not "This project uses X"
- **Project-specific** — Tailor to actual tech stack, not generic boilerplate
- **Progressive disclosure** — Put details in reference files, keep main files lean
- **No duplication** — Don't repeat info across CLAUDE.md levels
