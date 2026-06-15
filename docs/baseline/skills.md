# skills

> This file is a cchelp review baseline authored by the maintainer.
> The weekly workflow compares each section against the official Claude docs and rewrites only the sections whose **meaning** has drifted.
> Update granularity = a single section (one `##` heading). If the meaning is unchanged, the section is left byte-for-byte intact — no rewording, no reordering.

## Fundamentals
- Skills follow Agent Skills open standard (agentskills.io)
- SKILL.md is required entry point; directory name becomes skill name for invocation
- description is recommended (not required) so Claude knows when to use the skill
- name field is optional; if omitted, uses directory name (lowercase, alphanumeric, hyphen, max 64 characters)
- when_to_use field appends to description for auto-invocation matching
- argument-hint provides CLI autocomplete hint for expected arguments
- arguments field allows named positional arguments for $name substitution in skill content
- Description is loaded into context automatically; full content loads only when invoked
- Auto-invocation when description matches user request, or manual invocation with /skill-name
- Skill content stays in context across turns within same session
- !`command` blocks execute at skill load time, output replaces placeholder
- Multi-line variant using ```! fenced code blocks for multiple commands
- ${CLAUDE_SKILL_DIR} resolves to skill directory path
- $ARGUMENTS, $ARGUMENTS[N], $N for argument substitution
- ${CLAUDE_SESSION_ID} provides session identifier for logging/correlation
- ${CLAUDE_EFFORT} provides current effort level (low/medium/high/xhigh/max)
- Escape literal $ before a digit or argument name with backslash: \$1.00 in prose, \$name in skill content

## Advanced
- disable-model-invocation: true prevents Claude from auto-loading, user-only invocation
- user-invocable: false hides from / menu, Claude-only invocation
- allowed-tools pre-approves tool list for permission bypass during skill execution
- disallowed-tools removes tools from Claude's available pool while skill is active; restriction clears on next user message
- model field overrides active model for skill duration
- effort field overrides session effort level
- context: fork runs skill in isolated subagent context
- agent field specifies subagent type (Explore, Plan, general-purpose, custom)
- hooks field scopes hooks to skill lifecycle
- paths field uses glob patterns to limit auto-invocation to matching files
- shell field sets shell to bash (default) or powershell for !`command` execution
- Skills can include supporting files (template.md, examples/, scripts/)
- Skills location priority: Enterprise > Personal (~/.claude/skills/) > Project (.claude/skills/) > Plugin
- Plugin skills namespaced as /plugin-name:skill-name to prevent conflicts; the `name` frontmatter field determines the invocation name, allowing stable names across install methods
- Live change detection for .claude/skills/ directories within current session
- Nested .claude/skills/ discovery in subdirectories (monorepo support)
- --add-dir included directories have skills/ loaded automatically with live reload
- /reload-skills command re-scans skill directories without restarting session; SessionStart hooks can return reloadSkills: true to trigger reload in same session
- Skill content lifecycle: single message at invocation, persists until session end
- Auto-compaction: 25k combined budget, 5k per skill preserved, older skills dropped
- Skill descriptions truncated at 1,536 chars (description + when_to_use combined)
- Skill vs Command: same /name behavior, skills add supporting files and invocation control
- Skill vs CLAUDE.md: task-specific vs always-on knowledge
- Skill vs Subagent: instructions vs separate context
- Skill+context:fork vs subagent: delegate in skill vs define subagent separately
- Skill vs Hook: instructions vs deterministic lifecycle automation
- Plugin skill namespace prevents collisions with project/personal skills
- skillOverrides setting controls visibility (on/name-only/user-invocable-only/off)
- /skills command shows available skills with visibility status
- disableSkillShellExecution policy disables !`command` execution for user/project/plugin sources

## Recommended
- description should put key use case first to fit within character budget
- Skills should target under 500 lines; move detailed reference to separate files
- Reference files (reference.md, examples.md) should be linked from SKILL.md
- Use context: fork for skills with explicit instructions and actionable tasks
- Specify agent type when using context: fork to optimize execution environment
- Bundle scripts (Python, bash) in skills/scripts/ for Claude to execute
- Generate visual output as self-contained HTML files for data exploration
- Use allowed-tools in skill frontmatter to pre-approve common operations
- Leverage supporting file structure for complex skills: templates, examples, scripts
- Pass $ARGUMENTS placeholder so Claude sees user input
- Include ultrathink in skill content for deeper reasoning on complex tasks
- Use skills for repeatable workflows your team shares
- Dynamic context injection with !`command` to ground skill in live data
- Skills with disable-model-invocation: true work best for deterministic workflows
- Organized skills should preserve foundational knowledge while enabling flexibility

## Anti-patterns
- Do not put commands/, agents/, skills/, hooks/ inside .claude-plugin/ directory
- Only plugin.json belongs in .claude-plugin/; everything else at plugin root
- .claude/commands/ still works but skills/ is preferred for new development
- Forked subagent context has no conversation history; write actionable tasks
- context: fork only makes sense for skills with explicit instructions, not guidelines
- context: fork skills without actionable task prompt return without meaningful output
