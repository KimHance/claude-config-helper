# Skills Review Checklist

## File Structure
- [ ] Located at `skills/<skill-name>/SKILL.md` (project) or `~/.claude/skills/<name>/SKILL.md` (personal)
- [ ] Reference files (if any) in `skills/<skill-name>/references/`
- [ ] Follows [Agent Skills](https://agentskills.io) open standard

## Frontmatter — Required
- [ ] Has `name` field (becomes `/slash-command`)
- [ ] Has `description` field — combined `description` + `when_to_use` truncated at 1,536 chars in skill listing (as of v2.1.113)
- [ ] Description is concise and specific for skill discovery; front-load the key use case
- [ ] Description explains WHEN to use, not just WHAT it does

## Frontmatter — Optional Fields (correct usage)
- [ ] `when_to_use` — supplemental trigger phrases or example requests; appended to `description` in listing; counts toward 1,536-char cap (if used)
- [ ] `argument-hint` — autocomplete hint is clear (if used)
- [ ] `disable-model-invocation` — set to `true` only for user-only skills (if used)
- [ ] `user-invocable` — set to `false` only for skills Claude invokes automatically (if used)
- [ ] `allowed-tools` — lists only tools the skill genuinely needs without permission prompts (if used)
- [ ] `model` — model override is justified for the workload (if used)
- [ ] `effort` — effort level override is appropriate (if used)
- [ ] `context` — `fork` is used when skill should run in isolated subagent (if used)
- [ ] `agent` — specifies valid subagent type when `context: fork` is set (if used)
- [ ] `paths` — glob patterns are correct for auto-activation (if used)
- [ ] `shell` — set to `bash` or `powershell` only when needed (if used)
- [ ] `hooks` — frontmatter hooks use valid events and are scoped correctly (if used)

## Invocation Control
- [ ] Default (both user and Claude can invoke) is used unless there's a clear reason not to
- [ ] `disable-model-invocation: true` used only for destructive or sensitive operations
- [ ] `user-invocable: false` used only for internal/helper skills

## String Substitutions (if used)
- [ ] `$ARGUMENTS` / `$ARGUMENTS[N]` / `$N` used correctly for user input
- [ ] `${CLAUDE_SESSION_ID}` and `${CLAUDE_SKILL_DIR}` resolve to expected values
- [ ] Dynamic context injection (`` !`command` ``) runs safe, fast commands

## Content Quality
- [ ] Actionable instructions, not narrative
- [ ] Structured with clear sections
- [ ] Includes workflow steps the agent should follow
- [ ] No unnecessary explanation of things Claude already knows

## Context Window Efficiency
- [ ] SKILL.md is not bloated (keep under ~500 lines)
- [ ] Detailed reference material is in `references/` subdirectory (progressive disclosure)
- [ ] No large code blocks that could be summarized

## References
- [ ] External file references use relative paths
- [ ] Referenced files actually exist
- [ ] No dead links or stale references
