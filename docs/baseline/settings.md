# settings

> This file is a cchelp review baseline authored by the maintainer.
> The weekly workflow compares each section against the official Claude docs and rewrites only the sections whose **meaning** has drifted.
> Update granularity = a single section (one `##` heading). If the meaning is unchanged, the section is left byte-for-byte intact — no rewording, no reordering.

## Fundamentals
- Settings are JSON files that configure Claude Code behavior across model, permissions, hooks, environment variables, plugins, and more
- Five settings tiers, in precedence order (highest first): managed > `--settings` CLI flag > local (`.claude/settings.local.json`) > project (`.claude/settings.json`) > user (`~/.claude/settings.json`)
- Local is gitignored (single user, single repo); project is checked into the repo (team-shared); user is per-machine for one user; managed is org-wide IT-deployed
- Managed settings cannot be overridden by any other tier
- Within the JSON, scalar keys are overridden by higher-precedence tiers; **array keys merge across all scopes** (concatenated, deduplicated)
- The `$schema` field at the top of a settings file enables IDE autocomplete: `https://json.schemastore.org/claude-code-settings.json`
- `/status` command shows which tiers are active, the origin of each, and reports validation errors
- Automatic timestamped backups are created for settings files; the 5 most recent are retained
- The settings JSON does not allow comments (standard JSON, not JSONC)
- Schema may lag the latest CLI; warnings on recent fields don't invalidate the config
- ENV vars that override settings: `CLAUDE_CODE_DISABLE_THINKING`, `CLAUDE_CODE_DISABLE_AUTO_MEMORY`, `CLAUDE_CODE_ENABLE_AWAY_SUMMARY`, `CLAUDE_CODE_DISABLE_FEEDBACK_SURVEY`, `ANTHROPIC_MODEL`, `CLAUDE_CODE_EFFORT_LEVEL`, `CLAUDE_CODE_NO_FLICKER`, `CLAUDE_CODE_USE_POWERSHELL_TOOL`, `CLAUDE_CODE_DISABLE_GIT_INSTRUCTIONS`, `CLAUDE_CODE_SKIP_PROMPT_HISTORY`, `CLAUDE_CODE_API_KEY_HELPER_TTL_MS`, `CLAUDE_CODE_OTEL_HEADERS_HELPER_DEBOUNCE_MS`, `DISABLE_AUTOUPDATER`, `CLAUDE_CODE_DISABLE_ALTERNATE_SCREEN`, `ANTHROPIC_WORKSPACE_ID`, `CLAUDE_CODE_SESSION_ID`, `CLAUDE_CODE_FORCE_SYNC_OUTPUT`, `CLAUDE_CODE_PACKAGE_MANAGER_AUTO_UPDATE`, `CLAUDE_CODE_PLUGIN_PREFER_HTTPS`, `CLAUDE_CODE_POWERSHELL_RESPECT_EXECUTION_POLICY`, `CLAUDE_CODE_STOP_HOOK_BLOCK_CAP`, `CLAUDE_CODE_ENABLE_FEEDBACK_SURVEY_FOR_OTEL`, `DISABLE_UPDATES`, `ANTHROPIC_BEDROCK_SERVICE_TIER`, `ENABLE_TOOL_SEARCH`, `OTEL_LOG_RAW_API_BODIES`, `CLAUDE_CODE_CERT_STORE`

