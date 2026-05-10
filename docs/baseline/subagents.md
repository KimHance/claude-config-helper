# subagents

> This file is a cchelp review baseline authored by the maintainer.
> The weekly workflow compares each section against the official Claude docs and rewrites only the sections whose **meaning** has drifted.
> Update granularity = a single section (one `##` heading). If the meaning is unchanged, the section is left byte-for-byte intact — no rewording, no reordering.

## Fundamentals
- Subagents are specialized AI assistants that handle specific kinds of tasks in their own isolated context window
- Subagent files are Markdown with YAML frontmatter at `.claude/agents/<name>.md` (project) or `~/.claude/agents/<name>.md` (user)
- Required frontmatter fields are `name` (lowercase letters and hyphens) and `description` (when Claude should delegate to it)
- The markdown body becomes the subagent's system prompt; subagents receive only this prompt plus basic environment details
- Each subagent runs in its own context window with custom system prompt, specific tool access, and independent permissions
- Claude automatically delegates when a request matches the subagent's `description`; "use proactively" phrasing in description encourages delegation
- Subagents are spawned via the Agent tool (renamed from Task in version 2.1.63; `Task(...)` references still work as aliases)
- Each subagent invocation creates a fresh context; subagent context does not persist across invocations unless resumed
- Three explicit invocation patterns: natural language (Claude decides), @-mention (`@agent-<name>` or picker, guarantees that subagent), and session-wide via `--agent <name>` or `agent` setting
- A subagent's `description` field combined with the user request decides automatic delegation; clear specific descriptions improve routing

## Advanced
- Optional frontmatter: `tools`, `disallowedTools`, `model`, `permissionMode`, `maxTurns`, `skills`, `mcpServers`, `hooks`, `memory`, `background`, `effort`, `isolation`, `color`, `initialPrompt`
- `tools` is allowlist; `disallowedTools` is denylist; if both set, denylist applied first then allowlist resolved against the remainder
- `model` accepts `sonnet`/`opus`/`haiku`/full model id (e.g. `claude-opus-4-7`)/`inherit`; defaults to `inherit`
- `permissionMode` values: `default`, `acceptEdits`, `auto`, `dontAsk`, `bypassPermissions`, `plan`
- `permissionMode` is ignored for plugin subagents (security)
- `mcpServers` and `hooks` frontmatter are also ignored for plugin subagents (security)
- `skills` injects full skill content into subagent context at startup; subagents do not inherit skills from parent
- Skills with `disable-model-invocation: true` cannot be preloaded into subagents
- `memory: user` stores at `~/.claude/agent-memory/<name>/`, `memory: project` at `.claude/agent-memory/<name>/`, `memory: local` at `.claude/agent-memory-local/<name>/`
- When `memory` is enabled, the subagent's prompt includes the first 200 lines or 25KB of `MEMORY.md`, and Read/Write/Edit tools are auto-enabled
- `isolation: worktree` runs the subagent in a temporary git worktree; the worktree is auto-cleaned if the subagent makes no changes
- `initialPrompt` is auto-submitted as the first user turn when the agent runs as the main session via `--agent` or `agent` setting
- `background: true` always runs the subagent as a background task; default false
- `color` accepts `red`/`blue`/`green`/`yellow`/`purple`/`orange`/`pink`/`cyan` for display in task list and transcript
- Built-in subagents: Explore (Haiku, read-only), Plan (inherits model, read-only, used in plan mode), general-purpose (all tools, inherits model), plus helpers `statusline-setup` (Sonnet) and `claude-code-guide` (Haiku)
- Subagent scope priority: managed settings > `--agents` CLI flag > project `.claude/agents/` > user `~/.claude/agents/` > plugin `agents/` directory
- Plugin subagents appear in `/agents` and are referenced as `<plugin-name>:<agent-name>`
- `/agents` command opens a tabbed UI (Running / Library) for managing subagents; supports "Generate with Claude" to author the system prompt
- `claude agents` CLI lists configured subagents grouped by source, indicating which are overridden
- `--agents '<JSON>'` CLI flag defines session-only subagents inline; supports the same fields as file-based, with `prompt` instead of markdown body
- Disable specific subagents via `permissions.deny: ["Agent(name)"]` in settings, or `--disallowedTools "Agent(name)"`
- Restrict which subagents an agent can spawn via `tools: Agent(worker, researcher)` (allowlist); `Agent` alone allows any; omitting `Agent` disallows all
- This restriction applies only to agents running as main thread (`claude --agent`); subagents themselves cannot spawn other subagents
- Subagent file edits to disk require session restart; `/agents` interface changes apply immediately
- Resolution order for the model: `CLAUDE_CODE_SUBAGENT_MODEL` env var > per-invocation `model` parameter > frontmatter `model` > main conversation's model
- Subagents support hooks `PreToolUse`, `PostToolUse`, and `Stop` (converted to `SubagentStop` at runtime); main session can also subscribe via `SubagentStart`/`SubagentStop` in `settings.json`
- Hooks receive the active effort level via `effort.level` JSON input field and `$CLAUDE_EFFORT` environment variable
- Subagent transcripts persist at `~/.claude/projects/{project}/{sessionId}/subagents/agent-{agentId}.jsonl`, independent of main conversation, cleaned per `cleanupPeriodDays` (default 30)
- Subagents support auto-compaction at ~95% capacity by default; `CLAUDE_AUTOCOMPACT_PCT_OVERRIDE` lowers the threshold
- Foreground subagents block main conversation; background subagents pre-approve permissions before launch and auto-deny anything not pre-approved
- `CLAUDE_CODE_DISABLE_BACKGROUND_TASKS=1` disables all background task functionality; Ctrl+B backgrounds a running task
- Fork mode (experimental, `CLAUDE_CODE_FORK_SUBAGENT=1`, requires v2.1.117+): spawns a fork that inherits full conversation history, system prompt, tools, model; `/fork <directive>` triggers it; forks cannot spawn further forks
- Resume an existing subagent via `SendMessage` tool with the agent ID; requires `CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1`
- MCP servers can be scoped to subagents via the `mcpServers` field; the `alwaysLoad` option on an MCP server ensures all its tools are available to subagents without tool-search deferral

