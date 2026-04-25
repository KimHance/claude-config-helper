# Hooks Template

## Hook Types

Hooks can be defined as one of five types:

### 1. Command Hook (shell script)

```json
{
  "hooks": [
    {
      "type": "command",
      "event": "PreToolUse",
      "matcher": "Bash",
      "command": "./hooks/check-bash.sh"
    }
  ]
}
```

### 2. HTTP Hook (webhook endpoint)

```json
{
  "hooks": [
    {
      "type": "http",
      "event": "PostToolUse",
      "matcher": "Write",
      "url": "https://your-endpoint.com/hook"
    }
  ]
}
```

### 3. Prompt Hook (single-turn LLM evaluation)

```json
{
  "hooks": [
    {
      "type": "prompt",
      "event": "PreToolUse",
      "matcher": "Bash",
      "prompt": "Review this bash command for safety. Block if it could delete files or modify system config."
    }
  ]
}
```

### 4. Agent Hook (subagent with tools)

```json
{
  "hooks": [
    {
      "type": "agent",
      "event": "Stop",
      "agent": "Run the test suite and verify all tests pass before allowing completion."
    }
  ]
}
```

### 5. MCP Tool Hook (call MCP server tool directly)

```json
{
  "hooks": [
    {
      "type": "mcp_tool",
      "event": "PreToolUse",
      "matcher": "Edit|Write",
      "server": "security-scanner",
      "tool": "scan_file",
      "input": {
        "file_path": "${tool_input.file_path}"
      }
    }
  ]
}
```

`input` values support `${path}` substitution from the hook event payload. Text output from the tool is treated like command-hook stdout. Non-blocking if the MCP server is not connected. (v2.1.118+)

## Configuration Locations

| Location | Scope |
|---|---|
| `~/.claude/settings.json` | All projects |
| `.claude/settings.json` | Single project (committable) |
| `.claude/settings.local.json` | Single project (gitignored) |
| Managed policy settings | Organization-wide |
| Plugin `hooks/hooks.json` | When plugin enabled |
| Skill/agent frontmatter | While component active |

## Valid Events

| Event | When | Can Block |
|---|---|---|
| `SessionStart` | Session begins or resumes | No |
| `SessionEnd` | Session terminates | No |
| `UserPromptSubmit` | User submits a prompt | Yes |
| `UserPromptExpansion` | Slash command expands | Yes |
| `PreToolUse` | Before tool executes | Yes |
| `PostToolUse` | After tool succeeds | Yes |
| `PostToolUseFailure` | After tool fails | No |
| `PostToolBatch` | Batch of parallel tools resolves | Yes |
| `PermissionRequest` | Permission dialog appears | Yes |
| `PermissionDenied` | Auto mode denies tool call | No |
| `SubagentStart` | Subagent spawned | No |
| `SubagentStop` | Subagent finishes | Yes |
| `Stop` | Claude finishes responding | Yes |
| `StopFailure` | Turn ends due to API error | No |
| `TaskCreated` | Task created via TaskCreate | Yes |
| `TaskCompleted` | Task completed | Yes |
| `Notification` | Notification sent | No |
| `TeammateIdle` | Teammate going idle | Yes |
| `InstructionsLoaded` | CLAUDE.md or rules loaded | No |
| `ConfigChange` | Config file changes | Yes |
| `CwdChanged` | Working directory changes | No |
| `FileChanged` | Watched file changes | No |
| `WorktreeCreate` | Worktree created | Yes (any non-zero exit aborts creation) |
| `WorktreeRemove` | Worktree removed | No |
| `PreCompact` | Before compaction | Yes (exit code 2, or `{"decision":"block"}` with exit 0) |
| `PostCompact` | After compaction | No |
| `Elicitation` | MCP server requests user input | Yes |
| `ElicitationResult` | User responds to elicitation | Yes |

## Optional Fields

| Field | Description |
|---|---|
| `matcher` | Regex to filter when hook fires (tool name, source, etc.). For `PreCompact`: use `"manual"` or `"auto"` to target user-initiated vs automatic compaction |
| `if` | Permission rule syntax filter |
| `timeout` | Timeout in milliseconds |
| `statusMessage` | User-facing status message |
| `once` | `true` to run only once per session |
| `async` | `true` to run in background (non-blocking) |
| `asyncRewake` | With `async: true`: wake Claude on exit code 2 with stderr shown |
| `shell` | For command hooks: `bash` (default) or `powershell` |

## Command Hook Script Template

```bash
#!/bin/bash
# Hook: description of what this does
# Event: PreToolUse/PostToolUse
# Matcher: ToolName

# Input is passed via stdin as JSON
input=$(cat)

# Your logic here

# Exit codes:
#   0 = success (stdout parsed for JSON)
#   2 = blocking error (blocks tool call / rejects prompt)
#   other = non-blocking error (logged but does not block)
exit 0
```

### JSON Output Fields (stdout)

```json
{
  "continue": true,
  "stopReason": "optional reason to stop",
  "suppressOutput": false,
  "systemMessage": "optional message injected into context"
}
```

### Decision Control (PreToolUse)

```json
{
  "hookSpecificOutput": {
    "permissionDecision": "allow",
    "updatedInput": {},
    "additionalContext": "extra context for Claude"
  }
}
```

## PostToolUse / PostToolUseFailure Inputs

Both events receive additional fields beyond the standard tool input/output:

| Field | Description |
|---|---|
| `tool_response` | Tool execution result |
| `tool_use_id` | Unique tool use identifier |
| `duration_ms` | Tool execution time in milliseconds (v2.1.119+) |

## Hooks in Skill/Agent Frontmatter

```yaml
---
name: my-skill
hooks:
  - event: Stop
    type: command
    command: "./scripts/verify.sh"
---
```

Frontmatter hooks are scoped to the component lifecycle — active only while the skill/agent runs.

## Environment Variables

| Variable | Available In | Purpose |
|---|---|---|
| `$CLAUDE_PROJECT_DIR` | All hooks | Project root directory |
| `${CLAUDE_PLUGIN_ROOT}` | Plugin hooks | Plugin installation directory |
| `${CLAUDE_PLUGIN_DATA}` | Plugin hooks | Plugin persistent data directory |
| `CLAUDE_ENV_FILE` | `SessionStart`, `CwdChanged`, `FileChanged` | Path to write persistent env vars |

## Best Practices

- Make command scripts executable: `chmod +x hooks/script-name`
- Use specific matchers, not broad patterns
- Keep blocking hooks (`PreToolUse`, `UserPromptSubmit`, `PermissionRequest`) fast
- Use `async: true` or `PostToolUse` for heavy operations
- Use `prompt` hooks for safety checks that need LLM judgment
- Use `agent` hooks for complex validations needing file system access
- No secrets in hook scripts — use environment variables
- Use HTTPS for HTTP hook URLs
