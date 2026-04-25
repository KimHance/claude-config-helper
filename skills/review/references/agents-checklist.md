# Subagent Definitions Review Checklist

## Frontmatter
- [ ] Has `name` field
- [ ] Has `description` field with trigger examples
- [ ] Has `model` field with appropriate choice
- [ ] Description includes `<example>` blocks for accurate matching

## Model Selection
- [ ] `opus` — used for complex reasoning, deep analysis, creative tasks
- [ ] `sonnet` — used for standard tasks, code generation, structured output
- [ ] `haiku` — used for lightweight, fast, simple tasks
- [ ] `inherit` — used when the parent model choice should carry through
- [ ] Model choice is justified for the agent's workload

## Role Definition
- [ ] Clear statement of what the agent does
- [ ] Specific behavioral instructions
- [ ] Structured output format defined (if applicable)
- [ ] Step-by-step workflow outlined

## Scope
- [ ] Not overlapping with other agents' responsibilities
- [ ] Not too broad (trying to do everything)
- [ ] Not too narrow (could be a simple prompt instead)

## Tool Access
- [ ] If agent needs specific tools, they are mentioned in the instructions
- [ ] No unnecessary tool access requested
- [ ] `tools` (allowlist) vs `disallowedTools` (denylist) used appropriately — not both for the same tool
- [ ] MCP tools inherited from parent session unless explicitly scoped via `mcpServers` field

## Advanced Frontmatter (if used)
- [ ] `permissionMode` — appropriate mode chosen (`default`, `acceptEdits`, `auto`, `dontAsk`, `bypassPermissions`, `plan`); honored when running with `--agent <name>` flag (v2.1.119+)
- [ ] `maxTurns` — reasonable limit set to prevent runaway agents (if used)
- [ ] `skills` — preloaded skills are relevant to the agent's task; full content injected at startup, not just descriptions
- [ ] `mcpServers` — inline server definitions scoped to subagent; string references reuse parent session connections
- [ ] `hooks` — lifecycle hooks scoped to subagent; not supported in plugin subagents (silently ignored)
- [ ] `memory` — persistent memory scope set correctly (`user`, `project`, or `local`) if cross-session learning is needed
- [ ] `background` — set to `true` only for agents that should always run as background tasks
- [ ] `effort` — effort level override appropriate for agent's workload
- [ ] `isolation` — `worktree` used when agent needs an isolated git worktree copy (auto-cleaned if no changes made)
- [ ] `color` — display color set for visual identification in UI (if used)
- [ ] `initialPrompt` — auto-submitted first turn is appropriate for agents run as main session via `--agent` (if used)
