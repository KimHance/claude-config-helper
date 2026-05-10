# commands

> This file is a cchelp review baseline authored by the maintainer.
> The weekly workflow compares each section against the official Claude docs and rewrites only the sections whose **meaning** has drifted.
> Update granularity = a single section (one `##` heading). If the meaning is unchanged, the section is left byte-for-byte intact — no rewording, no reordering.

## Fundamentals
- A command is a single token starting with `/` typed at the start of a message; text after the command name is passed as arguments
- Type `/` alone to open the menu; type `/<prefix>` to filter
- Commands fall into three classes: built-in (CLI-coded behavior), bundled skills (prompt-based, marked **Skill** in the docs reference), and user-defined skills / MCP prompts
- Bundled skills use the same mechanism as user-written skills — Claude can also invoke them automatically when relevant
- User-defined commands now go through the skills mechanism (skill at `.claude/skills/<name>/SKILL.md` or legacy `.claude/commands/<name>.md`); both surface as `/<name>`
- MCP prompts surface as `/mcp__<server>__<prompt>` and are discovered dynamically from connected servers
- Plugin-provided skills surface as `/<plugin-name>:<skill-name>`
- Command availability depends on platform, plan, and environment (e.g. `/desktop` macOS/Windows, `/upgrade` Pro/Max, `/setup-bedrock` only when `CLAUDE_CODE_USE_BEDROCK=1`)
- Argument notation in docs: `<arg>` required, `[arg]` optional
- The `/help` command lists what is available in the current environment

## Advanced
- `/add-dir <path>` — add a working directory for file access during session; most `.claude/` config not loaded from added dirs (skills/ is the exception, and CLAUDE.md only with `CLAUDE_CODE_ADDITIONAL_DIRECTORIES_CLAUDE_MD=1`)
- `/agents` — manage subagent configurations (Running / Library tabs)
- `/autofix-pr [prompt]` — spawn a Claude Code on the web session that watches the PR for the current branch and pushes fixes; requires `gh` CLI
- `/batch <instruction>` — bundled Skill; orchestrates large-scale parallel changes across the codebase via worktree-isolated background agents
- `/branch [name]` (alias `/fork`) — branch the current conversation; `/fork` becomes a forked-subagent spawn when `CLAUDE_CODE_FORK_SUBAGENT=1`
- `/btw <question>` — quick side question that doesn't add to the conversation history
- `/chrome` — configure Claude in Chrome integration
- `/claude-api [migrate|managed-agents-onboard]` — bundled Skill; loads Claude API reference for the project's language; `migrate` upgrades existing API code to a newer model
- `/clear` (aliases `/reset`, `/new`) — start a new conversation; previous one stays in `/resume`
- `/color [color|default]` — set prompt-bar color (`red`/`blue`/`green`/`yellow`/`purple`/`orange`/`pink`/`cyan`); syncs to claude.ai/code under Remote Control
- `/compact [instructions]` — summarize conversation to free context; optional focus instructions
- `/config` (alias `/settings`) — open Settings UI (theme, model, output style, etc.)
- `/context` — visualize context window usage
- `/context [all]` — visualize current context usage as a colored grid; pass `all` to expand per-item breakdown in fullscreen mode
- `/copy [N]` — copy assistant response (Nth-latest) to clipboard; press `w` to save to file
- `/cost` — alias for `/usage`
- `/debug [description]` — bundled Skill; enable debug logging for the session and analyze the debug log
- `/desktop` (alias `/app`) — continue session in Claude Code Desktop app (macOS/Windows)
- `/diff` — interactive diff viewer for uncommitted changes and per-turn diffs
- `/doctor` — diagnose Claude Code install/settings; press `f` to have Claude fix issues
- `/effort [level|auto]` — set model effort level (`low`/`medium`/`high`/`xhigh`/`max`); takes effect immediately; without argument opens interactive slider
- `/exit` (alias `/quit`) — exit CLI
- `/export [filename]` — export conversation as plain text
- `/extra-usage` — configure extra usage to keep working past rate limits
- `/fast [on|off]` — toggle fast mode
- `/feedback [report]` (alias `/bug`) — submit feedback
- `/fewer-permission-prompts` — bundled Skill; scans transcripts and adds an allowlist to project settings
- `/focus` — toggle focus view (last prompt + tool summary + final response); fullscreen-only; persists per `viewMode`
- `/heapdump` — write JS heap snapshot to `~/Desktop` for diagnosing memory issues
- `/help` — show help and available commands
- `/hooks` — view hook configurations
- `/ide` — manage IDE integrations
- `/init` — initialize project with CLAUDE.md guide; `CLAUDE_CODE_NEW_INIT=1` enables interactive multi-phase flow (skills + hooks + memory)
- `/insights` — generate a usage report (project areas, interaction patterns, friction points)
- `/install-github-app` — set up Claude GitHub Actions app for a repo
- `/install-slack-app` — install Claude Slack app
- `/keybindings` — open or create keybindings configuration
- `/login` / `/logout` — Anthropic account auth
- `/loop [interval] [prompt]` (alias `/proactive`) — bundled Skill; run a prompt repeatedly; without interval Claude self-paces; without prompt runs autonomous maintenance or `.claude/loop.md`
- `/mcp` — manage MCP server connections and OAuth
- `/memory` — edit CLAUDE.md, toggle auto-memory, view auto-memory entries
- `/mobile` (aliases `/ios`, `/android`) — show QR for mobile app
- `/model [model]` — select model; supports left/right arrow effort adjustment
- `/passes` — share free-week pass with friends (eligibility-based)
- `/permissions` (alias `/allowed-tools`) — manage allow/ask/deny rules; review auto mode denials
- `/plan [description]` — enter plan mode (optionally with task description)
- `/plugin` — manage plugins
- `/powerup` — discover features through interactive lessons
- `/pr-comments [PR]` — **Removed in v2.1.91**; ask Claude directly to view PR comments instead
- `/privacy-settings` — view/update privacy settings (Pro/Max only)
- `/radio` — open Claude FM lo-fi radio in your browser
- `/recap` — one-line summary of current session
- `/release-notes` — interactive changelog viewer
- `/reload-plugins` — reload all active plugins without restart
- `/remote-control` (alias `/rc`) — make session controllable from claude.ai
- `/remote-env` — configure default remote env for `--remote` web sessions
- `/rename [name]` — rename session; auto-generates name if no arg
- `/resume [session]` (alias `/continue`) — resume conversation by ID/name
- `/review [PR]` — review a PR locally; `/ultrareview` is the cloud variant
- `/rewind` (aliases `/checkpoint`, `/undo`) — rewind conversation/code or summarize from a selected message
- `/sandbox` — toggle sandbox mode (supported platforms only)
- `/schedule [description]` (alias `/routines`) — create/list/run routines; conversational setup
- `/security-review` — analyze pending changes for security vulnerabilities
- `/setup-bedrock` — configure Amazon Bedrock auth/region/model pins (visible only with `CLAUDE_CODE_USE_BEDROCK=1`)
- `/setup-vertex` — configure Google Vertex AI auth/project/region/model (visible only with `CLAUDE_CODE_USE_VERTEX=1`)
- `/simplify [focus]` — bundled Skill; reviews recent changes for code reuse / quality / efficiency, applies fixes; runs 3 review agents in parallel
- `/skills` — list skills; `t` sorts by token count; `Space` cycles visibility states; `Enter` saves to `.claude/settings.local.json`
- `/stats` — alias for `/usage` (opens Stats tab)
- `/status` — open Settings UI on Status tab; usable while Claude is responding
- `/statusline` — configure status line; auto-configures from shell prompt without args
- `/stickers` — order Claude Code stickers
- `/tasks` (alias `/bashes`) — list/manage background tasks
- `/team-onboarding` — generate team onboarding guide from past 30 days of usage
- `/teleport` (alias `/tp`) — pull a Claude Code web session into this terminal (claude.ai subscription required)
- `/terminal-setup` — configure terminal keybindings (visible only in terminals that need it: VS Code, Cursor, Windsurf, Alacritty, Zed)
- `/theme` — change color theme; supports `auto`, light/dark, daltonized, ANSI, custom themes from `~/.claude/themes/` or plugins
- `/tui [default|fullscreen]` — set terminal UI renderer
- `/ultraplan <prompt>` — draft plan in ultraplan cloud session, review in browser
- `/ultrareview [PR]` — deep multi-agent cloud review (Pro/Max free runs through 2026-05-05, then extra usage)
- `/upgrade` — open upgrade page
- `/usage` — show session cost, plan limits, activity stats
- `/vim` — **Removed in v2.1.92**; toggle Vim editor mode via `/config → Editor mode`
- `/voice [hold|tap|off]` — toggle voice dictation (claude.ai account required)
- `/web-setup` — connect GitHub to Claude Code on the web via local `gh` CLI

