# MCP Server Configuration Review Checklist

## File Locations
- `.mcp.json` — project-level MCP config
- `~/.claude/mcp.json` — user-level MCP config

## Server Configuration
- [ ] Each server entry has valid `command` and `args`
- [ ] Server commands point to existing executables
- [ ] Environment variables (`env`) don't contain hardcoded secrets (use references)

## Tool Naming
- [ ] No duplicate tool names across different MCP servers
- [ ] Tool names follow a clear naming convention (e.g., `mcp__<server>__<action>`)
- [ ] No conflicting tools that do the same thing from different servers

## Scoping
- [ ] Project-level MCP config only includes servers relevant to the project
- [ ] User-level MCP config contains personal/global servers
- [ ] No project-specific servers in user-level config (portability issue)

## Security
- [ ] API keys and tokens are in environment variables, not hardcoded
- [ ] Servers with write access are appropriately restricted
- [ ] No unnecessary servers running (attack surface)

## Connectivity
- [ ] Server processes can be started without errors
- [ ] Required dependencies (npm packages, Python modules) are installed
