# MCP Server Configuration Review Checklist

## File Locations & Scopes
- [ ] Correct file used for each scope:
  - `~/.claude.json` — local scope (default, private, current project)
  - `.mcp.json` — project scope (team-shared, version controlled)
  - `~/.claude.json` — user scope (cross-project, private)
- [ ] Precedence understood: local > project > user

## Transport Type
- [ ] HTTP transport used where possible (recommended)
- [ ] SSE transport flagged as deprecated — migrate to HTTP
- [ ] Stdio transport used only for local tools that require it

## Server Configuration
- [ ] Each server entry has valid connection config:
  - HTTP: valid `url`
  - SSE: valid `url` (deprecated)
  - Stdio: valid `command` and `args`
- [ ] Server commands point to existing executables (stdio)
- [ ] Environment variables use `${VAR}` or `${VAR:-default}` expansion syntax
- [ ] No hardcoded secrets — use `${VAR}` references in `env`, `url`, `args`, `headers`

## Authentication
- [ ] OAuth 2.0 configured correctly (if used)
- [ ] `headersHelper` used for dynamic non-OAuth auth (if applicable)
- [ ] Pre-configured credentials (`--client-id`, `--client-secret`) stored securely

## Tool Naming
- [ ] No duplicate tool names across different MCP servers
- [ ] Tool names follow convention: `mcp__<server>__<action>`
- [ ] No conflicting tools that do the same thing from different servers

## MCP Tool Search
- [ ] Tool search enabled (default) — tools deferred until needed
- [ ] `ENABLE_TOOL_SEARCH` not set to `false` unless there's a specific reason

## Scoping
- [ ] Project-level (`.mcp.json`) only includes servers relevant to the project
- [ ] User-level config contains personal/global servers
- [ ] No project-specific servers in user-level config (portability issue)

## Managed MCP (if applicable)
- [ ] `managed-mcp.json` used for organization-wide servers (macOS: `/Library/Application Support/ClaudeCode/`, Linux: `/etc/claude-code/`)
- [ ] `allowedMcpServers` / `deniedMcpServers` policies configured correctly
- [ ] Policy matching uses correct fields: `serverName`, `serverCommand`, `serverUrl`

## Plugin-Provided MCP Servers (if applicable)
- [ ] Plugin MCP servers defined in `.mcp.json` at plugin root or inline in `plugin.json`
- [ ] Auto-connect behavior verified when plugin is enabled

## Security
- [ ] API keys and tokens in environment variables via `${VAR}` syntax, not hardcoded
- [ ] Servers with write access are appropriately restricted
- [ ] No unnecessary servers running (attack surface + startup latency)
- [ ] HTTP/SSE URLs use HTTPS

## Connectivity
- [ ] Server processes can be started without errors
- [ ] Required dependencies (npm packages, Python modules) are installed
