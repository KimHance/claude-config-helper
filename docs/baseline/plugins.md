# plugins

> This file is a cchelp review baseline authored by the maintainer.
> The weekly workflow compares each section against the official Claude docs and rewrites only the sections whose **meaning** has drifted.
> Update granularity = a single section (one `##` heading). If the meaning is unchanged, the section is left byte-for-byte intact — no rewording, no reordering.

## Fundamentals
- A plugin is a packaged bundle of skills, agents, hooks, MCP servers, LSP servers, monitors, and/or default settings, distributed and versioned as a single unit
- A plugin lives in its own directory containing `.claude-plugin/plugin.json` (the manifest)
- Manifest fields: `name` (unique identifier and skill namespace), `description`, `version` (optional — falls back to git SHA), `author` (optional)
- Plugin skills are namespaced as `/<plugin-name>:<skill-name>` to prevent conflicts with other plugins or standalone skills
- Standalone vs plugin: standalone (`.claude/<dir>/`) is for personal / project-only / quick experiments, with plain skill names; plugin is for sharing, multi-project reuse, versioning, marketplace distribution, with namespaced skill names
- Plugins are discovered through marketplaces (registered separately) or direct local/url loading via `--plugin-dir <path>` or `--plugin-url <archive-url>`
- The `/plugin` slash command manages installation, enabling/disabling, listing, and updates
- After enabling/disabling a plugin or editing plugin files, run `/reload-plugins` to apply changes without restarting
- The `enabledPlugins` settings key (`{"<plugin>@<marketplace>": true|false}`) is what actually turns plugins on/off; can live in user, project, local, or managed settings
- Local copy via `--plugin-dir` takes precedence over an installed plugin of the same name for that session, except when force-enabled in managed settings
- `--plugin-dir` accepts both directories and `.zip` plugin archives

## Advanced
- Plugin directory structure: `.claude-plugin/plugin.json` (manifest), `skills/` (each skill as `<name>/SKILL.md`), `commands/` (legacy flat MD; new plugins use `skills/`), `agents/` (subagent definitions), `hooks/hooks.json` (event handlers), `.mcp.json` (MCP servers), `.lsp.json` (LSP servers), `monitors/monitors.json` (background monitors), `bin/` (executables added to Bash `PATH` while plugin enabled), `settings.json` (default plugin settings)
- Only `plugin.json` belongs inside `.claude-plugin/`; everything else (`skills/`, `agents/`, `hooks/`, `commands/`, `.mcp.json`, etc.) lives at plugin root
- Plugin manifest is **optional** — if `.claude-plugin/plugin.json` is absent, components are auto-discovered in default locations and the plugin name is derived from the directory name
- Plugin manifest schema (`plugin.json`) full field list: `name`, `version`, `description`, `author` (object: `name`/`email`/`url`), `homepage`, `repository`, `license`, `keywords` (array), `skills` (component path override), `commands` (override), `agents` (override), `hooks` (override), `mcpServers` (override), `outputStyles` (override), `lspServers` (override), `experimental.themes`, `experimental.monitors`, `dependencies` (string or `{name, version}` entries)
- `version` field absent + git distribution → every commit counts as a new version; setting `version` makes updates explicit
- Plugin install scopes (where `enabledPlugins` is recorded): `user` (default, `~/.claude/settings.json`), `project` (`.claude/settings.json`), `local` (`.claude/settings.local.json`, gitignored), `managed` (managed settings, read-only)
- Plugin `settings.json` (plugin root): currently only `agent` and `subagentStatusLine` keys honored; `agent` activates one of the plugin's custom agents as the main thread system prompt
- Plugin agent supported frontmatter fields: `name`, `description`, `model`, `effort`, `maxTurns`, `tools`, `disallowedTools`, `skills`, `memory`, `background`, `isolation` (`"worktree"` only); `mcpServers` frontmatter are now loaded for main-thread agent sessions via `--agent`
- Plugin monitors require Claude Code v2.1.105 or later
- Plugin monitor required fields: `name`, `command`, `description`; optional: `when` (`"always"` default, or `"on-skill-invoke:<skill-name>"`)
- LSP server required fields: `command`, `extensionToLanguage`; optional: `args`, `transport` (`stdio`/`socket`), `env`, `initializationOptions`, `settings`, `workspaceFolder`, `startupTimeout`, `shutdownTimeout`, `restartOnCrash`, `maxRestarts`
- Plugin themes are experimental; live in `themes/` as JSON with `name`, `base` (preset), `overrides` (sparse color tokens)
- Bundled-file env vars: `${CLAUDE_PLUGIN_ROOT}` (plugin install dir), `${CLAUDE_PLUGIN_DATA}` (persistent data dir, survives plugin updates)
- Plugin agents have stricter security: `hooks`, `permissionMode` frontmatter fields are silently ignored when loading from a plugin
- Plugin MCP servers run from `.mcp.json` at plugin root (or inline `mcpServers` in `plugin.json`); start when plugin is enabled, stop when disabled
- LSP servers in `.lsp.json` give Claude real-time code intelligence (per-language `command`, `args`, `extensionToLanguage` map); user must have the language server binary installed locally
- Monitors in `monitors/monitors.json` watch logs/files/external status and push notifications to Claude during the session; each entry has `name`, `command`, optional `description`, `when` trigger
- `bin/` directory: executables placed here are added to Bash tool's `PATH` while the plugin is enabled
- Marketplace concept: a registry that lists installable plugins; users add a marketplace then install plugins from it
- `extraKnownMarketplaces` settings key adds marketplace sources; sources are `github` (`{source: "github", repo: "owner/repo"}`), `git` (`{source: "git", url: "..."}`), `directory` (`{source: "directory", path: "/local/path"}` for development), `hostPattern` (`{source: "hostPattern", hostPattern: "regex"}`), or `settings` (`{source: "settings", name: "...", plugins: [...]}`)
- Managed-only plugin policies: `strictKnownMarketplaces` (allowlist of marketplace sources, enforced before download), `blockedMarketplaces` (blocklist, enforced before download), `allowedChannelPlugins` (allowlist of channel plugins that may push messages, requires `channelsEnabled: true`), `pluginTrustMessage` (custom trust-warning text)
- Force-enabled plugins: managed settings can pin a plugin to enabled; users cannot override; force-enabled plugins' hooks are exempt from `allowManagedHooksOnly`
- Plugin trust dialog: shown the first time a plugin is installed, listing what it bundles and asking for explicit trust before activation
- Testing flags: `--plugin-dir <local>` for development; `--plugin-url <archive-zip-url>` for one-session loading from a remote archive (e.g., CI build artifact); both can be repeated for multiple plugins; if the fetch or archive validation fails, Claude Code reports a plugin load error and starts without the plugin
- Convert standalone → plugin: copy `.claude/commands/` `agents/` `skills/` into the plugin dir; move `hooks` from `settings.json` into `hooks/hooks.json` (same JSON shape); remove duplicates from `.claude/` after testing