## Advanced
- Core model/behavior keys: `agent`, `model`, `availableModels`, `modelOverrides`, `effortLevel`, `alwaysThinkingEnabled`, `outputStyle`
- Permissions keys: `permissions` (object), `allowManagedPermissionRulesOnly` (managed), `disableBypassPermissionsMode`
- File/directory access keys: `additionalDirectories`, `claudeMdExcludes`, `respectGitignore`, `fileSuggestion`
- Memory keys: `autoMemoryEnabled`, `autoMemoryDirectory` (latter only honored from managed/user/`--settings`, never from project/local)
- Login/org keys (typically managed): `forceLoginMethod` (`claudeai`/`console`), `forceLoginOrgUUID` (string or array; empty array fails closed)
- API/credentials keys: `apiKeyHelper`, `awsAuthRefresh`, `awsCredentialExport`, `gcpAuthRefresh`, `otelHeadersHelper`
- Environment keys: `env` (object of strings), `defaultShell` (`bash`/`powershell`)
- Sandbox: `sandbox` (object — see sandbox sub-shape)
- Terminal/UI: `tui` (`fullscreen`/`default`), `autoScrollEnabled`, `editorMode` (`normal`/`vim`), `viewMode` (`default`/`verbose`/`focus`), `preferredNotifChannel`, `showTurnDuration`, `showThinkingSummaries`, `spinnerTipsEnabled`, `spinnerTipsOverride`, `spinnerVerbs`, `syntaxHighlightingDisabled`, `prefersReducedMotion`, `terminalProgressBarEnabled`
- Git keys: `attribution` (object with `commit` and `pr` strings; empty string hides), `includeGitInstructions`
- Plugin keys: `enabledPlugins` (`{"plugin@marketplace": bool}`), `extraKnownMarketplaces`, `strictKnownMarketplaces` (managed), `blockedMarketplaces` (managed), `allowedChannelPlugins` (managed), `pluginTrustMessage` (managed)
- Hooks keys: `hooks` (object), `disableAllHooks`, `allowManagedHooksOnly` (managed), `allowedHttpHookUrls`, `httpHookAllowedEnvVars`, `continueOnBlock`
- MCP keys: `allowedMcpServers` (managed), `deniedMcpServers` (managed), `allowManagedMcpServersOnly` (managed), `enableAllProjectMcpServers`, `enabledMcpjsonServers`, `disabledMcpjsonServers`
- Subagent/team keys: `agent`, `disableAgentView`, `teammateMode` (`auto`/`in-process`/`tmux`)
- Update channel keys: `autoUpdatesChannel` (`stable`/`latest`), `minimumVersion`, `DISABLE_AUTOUPDATER` env equivalent
- Plan keys: `plansDirectory`, `useAutoModeDuringPlan`, `showClearContextOnPlanAccept`
- Auto mode keys: `autoMode` (with `environment`/`allow`/`soft_deny`/`hard_deny`; include `"$defaults"` to inherit), `disableAutoMode` (`"disable"`), `fastModePerSessionOptIn`
- Voice keys: `voice` (`enabled`/`mode`/`autoSubmit`), `language`
- Channels keys: `channelsEnabled` (managed), `companyAnnouncements` (array)
- Telemetry keys: `feedbackSurveyRate` (0-1), `awaySummaryEnabled`
- Worktree keys: `worktree.symlinkDirectories`, `worktree.sparsePaths`, `worktree.baseRef` (`fresh` branches from `origin/<default>`, `head` uses local HEAD; default `fresh`), `worktree.bgIsolation` (set to `"none"` to let background sessions edit working copy directly), plus a `.worktreeinclude` file for copying gitignored files into worktrees
- URL/template keys: `prUrlTemplate` (placeholders `{host}`, `{owner}`, `{repo}`, `{number}`, `{url}`)
- Status line: `statusLine` (`{type: "command", command: "..."}`); script receives `CLAUDE_PROJECT_DIR`
- Skills: `skillOverrides` (v2.1.129+, values `on`/`name-only`/`user-invocable-only`/`off`), `disableSkillShellExecution`, `maxSkillDescriptionChars` (character limit for skill descriptions), `skillListingBudgetFraction` (context budget fraction for skill listing)
- Sandbox/security: `sandbox`, `disableSkillShellExecution`; sandbox filesystem/network sub-keys include `bwrapPath` and `socatPath` to specify custom bubblewrap/socat binary locations (Linux/WSL)
- Deep links / remote control: `disableDeepLinkRegistration` (`"disable"`), `disableRemoteControl` (v2.1.128+)
- Session keys: `cleanupPeriodDays` (default 30, min 1), `skipWebFetchPreflight`
- Windows-only managed: `wslInheritsWindowsSettings`
- Policy keys (managed): `policyHelper` (object with `path`, `timeoutMs`, `refreshIntervalMs`; returns JSON with `managedSettings`, `claudeMd`, `appendSystemPrompt`), `parentSettingsBehavior` (`'first-wins'` | `'merge'` for SDK managedSettings precedence)
- `permissions` object sub-keys: `allow`, `deny`, `ask`, `defaultMode` (`default`/`acceptEdits`/`plan`/`auto`/`dontAsk`/`bypassPermissions`), `additionalDirectories`, `disableBypassPermissionsMode` (`"disable"`), `skipDangerousModePermissionPrompt` (ignored from project settings — security)
- Permission rule syntax: `Tool` (all), `Tool(specifier)`, e.g., `Bash(npm run *)`, `Read(./.env)`, `Read(./secrets/**)`, `Read(/abs/path)`, `WebFetch(domain:example.com)`, `MCP(server:name)`, `Agent(name)`
- Permission evaluation: deny → ask → allow, first match wins
- `env` field: every session gets these env vars; precedence shell > local > project > user > managed; values are always strings
- `--settings <file-or-json>` CLI flag merges in for one session, between managed and local in precedence
- `--env KEY=value` CLI flag sets env for one session
- Managed settings delivery: server (Anthropic admin console), MDM/OS policies (macOS plist `com.anthropic.claudecode`, Windows registry `HKLM\SOFTWARE\Policies\ClaudeCode` or `HKCU` for user-level), file-based (`/Library/Application Support/ClaudeCode/managed-settings.json` macOS, `/etc/claude-code/managed-settings.json` Linux/WSL, `C:\Program Files\ClaudeCode\managed-settings.json` Windows v2.1.75+), drop-in directory `managed-settings.d/*.json` (alphabetic merge, numeric prefixes for ordering)
- Within the managed tier, precedence is server > MDM/OS > file-based
- `forceRemoteSettingsRefresh` (managed) blocks CLI startup until remote settings fetched (fail-closed)
- Sandbox object (macOS/Linux/WSL2): `enabled`, `failIfUnavailable`, `autoAllowBashIfSandboxed`, `excludedCommands`, `allowUnsandboxedCommands`, plus `filesystem.{allowWrite, denyWrite, denyRead, allowRead, allowManagedReadPathsOnly}`, `network.{allowedDomains, deniedDomains, allowUnixSockets, allowAllUnixSockets, allowLocalBinding, allowMachLookup, allowManagedDomainsOnly, httpProxyPort, socksProxyPort}`, `enableWeakerNestedSandbox`, `enableWeakerNetworkIsolation`
- Sandbox path prefixes: `/abs`, `~/path` (home), `./path` or `path` (project root in non-user settings; `~/.claude` in user settings)
- Some keys live in `~/.claude.json` (the global config, not `settings.json`): `autoConnectIde`, `autoInstallIdeExtension`, `externalEditorContext`; this file also holds OAuth session, per-project allowed tools, MCP user/local server configs, caches
- SSH config (`sshConfigs[]`) is read only from managed and user settings, never from project/local

