# Agent Template

## Agent .md Structure

```markdown
---
name: agent-name
description: |
  What this agent does and when to use it. Include trigger examples:
  <example>user: "trigger phrase" assistant: spawns this agent</example>
  <example>user: "another trigger" assistant: spawns this agent</example>
model: sonnet|opus|haiku|inherit
---

You are a [Role]. Your job is to [primary responsibility].

## Process

### Step 1: [First action]
Description of what to do.

### Step 2: [Second action]
Description of what to do.

## Output Format
How results should be presented.
```

## Model Selection Guide

| Model | Use When |
|-------|----------|
| `opus` | Complex reasoning, deep analysis, creative tasks |
| `sonnet` | Standard tasks, code generation, structured output |
| `haiku` | Lightweight, fast, simple tasks |
| `inherit` | Parent model choice should carry through |

## Best Practices

- Include 3-5 trigger examples in description for accurate matching
- Include both Korean and English triggers if user is bilingual
- Define a clear step-by-step workflow
- Specify output format expectations
- Don't overlap responsibilities with other agents
