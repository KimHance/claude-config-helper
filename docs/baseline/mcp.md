# mcp

> This file is a cchelp review baseline authored by the maintainer.
> The weekly workflow compares each section against the official Claude docs and rewrites only the sections whose **meaning** has drifted.
> Update granularity = a single section (one `##` heading). If the meaning is unchanged, the section is left byte-for-byte intact — no rewording, no reordering.

## Fundamentals
- MCP (Model Context Protocol) is an open standard that lets Claude Code connect to external tools, databases, and APIs through MCP servers
- An MCP server exposes tools, prompts, and resources to Claude Code; tools become callable, prompts become slash commands, resources become `@` mentions
- MCP servers connect via one of three transports: `stdio` (local process), `http` (remote, recommended), or `sse` (deprecated, use http)
- Three install methods: CLI (`claude mcp add`), `.mcp.json` file, or `claude mcp add-json` for raw JSON
- Three install scopes: `local` (default, single project, private, stored in `~/.claude.json`), `project` (single project, shared via `.mcp.json` in repo root), `user` (all projects, private, stored in `~/.claude.json`)
- MCP tools appear to Claude as `mcp__<server>__<tool>` and are subject to the same permission system as built-in tools
- The `/mcp` slash command opens a panel that lists configured servers, their connection state, tool counts, and supports OAuth login / clearing auth / retry
- The CLI surface is `claude mcp add`, `claude mcp add-json`, `claude mcp add-from-claude-desktop`, `claude mcp list`, `claude mcp get <name>`, `claude mcp remove <name>`, and `claude mcp serve`
- The reserved server name is `workspace` — defining a server with that name causes Claude Code to skip it at load time and warn

