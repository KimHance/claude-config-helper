# Hooks Review Checklist

## Hook Configuration
- [ ] Valid JSON format in settings file or frontmatter
- [ ] Configured in correct location (`~/.claude/settings.json`, `.claude/settings.json`, `.claude/settings.local.json`, managed policy, or plugin `hooks/hooks.json`)
- [ ] Each hook has: `event` and a handler (`command`, `url`, `prompt`, `agent`, or `mcp_tool`)

## Hook Type Validation
- [ ] `command` hooks: `command` field is a valid shell command or script path
- [ ] `http` hooks: `url` field is a valid endpoint; URL is in `allowedHttpHookUrls` if managed
- [ ] `prompt` hooks: `prompt` field contains clear single-turn evaluation instructions
- [ ] `agent` hooks: `agent` field specifies valid subagent with appropriate tools
- [ ] `mcp_tool` hooks: `server` and `tool` fields are set; `input` uses `${path}` substitution from hook input (v2.1.118+)

## Events
- [ ] Events are valid. Full list:
  - Session: `SessionStart`, `SessionEnd`
  - User: `UserPromptSubmit`, `UserPromptExpansion`
  - Tool: `PreToolUse`, `PostToolUse`, `PostToolBatch`, `PostToolUseFailure`, `PermissionRequest`, `PermissionDenied`
  - Agent: `SubagentStart`, `SubagentStop`, `Stop`, `StopFailure`
  - Task: `TaskCreated`, `TaskCompleted`
  - Notification: `Notification`, `TeammateIdle`
  - Config: `InstructionsLoaded`, `ConfigChange`
  - File/Dir: `CwdChanged`, `FileChanged`
  - Worktree: `WorktreeCreate`, `WorktreeRemove`
  - Compaction: `PreCompact`, `PostCompact`
  - MCP: `Elicitation`, `ElicitationResult`
- [ ] Blocking events (`PreToolUse`, `UserPromptSubmit`, `UserPromptExpansion`, `PermissionRequest`, `PostToolUse`, `PostToolBatch`, `SubagentStop`, `Stop`, `TaskCreated`, `TaskCompleted`, `TeammateIdle`, `ConfigChange`, `PreCompact`, `Elicitation`, `ElicitationResult`) used appropriately
- [ ] `PostToolUse` and `PostToolUseFailure` hook inputs include `duration_ms` (tool execution time in ms) — use for performance monitoring hooks (v2.1.119+)
- [ ] `PreCompact` blocking: exit code 2 OR JSON `{"decision":"block"}` with exit 0 (as of v2.1.113)
- [ ] `PreCompact` matcher (if used) is `"manual"` or `"auto"` to target user-initiated vs automatic compaction
- [ ] `PermissionRequest` hooks returning `updatedInput`: the modified input is **re-checked against deny/ask rules** — an allow decision does not bypass deny rules (as of v2.1.113)

## Optional Fields
- [ ] `matcher` — regex is specific, not overly broad
- [ ] `if` — permission rule syntax filter is correct (if used)
- [ ] `timeout` — reasonable timeout set for slow hooks
- [ ] `statusMessage` — user-facing message is clear (if used)
- [ ] `once` — set to `true` only for one-time hooks (if used)
- [ ] `async` — set to `true` only for non-blocking background hooks (if used)
- [ ] `asyncRewake` — wakes Claude when async command exits with code 2 (stderr shown); use with `async: true` (if used)
- [ ] `shell` — set to `bash` (default) or `powershell` for command hooks targeting Windows environments (if used)

## Command Hook Scripts
- [ ] Referenced scripts exist at the specified paths
- [ ] Scripts are executable (`chmod +x`)
- [ ] Exit codes are correct: 0 = success, 2 = blocking error, other = non-blocking error
- [ ] Scripts read JSON from stdin correctly

## Matchers
- [ ] Matchers are specific (not matching every tool call)
- [ ] No overly broad patterns that slow down every operation
- [ ] Regex patterns are valid and tested

## Performance
- [ ] Blocking hooks (`PreToolUse`, `UserPromptSubmit`, `PermissionRequest`) execute quickly
- [ ] No network calls in synchronous command hooks
- [ ] Heavy operations use `PostToolUse` or `async: true`
- [ ] `prompt`/`agent` hooks reserved for checks that warrant LLM evaluation

## Security
- [ ] No sensitive data (tokens, passwords) in hook scripts or prompts
- [ ] No destructive operations without confirmation
- [ ] HTTP hook URLs use HTTPS
- [ ] `httpHookAllowedEnvVars` restricts which env vars are sent to HTTP hooks

## Hooks in Skills/Agents
- [ ] Frontmatter hooks use valid event names
- [ ] Hooks are scoped to the component lifecycle (active only while skill/agent runs)
- [ ] `Stop` hooks in subagents are correctly converted to `SubagentStop`

## Managed Hooks
- [ ] `allowManagedHooksOnly` — if set in managed policy, verify plugin hooks from force-enabled plugins still run as intended (expected behavior since v2.1.101)
- [ ] Unrecognized hook event names in `settings.json` are gracefully ignored (no longer crash the entire file since v2.1.101); remove any stale/typo event names to keep config clean

## Environment Variables
- [ ] Scripts use `$CLAUDE_PROJECT_DIR` for project root (not hardcoded paths)
- [ ] `SessionStart`/`CwdChanged`/`FileChanged` hooks use `CLAUDE_ENV_FILE` for persisting env vars (if needed)
- [ ] Plugin hooks use `${CLAUDE_PLUGIN_ROOT}` and `${CLAUDE_PLUGIN_DATA}` (if applicable)
