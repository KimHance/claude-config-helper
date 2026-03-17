---
name: review
description: Review checklist and evaluation criteria for Claude Code configuration files including CLAUDE.md, memory, skills, agents, commands, hooks, settings, and MCP setup
---

# Claude Config Review

Evaluation criteria for reviewing Claude Code configuration files. Each category has a detailed checklist in `references/`.

## Workflow

1. **Scan** — Find all Claude-related files at project level
2. **Categorize** — Determine which of the 8 categories are applicable (skip N/A)
3. **Evaluate** — For each category, load `references/<category>-checklist.md` and check each item
4. **Cross-validate** — Verify references between files are consistent
5. **Grade** — Assign A/B/C/D/F per category based on checklist compliance
6. **Report** — Terminal summary table + detailed `docs/claude-config-review-report.md`

## Categories

| # | Category | Files to Check | Reference |
|---|----------|---------------|-----------|
| 1 | CLAUDE.md | `CLAUDE.md`, `**/CLAUDE.md` | `references/claude-md-checklist.md` |
| 2 | Memory | `~/.claude/projects/*/memory/` | `references/memory-checklist.md` |
| 3 | Skills | `skills/**/SKILL.md` | `references/skills-checklist.md` |
| 4 | Subagents | `agents/*.md` | `references/agents-checklist.md` |
| 5 | Commands | `commands/*.md` | `references/commands-checklist.md` |
| 6 | Hooks | `hooks/hooks.json`, hook scripts | `references/hooks-checklist.md` |
| 7 | Settings | `.claude/settings.json` (project-level) | `references/settings-checklist.md` |
| 8 | MCP | `.mcp.json` (project-level) | `references/mcp-checklist.md` |

## Cross-Validation Checks

After category reviews, verify:
- CLAUDE.md references to skills/agents actually exist
- Memory file references point to valid paths
- Settings permissions match installed plugins' tool names
- No orphaned agents/skills (defined but never discoverable)

## Grading Scale

- **A** — All checklist items pass, follows best practices
- **B** — Minor issues (1-2 suggestions)
- **C** — Several issues (3+ important items)
- **D** — Significant problems affecting functionality
- **F** — Critical issues, fundamentally broken