## Recommended
- Use `/help` first when unsure what is available — surface differs per platform/plan/environment
- Use `/compact` (with optional focus) over `/clear` when you want to keep working in the same conversation but free up context
- Use `/copy` over manual selection in the terminal — its picker handles code blocks individually
- Use `/diff` to review uncommitted changes per Claude turn before committing
- Use `/permissions` to manage allow/ask/deny rules interactively rather than hand-editing settings
- Use `/skills` and `/agents` to inspect what Claude can currently invoke; `/skills` also exposes visibility cycling for skillOverrides
- Use `/btw` for quick side questions that should not pollute history (no tool access either)
- Use `/branch` (or `/fork` when `CLAUDE_CODE_FORK_SUBAGENT` unset) to preserve a snapshot of the conversation before a risky direction
- Use `/rewind` (alias `/checkpoint`, `/undo`) to revert conversation or code state — preferred over manually re-typing
- For team onboarding, run `/team-onboarding` to generate a paste-ready guide from your last 30 days
- For deep code review prefer `/ultrareview` over `/review` when willing to trade time and tokens for thoroughness
- For automation that should run on a schedule, prefer `/schedule` (routines) over `/loop` for cron-style cadence; `/loop` is for live in-session repetition
- Use `/heapdump` and `/doctor` first when diagnosing local Claude Code issues before opening a feedback report

## Anti-patterns
- Do not use `/pr-comments` — removed in v2.1.91; ask Claude directly with the `gh` CLI present
- Do not use `/vim` — removed in v2.1.92; toggle the Vim editor mode through `/config → Editor mode`
- Do not assume every command listed in the docs is available — availability depends on platform, plan, and env vars; `/upgrade`, `/desktop`, `/setup-bedrock`, `/setup-vertex`, `/passes`, `/privacy-settings` only show conditionally
- Do not type a command in the middle of a message — only the start of a message is recognized as a command boundary
- Do not assume `/clear` and `/compact` do the same thing — `/clear` starts a new conversation, `/compact` summarizes in place
- Do not assume `/fork` always branches the conversation — when `CLAUDE_CODE_FORK_SUBAGENT=1`, `/fork` spawns a forked subagent instead of conversation branching
- Do not author new custom commands as `.claude/commands/<name>.md` — that path still works but skills (`.claude/skills/<name>/SKILL.md`) are the recommended path going forward
- Do not assume `/btw` has tool access — it answers from existing context only and the answer is discarded, not appended to history
- Do not run `/ultrareview` from a non-git directory or without authorization — it bills against extra usage after the free trial window