## Recommended
- Use `.claude/settings.local.json` (gitignored) for personal overrides without polluting the team's project settings
- Use `.claude/settings.json` (committed) for team-shared baselines: project model, project permissions, project hooks
- Use `~/.claude/settings.json` for personal cross-project preferences (theme, editorMode, color, voice)
- Use managed settings only when org-wide enforcement is required; the user/project layer is enough otherwise
- Use `$schema` line at the top of any settings file for IDE autocomplete and field validation
- Use `permissions.defaultMode: "acceptEdits"` for tight, trusted projects; default mode otherwise
- Keep `permissions.deny` short and high-impact (secrets, dangerous commands); over-denying creates churn
- Use `Bash(<prefix> *)` rule shape rather than naming every variant; first match wins so deny rules go first
- Use `permissions.additionalDirectories` to grant file access without changing cwd
- Use `claudeMdExcludes` (in `.claude/settings.local.json`) to skip ancestor CLAUDE.md noise in monorepos
- Use `enabledPlugins: {"plugin@marketplace": false}` to disable a plugin per-scope without uninstalling
- Use `attribution.commit` / `attribution.pr` empty strings (`""`) to hide Co-Authored-By trailers if undesired
- Use `env` for telemetry config and feature flags; values are always strings
- Use `worktree.symlinkDirectories: ["node_modules"]` to avoid duplicating heavy dirs across worktrees
- Use `--settings '{"key": value}'` for one-off overrides instead of editing files
- Use `/status` to verify which settings layers are active when something seems off
- For org compliance: combine `forceLoginMethod`, `forceLoginOrgUUID`, `allowManagedHooksOnly`, `allowManagedPermissionRulesOnly`, `allowManagedMcpServersOnly`, `strictKnownMarketplaces`

## Anti-patterns
- Do not write JSON comments in `settings.json` — they break parsing
- Do not place `autoMemoryDirectory` in project or local settings — silently ignored from those tiers (security)
- Do not place `skipDangerousModePermissionPrompt` in project settings — ignored to prevent a hostile repo from suppressing the prompt
- Do not put secrets in `settings.json` — project files are committed; use `apiKeyHelper` / env vars / dynamic helpers instead
- Do not assume `--settings` overrides managed — managed always wins
- Do not assume CLI `--env KEY=value` is persisted — it applies for the session only
- Do not rely on `permissions.defaultMode: "bypassPermissions"` — managed `disableBypassPermissionsMode` can block it; also a security smell
- Do not pass user-only keys (`autoConnectIde`, `autoInstallIdeExtension`, `externalEditorContext`) in `settings.json` — they live in `~/.claude.json`
- Do not pass `sshConfigs` in project or local settings — only managed and user are read
- Do not assume array keys (e.g., `permissions.deny`, `additionalDirectories`) are replaced by higher-tier settings — they merge
- Do not commit `.claude/settings.local.json` — it should be gitignored
- Do not edit managed settings file paths from a normal user account — managed locations require admin / require IT-deployed configuration
- Do not use deprecated `includeCoAuthoredBy` — use `attribution.commit` instead
- Do not assume `tui: "fullscreen"` works on every terminal — fall back to `default` when issues appear
- Do not put long ad hoc instructions in `outputStyle` — output styles are a structured mechanism documented separately
- Do not depend on settings persisting across CLI versions — schema can evolve and `minimumVersion` may bump
