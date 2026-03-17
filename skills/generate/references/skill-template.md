# Skill Template

## SKILL.md Structure

```markdown
---
name: skill-name
description: When to use this skill — specific enough for discovery matching
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

## Directory Structure

```
skills/
└── skill-name/
    ├── SKILL.md           # Main skill file (kept lean)
    └── references/        # Detailed reference docs
        ├── topic-a.md
        └── topic-b.md
```

## Best Practices

- Description should explain WHEN to use, not just WHAT it does
- Keep SKILL.md under 200 lines
- Move detailed checklists/guides to references/ for progressive disclosure
- Content should be actionable, not narrative
- Don't explain things Claude already knows
