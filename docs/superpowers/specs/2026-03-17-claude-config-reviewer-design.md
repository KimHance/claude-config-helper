# Claude Config Reviewer Plugin — Design Spec

**Date:** 2026-03-17
**Status:** Approved
**Approach:** A — Single subagent with skill reference + slash command

---

## Overview

Personal custom marketplace plugin that reviews all Claude-related configuration files in any project. Provides a single `claude-config-reviewer` subagent that spawns on natural language triggers ("클로드 세팅 리뷰해줘", "AI 관련 세팅 리뷰해줘") and a `/review-claude-config` slash command for manual trigger. Outputs a terminal summary + detailed report file.

## Plugin Structure

```
claude-reviewr/
├── .claude-plugin/
│   ├── plugin.json
│   └── marketplace.json
├── CLAUDE.md
├── agents/
│   └── claude-config-reviewer.md
├── skills/
│   └── review-claude-config/
│       ├── SKILL.md
│       └── references/
│           ├── claude-md-checklist.md
│           ├── memory-checklist.md
│           ├── skills-checklist.md
│           ├── agents-checklist.md
│           ├── commands-checklist.md
│           ├── hooks-checklist.md
│           ├── settings-checklist.md
│           └── mcp-checklist.md
├── commands/
│   └── review-claude-config.md
└── README.md
```

## Component Details

### 1. Plugin Metadata (`.claude-plugin/plugin.json`)

```json
{
  "name": "claude-reviewr",
  "description": "Reviews Claude configuration files (CLAUDE.md, skills, agents, hooks, settings, memory, MCP) for quality and best practices",
  "version": "1.0.0",
  "author": { "name": "KimHance" },
  "license": "MIT",
  "skills": "./skills/",
  "agents": ["./agents/claude-config-reviewer.md"],
  "commands": "./commands/"
}
```

### 2. Marketplace Metadata (`.claude-plugin/marketplace.json`)

```json
{
  "name": "claude-reviewr",
  "description": "Claude configuration reviewer plugin",
  "owner": { "name": "KimHance" },
  "plugins": [{
    "name": "claude-reviewr",
    "description": "Reviews Claude configuration files for quality and best practices",
    "version": "1.0.0",
    "source": "./"
  }]
}
```

### 3. CLAUDE.md (Plugin Root)

Provides high-level instructions:
- Claude config review tasks are delegated to the `claude-config-reviewer` subagent
- The subagent references the `review-claude-config` skill for evaluation criteria
- Report output goes to `docs/claude-config-review-report.md`

### 4. Subagent (`agents/claude-config-reviewer.md`)

**Frontmatter:**
```yaml
name: claude-config-reviewer
description: |
  Reviews Claude Code configuration files for quality and best practices. Use this agent when the user asks to review Claude settings, AI configuration, CLAUDE.md quality, skill/agent definitions, memory system, hooks, or MCP setup. Examples: "클로드 세팅 리뷰해줘", "AI 관련 세팅 리뷰해줘", "review my claude config", "check my agent setup", "클로드 파일 점검해줘"
model: sonnet
```

**Tools needed:** Read, Glob, Grep, Bash (for `ls` only), Write (for report file)

**Behavior:**
1. **Scan** — Discover all Claude-related files across project and user levels
2. **Review** — Evaluate each applicable category against the checklist in the skill's reference files
3. **Cross-validate** — Check references between files (e.g., CLAUDE.md mentions a skill that exists)
4. **Report** — Output terminal summary (grades per category + top issues) and write detailed report

**Review Process per Category:**
- If no files found for a category → grade as "N/A" (skip)
- Assign letter grade (A/B/C/D/F)
- List specific issues found with file paths and line numbers
- Provide actionable improvement suggestions
- Note what's done well

**Model choice rationale:** `sonnet` is appropriate because the task is read-only analysis with structured output. No complex reasoning or code generation required. This keeps cost low for frequent use across projects.

### 5. Skill (`skills/review-claude-config/SKILL.md`)

**Frontmatter:**
```yaml
name: review-claude-config
description: Review checklist and evaluation criteria for Claude Code configuration files including CLAUDE.md, memory, skills, agents, commands, hooks, settings, and MCP setup
```

**Content:** Workflow overview + pointers to category-specific reference files in `references/` subdirectory. The agent loads only the relevant reference files per category, keeping context window usage efficient.

**Workflow:**
1. Scan for Claude-related files
2. Determine which categories are applicable (skip N/A)
3. For each applicable category, load the reference checklist and evaluate
4. Run cross-validation checks
5. Generate terminal summary table
6. Write detailed report to `docs/claude-config-review-report.md` (create `docs/` if needed)

