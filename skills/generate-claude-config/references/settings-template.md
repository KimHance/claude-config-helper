# Settings Template

## settings.json Structure

```json
{
  "permissions": {
    "allow": [
      "ToolName(pattern)",
      "Bash(specific-command:*)",
      "mcp__server__tool_name"
    ]
  },
  "enabledPlugins": {
    "plugin-name@marketplace-name": true
  },
  "extraKnownMarketplaces": {
    "marketplace-name": {
      "source": {
        "source": "github",
        "repo": "owner/repo"
      }
    }
  }
}
```

## File Locations

| File | Scope | Synced |
|------|-------|--------|
| `~/.claude/settings.json` | User-level | Yes |
| `~/.claude/settings.local.json` | User-level | No |
| `.claude/settings.json` | Project-level | Yes (committed) |
| `.claude/settings.local.json` | Project-level | No |

## Best Practices

- Scope permissions narrowly: `Bash(npm test:*)` not `Bash(*)`
- Put machine-specific paths in `.local.json`
- Never store secrets in settings files
- Keep project settings minimal — only project-specific overrides
- User-level settings for personal preferences and global plugins
