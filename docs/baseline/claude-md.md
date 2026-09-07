# claude-md

> This file is a cchelp review baseline authored by the maintainer.
> The weekly workflow compares each section against the official Claude docs and rewrites only the sections whose **meaning** has drifted.
> Update granularity = a single section (one `##` heading). If the meaning is unchanged, the section is left byte-for-byte intact — no rewording, no reordering.

## Fundamentals
- `CLAUDE.md` is a markdown file that gives Claude persistent instructions for a project, the user, or the organization
- CLAUDE.md is loaded into the context window at the start of every session as a user message after the system prompt
- It is treated as context, not enforced configuration — Claude reads it and tries to follow it but compliance is not guaranteed
- CLAUDE.md scopes: managed policy (org-wide), project (`./CLAUDE.md` or `./.claude/CLAUDE.md`), user (`~/.claude/CLAUDE.md`), local (`./CLAUDE.local.md` — gitignored, personal)
- Discovery walks up the directory tree from cwd; every CLAUDE.md and CLAUDE.local.md found along the way is concatenated into context
- Concatenation order is filesystem-root-down: ancestor files load first, the cwd's own file loads last; within a directory, `CLAUDE.local.md` is appended after `CLAUDE.md`
- Files in subdirectories below cwd are NOT loaded at launch — they load on demand when Claude reads files in those subdirectories
- `/init` generates a starting CLAUDE.md by analyzing the codebase; if a file already exists it suggests improvements rather than overwriting
- `CLAUDE_CODE_NEW_INIT=1` enables an interactive multi-phase `/init` flow that proposes CLAUDE.md, skills, and hooks together
- `/memory` slash command opens a panel listing all loaded CLAUDE.md / CLAUDE.local.md / rules files

## Advanced
- Managed policy CLAUDE.md locations: macOS `/Library/Application Support/ClaudeCode/CLAUDE.md`, Linux/WSL `/etc/claude-code/CLAUDE.md`, Windows `C:\Program Files\ClaudeCode\CLAUDE.md`
- Managed policy CLAUDE.md cannot be excluded by user settings — it always applies
- The `claudeMd` key in managed settings lets you put managed CLAUDE.md content directly inside `managed-settings.json` instead of deploying a separate file; as of v2.1.260, this setting no longer triggers the security approval dialog (hooks, shell-command, sandbox, and unsafe `env` settings still require approval)
- Project CLAUDE.md may live at either `./CLAUDE.md` or `./.claude/CLAUDE.md`; both are picked up
- `CLAUDE.local.md` exists per-worktree (since gitignored) — sharing personal instructions across worktrees requires importing from `~/.claude/`
- `@path/to/file` import syntax: imported files expand inline at session start, max recursion depth 5
- Import paths can be relative (resolved against the file containing the import, not cwd) or absolute (`@~/.claude/foo.md` or `@/abs/path.md`)
- First time Claude Code sees external imports it shows an approval dialog; declining permanently disables those imports
- `AGENTS.md` is NOT read by Claude Code; if a repo uses AGENTS.md, create a CLAUDE.md that does `@AGENTS.md` and append Claude-specific instructions
- Block-level HTML comments (`<!-- ... -->`) in CLAUDE.md are stripped before injection into context — useful for maintainer notes that should not consume tokens
- Comments inside code blocks are preserved
- The Read tool shows comments as-is (they reappear if a CLAUDE.md is read directly)
- `--add-dir` directories do NOT load their CLAUDE.md by default; set `CLAUDE_CODE_ADDITIONAL_DIRECTORIES_CLAUDE_MD=1` to opt in
- When opted in, `CLAUDE.md`, `.claude/CLAUDE.md`, `.claude/rules/*.md`, and `CLAUDE.local.md` from the additional directory are loaded
- `CLAUDE.local.md` from `--add-dir` is skipped if `--setting-sources` excludes `local`
- `.claude/rules/<topic>.md` directory: organize larger projects into multiple topic files (`testing.md`, `api-design.md`, `frontend/...`, etc.); discovered recursively
- Rules without `paths:` frontmatter load at session start, same priority as `.claude/CLAUDE.md`
- Path-scoped rules use YAML frontmatter `paths:` with glob patterns; only loaded when Claude reads files matching the pattern
- `paths:` accepts multiple patterns, supports brace expansion (`src/**/*.{ts,tsx}`)
- `.claude/rules/` supports symlinks, including links to shared directories or individual files
- Circular symlinks are detected and handled gracefully
- User-level rules at `~/.claude/rules/` apply to every project; load before project rules so project rules have higher priority
- `claudeMdExcludes` setting (in any settings layer) skips ancestor CLAUDE.md / rules files by absolute-path glob
- Arrays in `claudeMdExcludes` merge across settings layers
- Managed policy CLAUDE.md is not excludable via `claudeMdExcludes`
- After `/compact`, project-root CLAUDE.md is re-read from disk and re-injected; nested CLAUDE.md files reload only when Claude next reads files in their subdirectory
- `InstructionsLoaded` hook fires when CLAUDE.md or rules files load; useful for auditing exactly which instruction files are loaded and why
- `--append-system-prompt` flag injects instructions at the system prompt level (must be passed every invocation; suited for scripts/automation)
- Settings vs CLAUDE.md responsibility split: technical enforcement (permissions deny / sandbox / env / forceLogin) goes in managed settings, behavioral guidance goes in CLAUDE.md