## Advanced
- `claude mcp add --transport http <name> <url>` adds a remote HTTP server; supports `--header "K: V"` (repeatable), `--scope`, `--callback-port`, `--client-id`, `--client-secret`
- `claude mcp add --transport sse <name> <url>` is deprecated; HTTP transport is preferred
- `claude mcp add --transport stdio <name> -- <cmd> [args...]` adds a local stdio server; everything before `--` is options, everything after is the command and its args
- `--env KEY=value` is repeatable and must come before the server name; `--scope local|project|user` selects scope
- `claude mcp add-json <name> '<json>'` accepts a raw server config JSON; supports `--client-secret` for HTTP/SSE OAuth credentials
- `claude mcp add-from-claude-desktop` imports configured servers from Claude Desktop (macOS / WSL only); duplicate names get numerical suffix
- `claude mcp serve` runs Claude Code itself as a stdio MCP server so other clients (Claude Desktop, etc.) can use Claude's tools
- `.mcp.json` schema: `{ "mcpServers": { "<name>": { "type": "stdio|http|sse", ... } } }`
- stdio entry fields: `command`, `args`, `env`
- http/sse entry fields: `type`, `url`, `headers`, `oauth`, `headersHelper`, `alwaysLoad`
- `oauth` object fields: `clientId`, `clientSecret` (use `--client-secret` flag, not in JSON), `callbackPort`, `authServerMetadataUrl` (v2.1.64+), `scopes` (space-separated string, RFC 6749)
- Environment variable expansion in `.mcp.json`: `${VAR}` and `${VAR:-default}` work in `command`, `args`, `env`, `url`, `headers`
- Required env vars without defaults cause config parse failure
- Scope precedence (highest to lowest): local > project > user > plugin servers > claude.ai connectors
- Scopes match by name; plugins/connectors match by endpoint (URL or command), so a duplicate endpoint is suppressed
- Project-scoped servers in `.mcp.json` require user approval before use; reset with `claude mcp reset-project-choices`
- Plugin-bundled MCP servers live in plugin's `.mcp.json` or inline in `plugin.json`; use `${CLAUDE_PLUGIN_ROOT}` for bundled files and `${CLAUDE_PLUGIN_DATA}` for persistent state
- Plugin servers start when plugin is enabled; `/reload-plugins` refreshes after enable/disable mid-session
- claude.ai connectors are auto-shared if logged in with claude.ai account; disable with `ENABLE_CLAUDEAI_MCP_SERVERS=false`
- Servers added in Claude Code take precedence over a claude.ai connector pointing at the same URL
- OAuth flow: add server → run `/mcp` → browser login → tokens stored in macOS keychain or credentials file (not in config)
- For servers without dynamic client registration, register an OAuth app first then pass `--client-id` and `--client-secret`
- `--callback-port <PORT>` fixes the OAuth callback port for servers requiring a pre-registered redirect URI (`http://localhost:PORT/callback`)
- `MCP_CLIENT_SECRET` env var supplies the secret in CI / non-interactive contexts
- `headersHelper` field runs an arbitrary shell command at connection time and merges its JSON output into request headers; 10 s timeout, runs fresh on each connection
- `headersHelper` env vars: `CLAUDE_CODE_MCP_SERVER_NAME`, `CLAUDE_CODE_MCP_SERVER_URL`
- Project-scoped or local-scoped `headersHelper` runs only after the workspace trust dialog is accepted
- Reconnection: HTTP/SSE servers reconnect with exponential backoff up to 5 attempts on mid-session disconnect; v2.1.121+ retries initial connection up to 3 times on transient errors
- Authentication errors and 404s are not retried (require config change)
- Stdio servers are not auto-reconnected
- `MCP_TIMEOUT` env var sets startup timeout (e.g. `MCP_TIMEOUT=10000`)
- `MCP_CONNECTION_NONBLOCKING=1` lets other servers connect in background; servers with `alwaysLoad: true` still block startup up to 5 s
- MCP tool output > 10,000 tokens triggers a warning; default cap is 25,000 tokens, raise via `MAX_MCP_OUTPUT_TOKENS`
- Server-side tool authors can set `_meta["anthropic/maxResultSizeChars"]` (up to 500,000) to opt individual tools out of the persist-to-disk threshold for text content
- Image content is always subject to `MAX_MCP_OUTPUT_TOKENS`
- `list_changed` notifications from MCP servers refresh tools/prompts/resources without reconnecting
- Tool Search defers MCP tool definitions until needed; controlled by `ENABLE_TOOL_SEARCH` (`true`/`auto`/`auto:<N>`/`false`/unset)
- Tool Search requires Sonnet 4 / Opus 4 or later (Haiku unsupported); auto-disabled on Vertex AI and non-first-party `ANTHROPIC_BASE_URL`
- Per-server opt-out from Tool Search deferral: set `alwaysLoad: true` on that server (v2.1.121+); per-tool opt-out via `_meta["anthropic/alwaysLoad"]: true`
- MCP prompts surface as `/mcp__<server>__<prompt>` slash commands; arguments are parsed per the prompt's parameter schema
- MCP resources are referenced via `@<server>:<protocol>://<path>` in prompts; auto-fetched and attached
- MCP elicitation requests pop up form-mode or URL-mode dialogs; auto-respond via `Elicitation` hook
- Push messaging: server with `claude/channel` capability + `--channels` flag at startup pushes external events into the session
- Channel push integration is documented separately under Channels and Channels reference
- `mcp__<server>` matches all tools from that server; `mcp__<server>__<tool>` matches a specific tool
- Channel-mode servers, prompt commands, and resources are normalized so that spaces become underscores in identifiers
- Managed MCP option 1 (`managed-mcp.json`): exclusive control, fixed server set, users cannot add their own; locations: macOS `/Library/Application Support/ClaudeCode/managed-mcp.json`, Linux/WSL `/etc/claude-code/managed-mcp.json`, Windows `C:\Program Files\ClaudeCode\managed-mcp.json`
- Managed MCP option 2 (`managedMcpServers` setting): organizations can provision HTTP/SSE servers to all users via managed settings (v2.1.259+); server entries use the same shape as `.mcp.json`; command-based entries are skipped in managed deployment
- Managed MCP option 3: policy-based via `allowedMcpServers` / `deniedMcpServers` in managed settings; entries match by `serverName`, `serverCommand` (exact array), or `serverUrl` (wildcard `*` supported); governs user-added servers only (v2.1.259+)
- Allowlist behavior: undefined = no restriction, `[]` = full lockdown, list = only matching servers allowed
- Denylist behavior: undefined or `[]` = nothing blocked, list = matching servers blocked across all scopes; denylist always takes absolute precedence over allowlist
- Stdio servers must match `serverCommand` if any command entries exist in allowlist; remote servers must match `serverUrl` if any URL entries exist
- URL hostname matching is case-insensitive and trailing-dot-tolerant; paths remain case-sensitive
- Tool descriptions and server instructions are truncated at 2KB each; put critical info first