## Recommended
- Design each subagent to excel at one specific task; write detailed `description` so Claude knows when to delegate
- Include "Use proactively" or domain-specific trigger phrases in the description to encourage automatic delegation
- Limit tool access to the minimum required (principle of least privilege); for read-only roles use `tools: Read, Grep, Glob, Bash`
- Use `model: haiku` for lightweight tasks (cost), `sonnet`/`opus` for complex reasoning
- Use subagents to isolate high-volume output (test runs, log analysis, doc fetches) so verbose content stays out of main context
- Spawn multiple subagents in parallel for independent investigations (research splits)
- Chain subagents in sequence for multi-step workflows (reviewer → optimizer)
- Use `permissionMode: plan` for read-only exploration agents; `acceptEdits` for agents expected to modify files
- Use `isolation: worktree` when subagent edits could conflict with parallel work in the main session
- Preload domain-specific skills via `skills` field rather than relying on the subagent to discover them at runtime
- Use `memory: project` (recommended default) when subagent should accumulate codebase-specific knowledge across sessions; ask the subagent to consult and update its memory
- Define `PreToolUse` hooks for runtime validation when `tools`/`disallowedTools` is too coarse (e.g. allowing Bash but only SELECT queries)
- Check project subagents into version control under `.claude/agents/` so the team shares them
- Use `--agents` JSON flag for ephemeral, automation-only subagents that should not persist
- Use a fork (when fork mode is enabled) when a named subagent would need too much background to be useful
- Generate the system prompt via `/agents` → "Generate with Claude" rather than authoring blindly
- Use `@-mention` to guarantee a specific subagent runs for one task instead of relying on automatic delegation

## Anti-patterns
- Subagents cannot spawn other subagents; nested delegation is unsupported — use Skills or chain from main conversation instead
- Do not use subagents for tasks needing frequent back-and-forth or iterative refinement; main conversation is better
- Do not assume a subagent inherits skills from the parent; always list them explicitly in `skills` field
- Do not edit `.claude/agents/` files directly during a session expecting changes to apply; restart, or use `/agents`
- Do not use `permissionMode: bypassPermissions` casually; it skips approval for `.git`, `.claude`, `.vscode`, `.idea`, `.husky` writes (root-level `rm -rf /` still prompts as a circuit breaker)
- Do not set `hooks`, `mcpServers`, or `permissionMode` on plugin subagents — they are silently ignored
- Do not expect parent's `bypassPermissions` or `acceptEdits` to be overridable from a child subagent; parent takes precedence
- Do not use `auto` permission mode in subagent frontmatter when parent is also in auto — child's frontmatter is ignored, parent's classifier evaluates everything
- Do not preload skills with `disable-model-invocation: true` — Claude Code skips them and warns
- Do not stack many parallel subagents whose results all return verbose summaries; main context still bears the cost
- Do not rely on subagent transcripts being available indefinitely; `cleanupPeriodDays` (default 30) wipes them
- Do not skip the `description` field hoping the body is enough; without a clear description Claude cannot reliably auto-delegate
- Do not use a subagent for a quick question already in your context; use `/btw` instead
