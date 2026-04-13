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

### Generate + Review + Benchmark (`gn-rv`)

End-to-end orchestration workflow (generate-and-review).

1. **Generate** — Scaffold config files via `generator`
2. **Snapshot** — Copy originals for baseline comparison (if updating)
3. **Review + Benchmark** — Audit via `reviewer` with parallel eval (with-skill vs baseline)
4. **Iterate** — User-driven feedback loop until satisfied
5. **Description Optimize** — Optional trigger accuracy tuning

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
│   ├── reviewer.md          # Review agent (opus) — user-facing
│   ├── generator.md         # Generator agent (sonnet) — user-facing
│   ├── grader.md            # Eval grader (opus) — internal
│   └── eval-runner.md       # Eval executor (sonnet) — internal
├── skills/
│   ├── review/              # Review checklists + benchmark eval (7 categories)
│   ├── generate/            # Generation templates (8 types)
│   └── gn-rv/               # Generate + Review + Benchmark orchestration
├── commands/
│   ├── review.md            # /review
│   ├── generate.md          # /generate
│   └── gn-rv.md             # /gn-rv
└── CLAUDE.md
```

## Self-Review (v1.5.0)

This plugin reviews itself. Latest results:

| Category | Grade | Issues | Benchmark |
|----------|-------|--------|-----------|
| CLAUDE.md | A- | 1 | - |
| Memory | A- | 1 | - |
| Skills | A- | 2 | +57% pass rate, -35% tokens |
| Subagents | A | 0 | +83% pass rate, -35% tokens |
| Commands | A- | 1 | - |
| Hooks | N/A | - | - |
| MCP | N/A | - | - |

| Metric | With Skill | Baseline | Delta |
|--------|-----------|----------|-------|
| Pass rate | 96% | 26% | +70% |
| Avg tokens | ~29,250 | ~45,000 | -35% |
| Avg duration | ~73s | ~112s | -35% |

**Overall: A-**

## License

MIT
