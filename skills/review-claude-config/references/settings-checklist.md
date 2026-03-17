# Settings (settings.json) Review Checklist

## File Locations
- `~/.claude/settings.json` — user-level settings (synced)
- `~/.claude/settings.local.json` — user-level local settings (not synced)
- `.claude/settings.json` — project-level settings
- `.claude/settings.local.json` — project-level local settings

## Permissions
- [ ] No overly broad permissions (e.g., `Bash(*)` allows any command)
- [ ] Permissions are scoped to specific tools and patterns
- [ ] No sensitive commands auto-allowed (e.g., `git push --force`)
- [ ] MCP tool permissions match installed MCP servers

## Plugin Configuration
- [ ] `enabledPlugins` only lists plugins that are actually used
- [ ] No stale/removed plugin references
- [ ] `extraKnownMarketplaces` sources are valid URLs/repos

## Security
- [ ] No API keys, tokens, or passwords in settings files
- [ ] No overly permissive tool access
- [ ] Sensitive permissions are in `settings.local.json` (not synced)

## Organization
- [ ] User-level vs project-level settings are appropriately separated
- [ ] No duplicated settings across files
- [ ] Local-only settings (machine-specific paths, credentials) are in `.local.json`
