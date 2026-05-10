# hooks

> This file is a cchelp review baseline authored by the maintainer.
> The weekly workflow compares each section against the official Claude docs and rewrites only the sections whose **meaning** has drifted.
> Update granularity = a single section (one `##` heading). If the meaning is unchanged, the section is left byte-for-byte intact — no rewording, no reordering.

## Fundamentals
- Hooks are user-defined shell commands, HTTP endpoints, MCP tool calls, prompts, or subagents that fire at specific Claude Code lifecycle points
- Hooks are configured under the top-level `hooks` key in `settings.json` (user, project, local) or in skill/agent frontmatter or in plugin `hooks/hooks.json`
- A hook entry has the shape `{ "EventName": [ { "matcher": "...", "hooks": [ { "type": "...", ... } ] } ] }`
- Hook command receives JSON input on stdin describing the event (session_id, cwd, hook_event_name, plus event-specific fields)
- Hook command communicates back via exit code, stdout, and stderr
- Exit code 0 = success; stdout is parsed as JSON if exit code 0
- Exit code 2 = blocking error (where the event supports blocking); stderr is fed back as the error message to Claude
- Other non-zero exit codes = non-blocking error; stderr shown to user and debug log
- Hooks fire automatically; the user does not invoke them directly
- Hooks defined in skill/agent frontmatter are scoped to that component's lifetime and cleaned up automatically when it finishes
- `PostToolUse` hooks can replace tool output for all tools via `hookSpecificOutput.updatedToolOutput` (v2.1.121+)
- `PostToolUse` and `PostToolUseFailure` hook inputs include `duration_ms` for tool execution time (v2.1.119+)
- `UserPromptSubmit` hooks can set the session title via `hookSpecificOutput.sessionTitle` (v2.1.122+)
- All hooks receive the active effort level via `effort.level` in the hook input JSON and `$CLAUDE_EFFORT` environment variable (v2.1.119+)

## Advanced
- Hook event categories: session lifecycle, per-turn prompts, tool execution, permissions, file/config changes, context compaction, worktrees, tasks, subagents, MCP elicitation, notifications
- Session lifecycle events: `SessionStart`, `Setup`, `SessionEnd`
- `SessionStart` matchers: `startup`, `resume`, `clear`, `compact`
- `Setup` matchers: `init`, `maintenance`; fires only with `--init-only`, `--init` in `-p`, or `--maintenance` in `-p`
- `SessionEnd` matchers: `clear`, `resume`, `logout`, `prompt_input_exit`, `bypass_permissions_disabled`, `other`
- Per-turn events: `UserPromptSubmit` (no matcher), `UserPromptExpansion` (matcher: command name), `Stop` (no matcher), `StopFailure` (matcher: error type)
- Tool events: `PreToolUse`, `PostToolUse`, `PostToolUseFailure`, `PostToolBatch`, `PermissionRequest`, `PermissionDenied`
- Tool-event matchers are tool names (`Bash`, `Edit`, `Write`, `Read`, `Glob`, `Grep`, `Agent`, `WebFetch`, `WebSearch`, `AskUserQuestion`, `ExitPlanMode`, MCP tools `mcp__<server>__<tool>`)
- Subagent events: `SubagentStart`, `SubagentStop` (matcher = agent type)
- File/config events: `FileChanged` (matcher = literal filenames pipe-separated, NOT regex), `ConfigChange` (matcher = config source), `CwdChanged` (no matcher), `InstructionsLoaded` (matcher = load reason)
- Compaction events: `PreCompact`, `PostCompact` (matcher: `manual` or `auto`)
- Worktree events: `WorktreeCreate`, `WorktreeRemove` (no matcher); `WorktreeCreate` must return path
- Task events: `TaskCreated`, `TaskCompleted` (no matcher)
- MCP elicitation events: `Elicitation`, `ElicitationResult` (matcher = MCP server name)
- Other events: `Notification` (matcher = notification type), `TeammateIdle` (no matcher)
- Hook handler types: `command` (shell), `http` (POST to URL), `mcp_tool` (call connected MCP server), `prompt` (single-turn Claude eval), `agent` (subagent verification, experimental)
- `command` hooks support `shell: bash` (default) or `shell: powershell`
- `http` hooks send JSON via POST; non-2xx, timeout, or connection failure is a non-blocking error
- `http` hook headers can interpolate `$VAR` only if the var name is listed in `allowedEnvVars`
- `mcp_tool` hooks support `${path}` substitution from the hook input JSON; require the MCP server to be already connected
- `prompt` hooks default to a fast model with 30 s timeout; `agent` hooks default to 60 s
- Matcher pattern rules: `*` / `""` / omitted = match all; alphanumeric/underscore/pipe-only = exact or pipe-separated list; anything else = JavaScript regex
- `if` field on a handler narrows further within a matcher (e.g., `if: "Bash(git *)"`); only Bash arg-form parsing is fully supported
- Hook handler options: `type`, `if`, `timeout`, `statusMessage`, `once` (only honored in skill frontmatter), `async`, `asyncRewake`, `command`/`url`/`server`/`tool`/`prompt`
- Common stdin fields on every event: `session_id`, `transcript_path`, `cwd`, `permission_mode`, `hook_event_name`; subagent context adds `agent_id`, `agent_type`; all hooks include `effort.level` (v2.1.119+)
- Exit code 2 supported (blocking) by: `PreToolUse`, `PermissionRequest`, `UserPromptSubmit`, `UserPromptExpansion`, `Stop`, `SubagentStop`, `TeammateIdle`, `TaskCreated`, `TaskCompleted`, `ConfigChange` (except `policy_settings`), `PostToolBatch`, `PreCompact`, `WorktreeCreate`
- `PreToolUse` decision: `hookSpecificOutput.permissionDecision` of `allow` / `deny` / `ask` / `defer` plus `permissionDecisionReason`; precedence across multiple hooks is `deny > defer > ask > allow`
- `PreToolUse` and `PermissionRequest` can return `updatedInput` to modify the tool's arguments before execution
- `defer` permission decision requires Claude Code v2.1.89+ and only works in `-p` mode with a single tool call
- Top-level JSON output keys: `continue`, `stopReason`, `suppressOutput`, `systemMessage`, `decision`, `reason`, `hookSpecificOutput`
- Hook stdout context injection capped at 10,000 characters per call
- Settings priority for hooks: managed policy > local (`settings.local.json`) > project (`settings.json`) > user (`~/.claude/settings.json`); plugin hooks merge in alongside
- `allowManagedHooksOnly` policy blocks user/project/plugin hooks (force-enabled plugins exempt)
- `disableAllHooks: true` in any settings file disables all hooks for that scope
- Plugin hook config lives in `hooks/hooks.json`; supports an optional top-level `description`
- Skill/agent frontmatter `hooks:` field: same JSON shape, scoped to component lifetime; supports `once: true` (only honored here)
- For agent frontmatter, `Stop` hooks auto-convert to `SubagentStop` at runtime
- Provided env vars: `CLAUDE_PROJECT_DIR`, `CLAUDE_PLUGIN_ROOT`, `CLAUDE_PLUGIN_DATA`, `CLAUDE_CODE_REMOTE`
- `CLAUDE_ENV_FILE` is exposed only to `SessionStart`, `Setup`, `CwdChanged`, `FileChanged` for persisting env vars across the rest of the session

