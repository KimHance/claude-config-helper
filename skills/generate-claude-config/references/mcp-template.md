# MCP Configuration Template

## .mcp.json Structure

```json
{
  "mcpServers": {
    "server-name": {
      "command": "npx",
      "args": ["-y", "package-name"],
      "env": {
        "API_KEY": "env:VARIABLE_NAME"
      }
    }
  }
}
```

## File Locations

| File | Scope |
|------|-------|
| `.mcp.json` | Project-level |
| `~/.claude/mcp.json` | User-level (global) |

## Best Practices

- Use `env:VARIABLE_NAME` syntax for secrets, never hardcode
- Project-level config for project-specific servers only
- User-level config for personal/global servers (GitHub, Notion, etc.)
- Avoid duplicate tool names across servers
- Keep server count minimal — each adds latency at startup
