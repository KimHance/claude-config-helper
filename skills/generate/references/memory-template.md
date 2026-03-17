# Memory System Template

## MEMORY.md (index file)

```markdown
# Memory Index

## User
- [User role and preferences](user_role.md) - Brief description

## Feedback
- [Feedback item](feedback_topic.md) - Brief description

## Project
- [Project context](project_topic.md) - Brief description

## Reference
- [External resource](reference_topic.md) - Brief description
```

## Memory File Template

```markdown
---
name: descriptive-name
description: One-line description specific enough for relevance matching
type: user|feedback|project|reference
---

Memory content here.

For feedback/project types, structure as:
**Why:** Reason or context
**How to apply:** When and how this should influence behavior
```

## Best Practices

- MEMORY.md is an index only — no content, just links
- Keep MEMORY.md under 200 lines
- Use absolute dates, never relative ("2026-03-17" not "next Thursday")
- Name files semantically by topic, not chronologically
- Check for duplicates before creating new memories
