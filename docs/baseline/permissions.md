# permissions

> This file is a cchelp review baseline authored by the maintainer.
> The weekly workflow compares each section against the official Claude docs and rewrites only the sections whose **meaning** has drifted.
> Update granularity = a single section (one `##` heading). If the meaning is unchanged, the section is left byte-for-byte intact — no rewording, no reordering.

## Fundamentals
- Permissions control which tools Claude Code can use and which files / domains / resources it can touch
- Three rule decisions: `allow` (auto-approve), `ask` (prompt for confirmation), `deny` (block); evaluated in order **deny → ask → allow**, first match wins
- Tool tier baseline: read-only tools (Read/Grep/Glob, etc.) require no approval; Bash requires approval (with "yes don't ask again" remembered per project + command); file modifications require approval (remembered until session end)
- The `/permissions` command is the interactive UI for viewing and managing rules; lists each rule's source settings file
- A rule format is `Tool` (matches all uses) or `Tool(specifier)` (specific match)
- Settings precedence applies fully: managed > `--settings` flag > local > project > user; deny at any layer wins
- Hook decisions cannot bypass deny or ask rules; deny rules still apply when a `PreToolUse` hook returned `allow`/`ask`
- Hook exit-code-2 block takes precedence over allow rules (hook can block what permissions would otherwise allow)
- Permissions and sandboxing are complementary: permissions cover all tools, sandboxing OS-enforces only Bash
- The `/permissions` UI also surfaces working directories and recent auto-mode denials

## Advanced
Permission modes (`permissions.defaultMode`): `default` (prompt first use), `acceptEdits` (auto-accept edits + filesystem cmds in cwd / additionalDirectories), `plan` (read-only exploration), `auto` (research preview classifier-based), `dontAsk` (auto-deny unless pre-allowed), `bypassPermissions` (skip all prompts; root rm -rf still prompts). Added in v2.1.136: `settings.autoMode.hard_deny` for auto mode classifier rules that block unconditionally regardless of user intent or allow exceptions.
- `bypassPermissions` is the danger mode — also auto-allows writes to `.git`/`.claude`/`.vscode`/`.idea`/`.husky`; circuit breaker: `rm -rf /` and `rm -rf ~` still prompt
- `permissions.disableBypassPermissionsMode: "disable"` blocks bypass mode and `--dangerously-skip-permissions` flag
- `permissions.disableAutoMode: "disable"` blocks auto mode activation
- `Bash(*)` ≡ `Bash` (matches all bash); wildcard `*` allowed at any position
- Bash space-before-`*` enforces word boundary: `Bash(ls *)` matches `ls -la` but not `lsof`; `Bash(ls*)` matches both
- `Bash(<prefix>:*)` is equivalent to `Bash(<prefix> *)`; the `:*` form is recognized only at the trailing position
- Bash compound commands (`&&`, `||`, `;`, `|`, `|&`, `&`, newlines) require each subcommand to match a rule independently
- Approving a compound command via "Yes don't ask again" saves up to 5 separate rules, one per subcommand
- Bash process wrappers stripped before matching: `timeout`, `time`, `nice`, `nohup`, `stdbuf`; bare `xargs` (no flags) also stripped
- Environment runners NOT stripped: `direnv exec`, `devbox run`, `mise exec`, `npx`, `docker exec` — write specific rules like `Bash(devbox run npm test)`
- Exec wrappers always prompt (never auto-approved by prefix): `watch`, `setsid`, `ionice`, `flock`; same for `find -exec`/`-delete`
- Read-only Bash commands run without prompt in every mode: `ls`, `cat`, `head`, `tail`, `grep`, `find`, `wc`, `diff`, `stat`, `du`, `cd`, read-only forms of `git`
- Unquoted globs allowed for fully-read-only commands (`ls *.ts`); commands with write/exec flags (`find`, `sort`, `sed`, `git`) still prompt with unquoted glob
- `cd` into cwd / `additionalDirectories` is read-only; compound `cd packages/api && ls` runs without prompt; `cd` + `git` always prompts
- PowerShell rules use same shape as Bash; aliases canonicalized (so `Get-ChildItem` rule also matches `gci`/`ls`/`dir`); case-insensitive; AST parsed; pipeline `|`, `;`, and (PS7+) `&&`/`||` split compound commands
- Read/Edit specifier patterns (gitignore-spec): `//abs/path` (filesystem-absolute), `~/path` (home), `/path` (project-root-relative), `path` or `./path` (cwd-relative)
- WARNING: `/Users/alice/file` is project-root-relative, NOT absolute; absolute requires `//Users/alice/file`
- Windows paths normalized to POSIX: `C:\Users\alice` → `/c/Users/alice`; cross-drive `**` use `//**/.env`
- `*` matches single dir; `**` matches recursively; bare `Read`/`Edit`/`Write` matches all
- `Edit` rules apply to all built-in edit tools; `Read` rules best-effort on Read/Grep/Glob etc.
- Read/Edit rules apply ONLY to built-in tools, NOT Bash subprocesses — `Read(./.env)` deny does not block `cat .env`; sandbox is needed for OS-level file enforcement
- Symlink behavior: allow rules need BOTH symlink and target match (otherwise prompts); deny rules block if EITHER matches
- WebFetch: `WebFetch(domain:example.com)` matches that domain; bare `WebFetch` matches all
- WebFetch alone does NOT prevent network access — Bash with `curl`/`wget` can still hit any URL; combine with Bash deny rules or sandbox
- MCP rules: `mcp__<server>` matches all server tools; `mcp__<server>__*` wildcard same; `mcp__<server>__<tool>` specific tool
- Agent rules: `Agent(name)` matches a named subagent (built-in or custom); add to deny array or use `--disallowedTools` flag
- Skill rules: `Skill(name)` exact, `Skill(name *)` prefix-with-args
- `permissions.additionalDirectories` extends file access (not configuration discovery); files there follow the same permission rules as cwd
- Configuration discovered from `--add-dir` directories: only skills (`.claude/skills/` with live reload), `enabledPlugins`/`extraKnownMarketplaces` from `.claude/settings.json`, and CLAUDE.md / `.claude/rules/` / `CLAUDE.local.md` only when `CLAUDE_CODE_ADDITIONAL_DIRECTORIES_CLAUDE_MD=1`
- Subagents, commands, output styles, hooks, and other settings are NOT loaded from `--add-dir`
- Working dir extension methods: `--add-dir <path>` at startup, `/add-dir` mid-session, or persistent via `permissions.additionalDirectories`
- Workspace trust dialog: project-scope `allowed-tools` in skills, `headersHelper` in MCP, etc. take effect only after the user accepts the trust dialog
- Managed-only permission policies: `allowManagedPermissionRulesOnly` (blocks user/project rule overrides), `allowManagedMcpServersOnly`, `allowManagedHooksOnly`, `allowedChannelPlugins`, `forceRemoteSettingsRefresh`, `pluginTrustMessage`, `sandbox.filesystem.allowManagedReadPathsOnly`, `sandbox.network.allowManagedDomainsOnly`, `strictKnownMarketplaces`, `blockedMarketplaces`, `wslInheritsWindowsSettings`, `channelsEnabled`
- `disableBypassPermissionsMode` works from any scope — a user can lock themselves out
- Sandbox interaction: when sandbox enabled with `autoAllowBashIfSandboxed: true` (default), sandboxed Bash runs without prompts even with `ask: Bash(*)`; explicit deny still applies; `rm`/`rmdir` against `/`, home, or critical system paths still prompts

