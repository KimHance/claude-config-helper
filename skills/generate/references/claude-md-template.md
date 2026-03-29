# CLAUDE.md Template

## File Locations

| Scope | Location | Purpose |
|---|---|---|
| Managed policy | macOS: `/Library/Application Support/ClaudeCode/CLAUDE.md`, Linux: `/etc/claude-code/CLAUDE.md` | Organization-wide |
| Project | `./CLAUDE.md` or `./.claude/CLAUDE.md` | Team-shared (committed) |
| User | `~/.claude/CLAUDE.md` | Personal preferences |

## Structure

```markdown
# Project Name

## Overview
Brief 1-2 sentence description of what the project does.

## Tech Stack
- Language/framework versions
- Key dependencies

## Conventions
- Naming conventions (files, variables, functions)
- Code style (formatter, linter config)
- Import ordering

@docs/coding-standards.md

## Commands
- Build: `command`
- Test: `command`
- Lint: `command`
- Dev server: `command`

## Architecture
Brief description of project structure and key directories.

## Patterns
Project-specific patterns Claude should follow.

## Constraints
Things Claude should NOT do in this project.
```

## Importing Files

Use `@path/to/file` to import additional context. Relative paths resolve from the containing file. Maximum 5 hops.

```markdown
See @README.md for project overview and @package.json for available commands.
@docs/api-guide.md
```

### AGENTS.md Compatibility

If the project has an `AGENTS.md`, create a CLAUDE.md that imports it:

```markdown
@AGENTS.md

## Claude Code
Additional Claude Code-specific instructions here.
```

## Path-Specific Rules (`.claude/rules/`)

Place rule files in `.claude/rules/` — each file covers one topic.

### Global rule (loaded at launch)

```markdown
# Testing Standards

Run the full test suite before committing.
Use integration tests for database operations.
```

### Path-specific rule (loaded on demand)

```markdown
---
paths:
  - "src/api/**/*.ts"
---

# API Development Rules

Use Zod for request validation.
Return standardized error responses.
```

User-level rules go in `~/.claude/rules/`. Symlinks are supported.

## Excluding CLAUDE.md Files

Use `claudeMdExcludes` in settings to skip irrelevant files (useful in monorepos):

```json
{
  "claudeMdExcludes": [
    "**/other-team/CLAUDE.md",
    "/path/to/monorepo/legacy/.claude/rules/**"
  ]
}
```

Managed policy CLAUDE.md files cannot be excluded.

## Best Practices

- Target under 200 lines per CLAUDE.md file
- Write concrete, verifiable instructions ("Use 2-space indentation" not "Format code properly")
- Use imperative tone: "Run tests with `npm test`" not "Tests are run using npm test"
- Only include information Claude wouldn't already know
- Use `@path` imports instead of inlining large reference material
- Use `.claude/rules/` for path-specific conventions instead of bloating root CLAUDE.md
- Module-level CLAUDE.md should only contain module-specific info
- Remove conflicting instructions across files
