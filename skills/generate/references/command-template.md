# Command (Slash Command) Template

## Structure

```markdown
---
description: Brief description of what the command does
---

Instructions for Claude when this command is invoked.
Typically delegates to an agent or skill for complex tasks.
```

## Best Practices

- Command name: kebab-case, 1-3 words, intuitive
- Description should help Claude match user intent
- Delegate to agents/skills for complex workflows
- Keep command body concise — it's a trigger, not the full implementation
- Built-in skills `/init`, `/review`, and `/security-review` are invokable by Claude via the Skill tool (v2.1.113+) — delegate to them rather than reimplementing their logic