## Recommended
- Use deny rules sparingly but decisively for secrets, credentials, and dangerous commands (`Read(./.env)`, `Read(./secrets/**)`, `Bash(curl *)`, `Bash(wget *)`)
- Use `permissions.allow` for predictable, repeatedly-used commands (`Bash(npm run *)`, `Bash(git commit *)`, etc.)
- Prefer `WebFetch(domain:trusted.com)` allowlist + Bash network-tool deny over trying to constrain `Bash(curl ...)` arguments
- Treat unquoted command-arg patterns (`Bash(curl http://github.com/ *)`) as fragile — use hooks or sandbox for real URL filtering
- Use `Agent(name)` deny rules to disable specific subagents an admin doesn't trust
- Use `Skill(name)` permission rules to allow / deny specific skills without editing their frontmatter
- Use `additionalDirectories` for trusted siblings (sibling repos, shared docs) instead of running from a higher cwd
- Combine permissions with sandboxing for defense-in-depth: deny rules block intent, sandbox blocks effect even on prompt-injection
- For org policy enforcement, place rules in managed settings + set `allowManagedPermissionRulesOnly: true`
- Use `defaultMode: "acceptEdits"` for tightly trusted projects to skip per-edit prompts; pair with deny rules for guardrails
- Use `defaultMode: "plan"` for read-only exploration (e.g., onboarding sessions)
- Use `dontAsk` mode plus a curated allow list for highly automated, hands-off workflows
- For "all but a few Bash commands" use case, allow `Bash` and write a `PreToolUse` hook that exits 2 on disallowed commands
- Write absolute-path rules with double slash (`//abs`) — single slash is project-root-relative

## Anti-patterns
- Do not assume `/Users/alice/file` is absolute — it's project-root-relative; use `//Users/alice/file` for absolute
- Do not rely on `Bash(prefix *)` to constrain arguments — flags-before-URL, redirects, env-var URL substitution, and extra spaces all bypass it
- Do not assume `Bash(devbox run npm test)`-style runners are stripped — environment runners (`direnv exec`, `devbox run`, `mise exec`, `npx`, `docker exec`) are NOT stripped; specific rules are required
- Do not assume `Read(./.env)` deny blocks `cat .env` in Bash — Read/Edit rules cover built-in tools only, not Bash subprocesses
- Do not use `bypassPermissions` outside of isolated containers / VMs — it bypasses prompts on writes to `.git`/`.claude`/`.vscode`/`.idea`/`.husky`
- Do not assume PowerShell aliases must be spelled exactly — they are canonicalized (case-insensitive); `Get-ChildItem`, `gci`, `ls`, `dir` all match the same rule
- Do not assume `WebFetch(domain:x)` blocks Bash from reaching that domain — Bash `curl`/`wget` is unaffected
- Do not place project-scope `permissions.skipDangerousModePermissionPrompt` — silently ignored from project settings (security)
- Do not assume `--allowedTools` / `--disallowedTools` overrides managed deny — managed always wins
- Do not assume `permissions.allow` overrides higher-tier deny — deny at any tier wins
- Do not use `Bash(ls*)` (no space) when you mean `Bash(ls *)` — the no-space form also matches `lsof` and other prefix-collisions
- Do not match exec wrappers (`watch`, `setsid`, `flock`, `find -exec`, `find -delete`) with prefix rules — they always prompt
- Do not assume Read deny rules cover symlinks pointing into denied dirs from elsewhere — they do, but allow rules don't (allow needs both symlink and target to match)
- Do not configure `auto` mode without telling the classifier which infra you trust (see auto mode config)
- Do not place rules expected to be policy-binding in user or project settings if managed settings are required — only managed-tier guarantees enforcement
