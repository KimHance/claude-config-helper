# Hooks Template

## hooks.json Structure

```json
{
  "hooks": [
    {
      "event": "PreToolUse",
      "matcher": "ToolName",
      "command": "./hooks/script-name"
    },
    {
      "event": "PostToolUse",
      "matcher": "ToolName",
      "command": "./hooks/script-name"
    }
  ]
}
```

## Valid Events

| Event | When | Blocking |
|-------|------|----------|
| `PreToolUse` | Before a tool executes | Yes — non-zero exit blocks the tool |
| `PostToolUse` | After a tool executes | No |
| `Notification` | On notifications | No |
| `Stop` | When agent stops | No |
| `SubagentStop` | When subagent stops | No |

## Hook Script Template

```bash
#!/bin/bash
# Hook: description of what this does
# Event: PreToolUse/PostToolUse
# Matcher: ToolName

# Input is passed via stdin as JSON
input=$(cat)

# Your logic here

# For PreToolUse: exit 0 to allow, exit non-zero to block
exit 0
```

## Best Practices

- Make scripts executable: `chmod +x hooks/script-name`
- Use specific matchers, not broad patterns
- Keep PreToolUse hooks fast (they block execution)
- Put heavy operations in PostToolUse hooks
- No secrets in hook scripts
