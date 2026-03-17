# cchelp

> Custom marketplace plugin for reviewing and generating Claude Code configuration files.

---

## What is this?

A plugin that **reviews** and **generates** Claude Code configuration files — CLAUDE.md, memory, skills, agents, commands, hooks, MCP, and more.

## Features

### Review (`reviewer`)

Evaluates 7 categories against best-practice checklists and assigns letter grades.

| Category | What it checks |
|----------|---------------|
| CLAUDE.md | Structure, clarity, context efficiency, duplication |
| Memory | Frontmatter, index structure, type consistency, date format |
| Skills | SKILL.md structure, description quality, token efficiency |
| Agents | Trigger examples, model selection, role clarity |
| Commands | Naming, frontmatter, delegation patterns |
| Hooks | Event matching, script executability, performance |
| MCP | Server config, tool duplication, secret management |

**Output:** Terminal summary table + detailed report at `docs/claude-config-review-report.md`

### Generate (`generator`)

Analyzes the project's tech stack and scaffolds Claude config files from templates.

- Project-tailored `CLAUDE.md`
- Memory system initialization
- Skills / agents / commands scaffolding
- Hooks, settings, MCP configuration

### Generate + Review (`gn-rv`)

End-to-end orchestration workflow.

1. **Generate** — Scaffold config files via `generator`
2. **Review** — Audit generated files via `reviewer`
3. **Fix** — Offer auto-fix for Critical/Important issues

## Usage

### Natural Language

```
Review my claude config
Set up claude config for this project
Generate and review claude config
```

### Slash Commands

```
/review    # Review config files
/generate  # Generate config files
/gn-rv     # Generate + review in one step
```

## Installation

Add to `~/.claude/settings.json`:

```json
{
  "extraKnownMarketplaces": {
    "claude-config-helper": {
      "source": {
        "source": "github",
        "repo": "KimHance/claude-config-helper"
      }
    }
  },
  "enabledPlugins": {
    "cchelp@claude-config-helper": true
  }
}
```

## Plugin Structure

```
cchelp/
├── .claude-plugin/          # Plugin & marketplace metadata
├── agents/
│   ├── reviewer.md          # Review agent (opus)
│   └── generator.md         # Generator agent (sonnet)
├── skills/
│   ├── review/              # Review checklists (7 categories)
│   ├── generate/            # Generation templates (8 types)
│   └── gn-rv/               # Generate + Review orchestration
├── commands/
│   ├── review.md            # /review
│   ├── generate.md          # /generate
│   └── gn-rv.md             # /gn-rv
└── CLAUDE.md
```

## Self-Review (v1.3.1)

This plugin reviews itself. Latest results:

| Category | Grade | Issues |
|----------|-------|--------|
| CLAUDE.md | B+ | 2 |
| Skills | A- | 1 |
| Subagents | A | 0 |
| Commands | A- | 1 |

**Overall: A-**

## License

MIT