## Recommended
- Add to CLAUDE.md when: Claude makes the same mistake twice / a code review catches something Claude should have known / you keep typing the same correction across sessions / a new teammate would need that same context
- Keep facts that should hold every session: build commands, conventions, project layout, "always do X" rules
- Move multi-step procedures or codepath-specific guidance to skills or path-scoped rules instead of bloating CLAUDE.md
- Target under 200 lines per CLAUDE.md file — longer files consume more context and reduce adherence
- Use markdown headers and bullets to group related instructions; structured sections are followed more reliably than dense paragraphs
- Be specific and verifiable: "Use 2-space indentation" beats "format code properly"; "Run `npm test` before committing" beats "test your changes"; "API handlers live in `src/api/handlers/`" beats "keep files organized"
- Review CLAUDE.md and rules periodically to remove outdated or contradicting instructions; if two rules conflict, Claude may pick arbitrarily
- For path-scoped guidance (e.g., rules that apply only inside `src/api/`), prefer `.claude/rules/<topic>.md` with `paths:` frontmatter over a nested CLAUDE.md
- Use `@path` imports for organization (splitting one CLAUDE.md into themed files), even though imported content still loads at launch
- Use `CLAUDE.local.md` (gitignored) for personal sandbox URLs / preferred test data / personal worktree notes
- For org-wide standards, deploy a managed policy CLAUDE.md via MDM / Group Policy / Ansible
- Use HTML block comments for maintainer notes inside CLAUDE.md so they don't burn context
- Use `claudeMdExcludes` in `settings.local.json` to skip irrelevant ancestor CLAUDE.md files in monorepos
- For things that must run at fixed lifecycle events (pre-commit, post-edit), use hooks instead of writing instructions in CLAUDE.md
- For instructions you want at the system-prompt level (not user-message level), use `--append-system-prompt`

## Anti-patterns
- Do not treat CLAUDE.md as enforcement — it is a user message after the system prompt; vague or contradictory instructions get inconsistent behavior
- Do not put `AGENTS.md` content where Claude Code expects `CLAUDE.md` — Claude Code does not read AGENTS.md; bridge with `@AGENTS.md` import
- Do not bloat CLAUDE.md past ~200 lines — adherence drops and context cost rises
- Do not assume `@path` imports reduce context cost — imported content still loads at launch alongside the parent
- Do not assume nested CLAUDE.md files reload after `/compact` — only the project-root CLAUDE.md is re-injected; nested files come back when Claude next reads matching subdirectory files
- Do not write contradictory rules across CLAUDE.md / nested CLAUDE.md / `.claude/rules/` — Claude picks arbitrarily and behavior becomes unpredictable
- Do not put per-codepath guidance into the top-level CLAUDE.md — it consumes context for every session even when irrelevant; use `.claude/rules/<topic>.md` with `paths:` instead
- Do not commit `CLAUDE.local.md` — it is meant to be gitignored; running `/init` with the personal option adds the gitignore for you
- Do not load CLAUDE.md from `--add-dir` directories without explicitly setting `CLAUDE_CODE_ADDITIONAL_DIRECTORIES_CLAUDE_MD=1` — the default skips them
- Do not use HTML inline comments expecting them to be stripped — only block-level comments are removed; inline comments inside code blocks are preserved as-is
- Do not try to exclude managed policy CLAUDE.md — `claudeMdExcludes` cannot remove it
- Do not write build / test / commit hooks as instructions in CLAUDE.md if you need deterministic execution — write them as Claude Code hooks
- Do not put secrets in CLAUDE.md — it loads into context every session and is committed if at project scope
- Do not assume rules without `paths:` frontmatter are conditional — only `paths:`-scoped rules are conditional; the rest load every session
- Do not use `~/.claude/rules/` for project-specific instructions — those go in `.claude/rules/` so the team shares them via version control
