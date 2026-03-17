# CLAUDE.md Template

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

## Best Practices

- Keep under 200 lines for project-level
- Module-level CLAUDE.md should only contain module-specific info
- Use imperative tone: "Run tests with `npm test`" not "Tests are run using npm test"
- Only include information Claude wouldn't already know
- Link to docs rather than inlining large reference material