## Recommended
- Use `PreToolUse` (not `PostToolUse`) to block dangerous tool calls — `PostToolUse` runs after the tool already executed
- Use `if: "Bash(<pattern>)"` to narrow Bash hooks to specific command shapes rather than matching every Bash invocation
- Parse stdin JSON with `jq` and quote results to avoid command injection
- Use `CLAUDE_PROJECT_DIR` (quoted) inside hook commands to address paths in the user's project regardless of the hook script's working directory
- Use `CLAUDE_PLUGIN_ROOT` for hook scripts bundled in a plugin
- Persist short-lived environment variables across the session by writing `export FOO=bar` to `$CLAUDE_ENV_FILE` from `SessionStart` / `Setup` / `CwdChanged` / `FileChanged`
- Use `mcp_tool` hook type when delegating validation to an existing MCP server's tool, with `${tool_input.<field>}` substitution
- Use `prompt` hook type for cheap LLM yes/no judgments where deterministic shell logic would be brittle
- Use HTTP hooks with `allowedEnvVars` to inject only the specific tokens needed (avoid leaking unrelated env)
- Use `disableAllHooks: true` in `settings.local.json` to opt out per-developer when project hooks are too noisy
- Skill-scoped hooks (frontmatter) are best for validation that should only apply while a specific skill is active
- For destructive command guards, return `permissionDecision: "deny"` with a clear `permissionDecisionReason` instead of just exiting non-zero
- For permission UX nudges, return `permissionDecision: "ask"` with a reason
- Use `additionalContext` in `hookSpecificOutput` rather than plain stdout for `SessionStart` / `UserPromptSubmit` to ensure context is reliably attached
- For long-running side effects, use `async: true` (or `asyncRewake: true` to rewake Claude on completion)
- Define each conditional separately rather than trying to cram multiple conditions into a single matcher or `if`

## Anti-patterns
- Hooks cannot block events that do not support exit code 2: `PostToolUse`, `PostToolUseFailure`, `StopFailure`, `SessionEnd`, `Notification`, `SubagentStart`, `WorktreeRemove`, `PostCompact`, `FileChanged`, `CwdChanged`, `InstructionsLoaded`
- Hooks cannot block `ConfigChange` matched on `policy_settings` (admin policy supersedes hooks)
- Hook `permissionDecision: "allow"` does NOT override deny rules in `permissions`; deny still wins
- `defer` permission decision fails for batches with more than one tool call; only single-tool batches support deferral
- `FileChanged` matcher is NOT a regex — `*.env` does not match anything; only literal filenames pipe-separated work
- `if` arg-form parsing is implemented for Bash; for other tools the condition may always match because the argument shape can't be parsed
- `once: true` is silently ignored in `settings.json` and in agent frontmatter; only skill frontmatter honors it
- Hook stdout exceeding 10,000 characters is truncated; do not rely on long-form output to inject context
- `mcp_tool` hooks fail (non-blocking error) if invoked from `SessionStart` / `Setup` before the MCP server has connected
- Do not eval or shell-interpolate `tool_input` fields directly — `jq -r` and quoting are mandatory to avoid injection
- HTTP hooks cannot block by HTTP status alone; status must be 2xx and the JSON body must carry the decision
- Top-level `decision` / `reason` fields on `PreToolUse` are deprecated in favor of `hookSpecificOutput.permissionDecision`
- Hooks cannot change `permissionMode` mid-session; mode is set on the CLI or in settings only
- Hooks run non-interactively; they cannot prompt the user for input on their own (use `permissionDecision: "ask"` for permission, or rely on the `AskUserQuestion` tool flow elsewhere)
- Each hook invocation is isolated; do not assume in-process state persists across firings
