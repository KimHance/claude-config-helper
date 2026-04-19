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
# Optional fields:
# tools: Read, Grep, Glob, Bash          # allowlist (inherits all if omitted)
# disallowedTools: Write, Edit           # denylist (applied before tools allowlist)
# permissionMode: default                # default|acceptEdits|auto|dontAsk|bypassPermissions|plan
# maxTurns: 20                           # cap agentic turns
# skills: [skill-name]                   # preload skill content at startup
# mcpServers: [server-name]              # scoped MCP servers (inline or reference)
# hooks:                                 # lifecycle hooks (not supported in plugin subagents)
# memory: user                           # persistent memory: user|project|local
# background: false                      # true = always runs as background task
# effort: medium                         # low|medium|high|xhigh (Opus 4.7+)|max (Opus only)
# isolation: worktree                    # run in isolated git worktree copy
# color: blue                            # red|blue|green|yellow|purple|orange|pink|cyan
# initialPrompt: ""                      # auto-submitted first turn (for --agent mode only)
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

## Frontmatter Fields

| Field | Required | Description |
|-------|----------|-------------|
| `name` | Yes | Unique identifier (lowercase letters and hyphens) |
| `description` | Yes | When Claude should delegate; include `<example>` trigger blocks |
| `model` | No | `sonnet`, `opus`, `haiku`, full model ID, or `inherit` (default) |
| `tools` | No | Tool allowlist; inherits all tools if omitted |
| `disallowedTools` | No | Tool denylist; applied before `tools` allowlist |
| `permissionMode` | No | `default`, `acceptEdits`, `auto`, `dontAsk`, `bypassPermissions`, `plan` |
| `maxTurns` | No | Max agentic turns before stopping |
| `skills` | No | Skills preloaded at startup (full content injected, not just descriptions) |
| `mcpServers` | No | Scoped MCP servers; inline or by name reference |
| `hooks` | No | Lifecycle hooks (ignored in plugin subagents) |
| `memory` | No | Persistent memory scope: `user`, `project`, or `local` |
| `background` | No | `true` to always run as background task |
| `effort` | No | `low`, `medium`, `high`, `xhigh` (Opus 4.7+ only), `max` |
| `isolation` | No | `worktree` to run in isolated git worktree (auto-cleaned if no changes) |
| `color` | No | UI color: `red`, `blue`, `green`, `yellow`, `purple`, `orange`, `pink`, `cyan` |
| `initialPrompt` | No | Auto-submitted first turn when running as main session agent via `--agent` |

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
- Use `isolation: worktree` for agents that make independent changes in parallel
- Use `skills` to preload relevant reference material (full content injected at startup)
- Prefer `disallowedTools` over `tools` when you want to inherit most tools but block a few
