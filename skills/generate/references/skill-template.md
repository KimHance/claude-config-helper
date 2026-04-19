# Skill Template

## SKILL.md Structure

```markdown
---
name: skill-name
description: When to use this skill — front-load the key use case (combined with when_to_use, capped at 1,536 chars in listing)
---

# Skill Title

Brief overview of what this skill does.

## Workflow
1. Step one
2. Step two
3. Step three

## Key Principles
- Principle one
- Principle two

## References
Detailed reference material is in `references/` subdirectory.
```

## Frontmatter Reference

| Field | Required | Description |
|---|---|---|
| `name` | Yes | Display name, becomes `/slash-command` |
| `description` | Recommended | When to use — combined with `when_to_use`, truncated at 1,536 chars in skill listing |
| `when_to_use` | No | Supplemental trigger phrases/examples appended to `description` in listing; counts toward 1,536-char cap |
| `argument-hint` | No | Hint shown in autocomplete |
| `disable-model-invocation` | No | `true` = only user can invoke via `/` |
| `user-invocable` | No | `false` = hidden from `/` menu, Claude invokes automatically |
| `allowed-tools` | No | Tools Claude can use without permission prompts |
| `model` | No | Model override (e.g., `opus`, `sonnet`, `haiku`) |
| `effort` | No | Effort level override: `low`, `medium`, `high`, `xhigh` (Opus 4.7+), `max` |
| `context` | No | `fork` to run in isolated subagent |
| `agent` | No | Subagent type when `context: fork` (e.g., `Explore`, `Plan`, custom) |
| `paths` | No | Glob patterns for auto-activation (e.g., `["src/api/**/*.ts"]`) |
| `shell` | No | `bash` or `powershell` |
| `hooks` | No | Hooks scoped to skill lifecycle |

## Advanced Examples

### User-only skill (destructive operation)

```yaml
---
name: deploy
description: Deploy to production — use when user runs /deploy
disable-model-invocation: true
---
```

### Auto-activated path-specific skill

```yaml
---
name: api-guidelines
description: API design guidelines — auto-activates for API route files
paths:
  - "src/api/**/*.ts"
user-invocable: false
---
```

### Skill running in subagent

```yaml
---
name: deep-analysis
description: Deep codebase analysis — use for architecture review
context: fork
agent: Explore
model: opus
---
```

### Skill with hooks

```yaml
---
name: tdd
description: Test-driven development workflow
hooks:
  - event: Stop
    type: command
    command: "./scripts/verify-tests.sh"
---
```

## String Substitutions

| Placeholder | Resolves To |
|---|---|
| `$ARGUMENTS` | Full user arguments after `/skill-name` |
| `$ARGUMENTS[N]` or `$N` | Nth argument (0-indexed) |
| `${CLAUDE_SESSION_ID}` | Current session ID |
| `${CLAUDE_SKILL_DIR}` | Directory containing SKILL.md |

### Dynamic Context Injection

Use `` !`command` `` to run a shell command and inject its output:

```markdown
Current branch: !`git branch --show-current`
Recent changes: !`git log --oneline -5`
```

## Directory Structure

```
skills/
└── skill-name/
    ├── SKILL.md           # Main skill file (kept lean)
    ├── template.md        # Optional template file
    ├── scripts/           # Optional scripts
    └── references/        # Detailed reference docs
        ├── topic-a.md
        └── topic-b.md
```

## Skill Locations

| Location | Scope |
|---|---|
| `.claude/skills/<name>/SKILL.md` | Project-level |
| `~/.claude/skills/<name>/SKILL.md` | Personal (all projects) |
| Enterprise managed settings | Organization-wide |
| `<plugin>/skills/<name>/SKILL.md` | Plugin-provided |

Priority: enterprise > personal > project.

## Best Practices

- Description should explain WHEN to use, not just WHAT it does
- Keep SKILL.md under 500 lines
- Move detailed checklists/guides to references/ for progressive disclosure
- Content should be actionable, not narrative
- Don't explain things Claude already knows
- Use `context: fork` for heavy analysis that might bloat main context
- Use `paths` for auto-activation instead of relying on Claude to discover the skill
- Use `allowed-tools` sparingly — only for tools the skill genuinely needs