## Recommended
- Start with standalone (`.claude/`) for quick iteration; convert to a plugin only when ready to share
- Use a clear, unique `name` in `plugin.json` — it doubles as the skill namespace (`/<name>:<skill>`)
- Set an explicit `version` in `plugin.json` rather than relying on git SHA so users get coherent update bumps
- Use `${CLAUDE_PLUGIN_ROOT}` for any path inside the plugin (skill scripts, MCP server commands, hook scripts) so the plugin works regardless of install location
- Use `${CLAUDE_PLUGIN_DATA}` for persistent state that should survive plugin updates
- Test with `--plugin-dir ./local-copy` while iterating; reload with `/reload-plugins` instead of restarting
- For team-internal plugins, host the marketplace in a private repo and add via `extraKnownMarketplaces`
- Bundle a `README.md` with install + usage instructions before sharing
- Prefer official LSP plugins for common languages; only ship a custom `.lsp.json` for languages without an official plugin
- For org-wide enforcement, combine `strictKnownMarketplaces` + force-enabled plugins in managed `enabledPlugins` so users can't add unapproved sources
- Use `--plugin-url` only for archives you control or trust — same trust considerations as any plugin source
- After conversion from standalone, delete the original `.claude/` files to avoid duplicate-name resolution surprises
- Keep `commands/` only for legacy migration; author new plugin extensions as `skills/`

## Anti-patterns
- Do not put `commands/`, `agents/`, `skills/`, `hooks/`, `.mcp.json`, etc. inside `.claude-plugin/` — only `plugin.json` belongs there
- Do not assume plugin agent frontmatter `hooks` / `permissionMode` are honored — they are silently ignored for plugin agents; `mcpServers` are now loaded for main-thread agent sessions via `--agent`
- Do not omit `version` and assume the git SHA strategy is fine if you want predictable update behavior — every commit becomes a "new version"
- Do not collide with another plugin's `name` — both can't be installed simultaneously without confusion
- Do not assume `--plugin-dir` overrides a force-enabled managed plugin — managed force-enable always wins
- Do not use plain (non-namespaced) skill names like `/hello` from inside a plugin — plugin skills are always `/<plugin>:<skill>`
- Do not bundle secrets in `plugin.json` or `.mcp.json` — plugins are typically distributed via public marketplaces; use env var expansion (`${API_KEY}`) instead
- Do not load a plugin from `--plugin-url` you don't trust — Claude Code fetches the archive and runs its hooks/scripts
- Do not put settings keys other than `agent` / `subagentStatusLine` in plugin `settings.json` — unknown keys are silently ignored
- Do not assume hooks defined in a plugin work when `allowManagedHooksOnly: true` is set — only managed hooks and force-enabled plugin hooks are loaded in that case
- Do not modify `.claude-plugin/plugin.json` mid-session expecting changes to apply automatically — run `/reload-plugins` after edits
- Do not skip the `description` field in `plugin.json` — it is shown in the plugin manager and helps users decide whether to install
- Do not assume installing a plugin auto-trusts it — the trust dialog must be accepted before the plugin's components activate
- Do not author new plugins with skills under `commands/` — that path still works for legacy compat but `skills/` is the recommended path
