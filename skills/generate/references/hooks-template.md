# Hooks Template

## Hook Types

Hooks can be defined as one of four types:

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
| `PreToolUse` | Before tool executes | Yes |
| `PostToolUse` | After tool succeeds | No |
| `PostToolUseFailure` | After tool fails | No |
| `PermissionRequest` | Permission dialog appears | Yes |
| `SubagentStart` | Subagent spawned | No |
| `SubagentStop` | Subagent finishes | No |
| `Stop` | Claude finishes responding | No |
| `StopFailure` | Turn ends due to API error | No |
| `TaskCreated` | Task created via TaskCreate | No |
| `TaskCompleted` | Task completed | No |
| `Notification` | Notification sent | No |
| `TeammateIdle` | Teammate going idle | No |
| `InstructionsLoaded` | CLAUDE.md or rules loaded | No |
| `ConfigChange` | Config file changes | No |
| `CwdChanged` | Working directory changes | No |
| `FileChanged` | Watched file changes | No |
| `WorktreeCreate` | Worktree created | No |
| `WorktreeRemove` | Worktree removed | No |
| `PreCompact` | Before compaction | No |
| `PostCompact` | After compaction | No |
| `Elicitation` | MCP server requests user input | No |
| `ElicitationResult` | User responds to elicitation | No |

## Optional Fields

| Field | Description |
|---|---|
| `matcher` | Regex to filter when hook fires (tool name, source, etc.) |
| `if` | Permission rule syntax filter |
| `timeout` | Timeout in milliseconds |
| `statusMessage` | User-facing status message |
| `once` | `true` to run only once per session |
| `async` | `true` to run in background (non-blocking) |

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
