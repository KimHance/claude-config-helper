# Hooks Review Checklist

## hooks.json
- [ ] Valid JSON format
- [ ] Each hook has: `event`, `command`, and optionally `matcher`
- [ ] Events are valid: `PreToolUse`, `PostToolUse`, `Notification`, `Stop`, `SubagentStop`

## Hook Scripts
- [ ] Referenced scripts exist at the specified paths
- [ ] Scripts are executable (`chmod +x`)
- [ ] Scripts handle errors gracefully (non-zero exit = block the action)

## Matchers
- [ ] Matchers are specific (not matching every tool call)
- [ ] No overly broad patterns that slow down every operation
- [ ] Regex patterns are valid and tested

## Performance
- [ ] Hook scripts execute quickly (blocking hooks delay tool execution)
- [ ] No network calls in synchronous hooks
- [ ] Heavy operations are in PostToolUse (non-blocking) rather than PreToolUse (blocking)

## Security
- [ ] No sensitive data (tokens, passwords) in hook scripts
- [ ] No destructive operations without confirmation