## Recommended
- Prefer the `http` transport over `sse` (sse is deprecated)
- Use `local` scope (default) for personal/credential-bearing servers; use `project` scope (writes `.mcp.json`) for team-shared servers; use `user` scope for cross-project personal utilities
- Commit `.mcp.json` to version control when servers should be shared with the team; do not commit `~/.claude.json`
- Use `${VAR}` expansion in `.mcp.json` for machine-specific paths and credentials so the same file works across the team
- Use Bearer token via `--header "Authorization: Bearer ..."` for servers using simple token auth; use OAuth flow (`/mcp`) for servers supporting OAuth 2.0
- Use `--callback-port` when the server requires a pre-registered redirect URI; use `--client-id` + `--client-secret` when dynamic client registration is unsupported
- Set `oauth.scopes` to pin the requested scope set when the security team requires it
- Use `headersHelper` for non-OAuth auth schemes (Kerberos, short-lived tokens, internal SSO); the helper writes JSON headers to stdout
- Use `alwaysLoad: true` only for the small set of servers Claude must see on every turn; the rest stay deferred for context savings
- Raise `MAX_MCP_OUTPUT_TOKENS` when working with servers that legitimately produce large outputs (database dumps, long reports)
- Use `claude mcp serve` to expose Claude Code's tools to other MCP clients (e.g., Claude Desktop) for testing or cross-tool workflows
- Reset stale project-scope approvals with `claude mcp reset-project-choices` after updating `.mcp.json`
- For org rollouts, prefer `managed-mcp.json` (Option 1) when a fixed approved set is needed, or allow/denylists (Option 3) when users still need flexibility
- Use URL wildcards (`https://*.internal.corp/*`) in `allowedMcpServers` to allow whole subdomains without listing each server
- For server authors: include clear server instructions (under 2KB) so Tool Search can match user requests; truncation hides anything past the cap

## Anti-patterns
- Do not use `sse` transport for new integrations — it is deprecated; use `http`
- Do not place `--scope` / `--env` / `--header` / `--transport` after the server name on `claude mcp add` — all options must come before `<name>`, and the `--` separator divides options from the server's own command
- Do not name a server `workspace` — Claude Code skips it and warns; this name is reserved
- Do not put `clientSecret` directly in `.mcp.json` — use the `--client-secret` flag so the secret is stored in the keychain / credentials file
- Do not rely on `--callback-port` / `--client-id` for stdio servers — those flags only apply to HTTP and SSE
- Do not assume command-array matching in `serverCommand` allowlists is partial — it is exact, including order and every flag
- Do not assume name-based allowlist alone permits stdio servers when command entries exist — stdio servers must match a `serverCommand` if any are listed
- Do not assume the denylist can be overridden by adding the same server to allowlist — denylist takes absolute precedence
- Do not depend on stdio servers reconnecting automatically after a crash — only HTTP/SSE auto-reconnect
- Do not skip the OAuth `/mcp` step after adding a server that requires authentication — server stays unauthenticated otherwise
- Do not embed long server instructions or tool descriptions over 2KB — they are truncated by Tool Search
- Do not assume `MAX_MCP_OUTPUT_TOKENS` overrides per-tool `anthropic/maxResultSizeChars` — the per-tool annotation wins for text content
- Do not invoke `mcp_tool` hook events from `SessionStart` / `Setup` — MCP servers may not be connected yet
- Do not write secrets into `.mcp.json` for project-scope sharing — use env var expansion (`${API_KEY}`) so secrets stay out of version control
- Do not invoke `headersHelper` from a project- or local-scope config without the user trusting the workspace first; the helper runs arbitrary shell
