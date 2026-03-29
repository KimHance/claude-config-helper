# MCP Configuration Template

## Transport Types

### HTTP (recommended)

```bash
claude mcp add --transport http server-name https://api.example.com/mcp
```

### Stdio (local tools)

```json
{
  "mcpServers": {
    "server-name": {
      "command": "npx",
      "args": ["-y", "package-name"],
      "env": {
        "API_KEY": "${API_KEY}"
      }
    }
  }
}
```

### SSE (deprecated — migrate to HTTP)

```bash
claude mcp add --transport sse server-name https://api.example.com/sse
```

## File Locations & Scopes

| Scope | Storage | Purpose | Precedence |
|---|---|---|---|
| Local (default) | `~/.claude.json` | Private, current project | Highest |
| Project | `.mcp.json` in project root | Team-shared (version control) | Middle |
| User | `~/.claude.json` | Cross-project, private | Lowest |

## Environment Variable Expansion

Use `${VAR}` syntax in `command`, `args`, `env`, `url`, and `headers` fields:

```json
{
  "mcpServers": {
    "my-api": {
      "command": "npx",
      "args": ["-y", "@example/mcp-server"],
      "env": {
        "API_KEY": "${MY_API_KEY}",
        "BASE_URL": "${API_URL:-https://api.example.com}"
      }
    }
  }
}
```

`${VAR:-default}` provides a fallback value if the variable is unset.

## Authentication

### OAuth 2.0

```bash
claude mcp add --transport http my-server https://api.example.com/mcp
# Then authenticate:
# /mcp → select server → authenticate
```

### Pre-configured OAuth

```bash
claude mcp add --transport http my-server https://api.example.com/mcp \
  --client-id MY_CLIENT_ID \
  --client-secret MY_CLIENT_SECRET \
  --callback-port 8080
```

### Dynamic auth with headersHelper

```json
{
  "mcpServers": {
    "my-server": {
      "url": "https://api.example.com/mcp",
      "headersHelper": "./scripts/get-auth-headers.sh"
    }
  }
}
```

## Managed MCP (organization-wide)

For `managed-mcp.json` at system paths (macOS: `/Library/Application Support/ClaudeCode/`, Linux: `/etc/claude-code/`):

```json
{
  "mcpServers": {
    "internal-tools": {
      "url": "https://internal.company.com/mcp"
    }
  }
}
```

Policy-based control in managed settings:

```json
{
  "allowedMcpServers": [
    { "serverName": "approved-*" },
    { "serverUrl": "https://*.company.com/*" }
  ],
  "deniedMcpServers": [
    { "serverName": "untrusted-*" }
  ]
}
```

## CLI Commands

```bash
# Add server
claude mcp add [--transport http|sse|stdio] [--scope local|project|user] [--env KEY=VAL] <name> <url-or-command> [args...]

# List servers
claude mcp list

# Remove server
claude mcp remove <name>

# Authenticate (interactive)
# /mcp → select server

# Run Claude Code as MCP server
claude mcp serve
```

## Best Practices

- Prefer HTTP transport over SSE (deprecated) or stdio
- Use `${VAR}` syntax for secrets, never hardcode
- Project-level (`.mcp.json`) for project-specific servers only
- User-level for personal/global servers (GitHub, Notion, etc.)
- Avoid duplicate tool names across servers
- Keep server count minimal — each adds startup latency
- Use HTTPS for all remote URLs
- Leave MCP Tool Search enabled (default) for efficient tool loading