### 6. Reference Files (`skills/review-claude-config/references/`)

Each file contains the detailed checklist for one category. Progressive disclosure: loaded only when that category is being reviewed.

#### `claude-md-checklist.md`
- Exists at appropriate levels (project root, module directories)
- Clear structure with sections (overview, conventions, commands, patterns)
- Not too long (context window efficiency) or too short (missing critical info)
- No stale/contradictory instructions
- Uses imperative tone, actionable instructions
- Module-level files complement (not duplicate) project-level

#### `memory-checklist.md`
- MEMORY.md index exists and is under 200 lines
- Memory files have proper frontmatter (name, description, type)
- No duplicate or contradictory memories
- Descriptions are specific enough for relevance matching
- Types are correctly assigned (user/feedback/project/reference)
- No stale project memories with relative dates

#### `skills-checklist.md`
- SKILL.md has proper frontmatter (name, description)
- Description is concise and specific for discovery
- Content is actionable, not narrative
- References to external files use relative paths
- Not bloated — respects context window budget

#### `agents-checklist.md`
- Proper frontmatter (name, description, model)
- Description includes trigger examples for accurate matching
- Model choice is appropriate (opus for complex reasoning, sonnet for speed, haiku for lightweight)
- Clear role definition and behavioral instructions
- Not overlapping with other agents

#### `commands-checklist.md`
- Proper frontmatter with description
- Clear trigger name matching user intent
- Instructions are specific about what to do
- Delegates to agents/skills when appropriate

#### `hooks-checklist.md`
- hooks.json properly formatted
- Hook scripts exist and are executable
- Hooks match appropriate events (PreToolUse, PostToolUse, etc.)
- No overly broad matchers that slow down every tool call

#### `settings-checklist.md`
- Permissions are not overly broad (avoid `Bash(*)`)
- Plugin list is clean (no disabled/unused plugins)
- No sensitive data in settings files
- extraKnownMarketplaces sources are valid

#### `mcp-checklist.md`
- MCP servers are properly configured
- No duplicate or conflicting tool names across servers
- Server connections are healthy (if checkable)
- Tools are properly scoped with appropriate permissions

### 7. Cross-Validation Checks (in SKILL.md)
- CLAUDE.md references to skills/agents that actually exist
- Memory references to files/paths that are valid
- Settings permissions match installed plugins' tool names
- No orphaned files (agents/skills defined but never referenced)

### 8. Command (`commands/review-claude-config.md`)

**Frontmatter:**
```yaml
description: Review all Claude configuration files in the current project for quality and best practices
```

**Body:** Instructs Claude to spawn the `claude-config-reviewer` subagent to perform a full review of the current project's Claude configuration.

### 9. Report Format

**Terminal Summary:**
```
## Claude Config Review Summary

| Category           | Grade | Issues |
|--------------------|-------|--------|
| CLAUDE.md          | B+    | 2      |
| Memory System      | A     | 0      |
| Skills             | C     | 4      |
| Subagents          | A     | 0      |
| Commands           | N/A   | -      |
| Hooks              | B     | 1      |
| Settings           | B-    | 3      |
| MCP                | N/A   | -      |

**Overall: B**

Top 3 Issues:
1. [Critical] skills/foo/SKILL.md missing description in frontmatter
2. [Important] CLAUDE.md references non-existent skill "bar"
3. [Suggestion] Memory file "project_deadline.md" uses relative date
```

**Detailed Report (`docs/claude-config-review-report.md`):**
Full breakdown per category with file paths, line references, and specific improvement suggestions.

## Installation

Add to `~/.claude/settings.json`:
```json
{
  "extraKnownMarketplaces": {
    "claude-reviewr": {
      "source": {
        "source": "github",
        "repo": "KimHance/claude-reviewr"
      }
    }
  },
  "enabledPlugins": {
    "claude-reviewr@claude-reviewr": true
  }
}
```

Note: `claude-reviewr` in `extraKnownMarketplaces` is the marketplace name, and `claude-reviewr` after `@` in `enabledPlugins` matches the `name` in the marketplace's plugins array.

## Triggering

- **Natural language:** "클로드 세팅 리뷰해줘", "AI 관련 세팅 리뷰해줘", "review claude config", "check my agent setup", "클로드 파일 점검해줘"
- **Slash command:** `/review-claude-config`

## Edge Cases

- **Missing categories:** If no files exist for a category (e.g., no hooks in a project), grade as "N/A" and skip
- **No docs/ directory:** Create `docs/` directory before writing the report file
- **User-level vs project-level:** Scan both `~/.claude/` and `.claude/` in project root
