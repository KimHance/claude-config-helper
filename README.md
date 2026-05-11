# cchelp

> Custom marketplace plugin for reviewing and generating Claude Code configuration files.

---

## What is this?

A plugin that **reviews** and **generates** Claude Code configuration files — CLAUDE.md, memory, skills, agents, commands, hooks, MCP, and more.

The review system is **self-improving**: a weekly GitHub Actions workflow (`baseline-sync`) keeps the rule files in `docs/baseline/*.md` in sync with the official Claude Code docs, and the same rules drive both the user-facing `/cchelp:review` and the workflow's own self-audit.

## Features

### Review (`/cchelp:review`)

Evaluates 7 categories against `docs/baseline/<category>.md` and assigns letter grades.

| Category | Rule source |
|----------|-------------|
| CLAUDE.md | `docs/baseline/claude-md.md` |
| Memory | `docs/baseline/claude-md.md` (memory covered there) |
| Skills | `docs/baseline/skills.md` |
| Subagents | `docs/baseline/subagents.md` |
| Commands | `docs/baseline/commands.md` |
| Hooks | `docs/baseline/hooks.md` |
| MCP | `docs/baseline/mcp.md` |

Plus cross-cutting baselines for `permissions`, `plugins`, `settings`.

**Output:** Terminal summary table + detailed report at `docs/claude-config-review-report.md` (gitignored).

### Generate (`/cchelp:generate`)

Analyzes the project's tech stack and scaffolds Claude config files from templates.

- Project-tailored `CLAUDE.md`
- Memory system initialization
- Skills / agents / commands scaffolding
- Hooks, settings, MCP configuration

## How review works (in-memory pipeline)

`/cchelp:review` runs a 5-step orchestration in the **main session** (not as a subagent — Claude Code disallows subagent-spawning-subagents).

```
┌─ Main session ─────────────────────────────────────────────┐
│                                                            │
│  Step 1: Discover                                          │
│   ├─ Glob skills/**/SKILL.md                              │
│   └─ Glob agents/*.md                                     │
│                                                            │
│  Step 2: Benchmark (MANDATORY when targets exist)         │
│   ├─ For each target, dispatch in parallel:                │
│   │   ├─ eval-runner (mode=with_skill) → returns JSON     │
│   │   └─ eval-runner (mode=baseline)   → returns JSON     │
│   └─ grader compares both → returns aggregate JSON         │
│                                                            │
│  Step 3: Audit                                             │
│   └─ reviewer subagent reads docs/baseline/*.md +          │
│      bench_data inline → writes review report             │
│                                                            │
│  Step 4: Pre-output verification                           │
│   └─ Confirm bench_data populated (no N/A when targets)   │
│                                                            │
│  Step 5: Output                                            │
│   └─ Read report, print summary table + Top 3 issues      │
└────────────────────────────────────────────────────────────┘
```

**No filesystem writes** by eval-runner / grader — they return JSON inline in their response messages. This eliminates permission prompts in user-local environments.

## Weekly auto-update (`baseline-sync` workflow)

A scheduled GitHub Actions workflow keeps the rules in sync with the official Claude Code docs:

```
[cron / manual dispatch]
        │
        ▼
JOB 1 sync-and-commit
   • 9 doc-fetcher subagents check docs/baseline/*.md vs official docs
   • Apply diffs, branch + commit + push
        │
        ▼
JOB 2 project-review
   • Self-audit (sanity checks: synonym swap, SDK leak, deletion rate)
   • Decide bump level (patch/minor/major)
   • Run benchmarks (skills/subagents categories)
   • Bump plugin.json + marketplace.json
        │
        ▼
JOB 3 create-pr
   • Assemble Korean PR body with bench table
   • Attach labels (automated, criteria-update, semantic labels)
   • Attach reviewer if suspicion flags fire
   • Open PR via REST
        │
        ▼
[user merges PR]
        │
        ▼
auto-release.yml
   • Auto-tag v<version>
   • Create GitHub Release
```

Same review code drives both `/cchelp:review` (user) and JOB 2 (workflow self-audit).

## Usage

### Natural Language

```
Review my claude config
Set up claude config for this project
```

### Slash Commands

```
/cchelp:review    # Review config files
/cchelp:generate  # Generate config files
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

After install, restart Claude Code or run `/reload-plugins`. After upstream releases, run `/plugin marketplace update` to refresh the cache.

## Plugin Structure

```
cchelp/
├── .claude-plugin/             # Plugin & marketplace metadata
│   ├── plugin.json
│   └── marketplace.json
├── agents/                     # 6 agents
│   ├── reviewer.md             # Review (opus) — user-facing
│   ├── generator.md            # Generate (sonnet) — user-facing
│   ├── grader.md               # Eval grader (opus) — internal, in-memory
│   ├── eval-runner.md          # Eval executor (sonnet) — internal, in-memory
│   ├── plan-reviewer.md        # Cron pipeline U3.5 plan validator (opus)
│   └── self-eval-runner.md     # Cron pipeline U5 thin executor (haiku)
├── skills/
│   ├── review/                 # Review skill (rules in docs/baseline/)
│   └── generate/               # Generation templates (8 types)
├── commands/
│   ├── review.md               # /cchelp:review (in-memory orchestration)
│   └── generate.md             # /cchelp:generate
├── docs/
│   └── baseline/               # Single rule source (synced from official docs)
│       ├── claude-md.md
│       ├── skills.md
│       ├── subagents.md
│       ├── commands.md
│       ├── hooks.md
│       ├── mcp.md
│       ├── permissions.md
│       ├── plugins.md
│       └── settings.md
├── .github/workflows/
│   ├── baseline-sync.yml       # Weekly rule sync (3 jobs: sync → review → PR)
│   └── auto-release.yml        # Tag + Release on PR merge
└── CLAUDE.md
```

## Self-Review (v3.1.1, 2026-05-11)

The plugin reviews itself end-to-end with the in-memory pipeline (18 eval-runners + 9 graders + 1 reviewer, all parallel, no permission prompts).

| Category | Grade | Issues | Benchmark (avg) |
|----------|-------|--------|-----------------|
| CLAUDE.md | A | 0 | - |
| Skills | A- | 1 | with-skill +15pp avg |
| Subagents | A- | 2 | with-skill +29pp pass-rate vs baseline |
| Commands | A | 0 | - |
| Memory / Hooks / MCP | N/A | - | - |

**Bench detail (skills + subagents, 9 targets):**

| Target | Quality (with / base) | Tokens (with / base) | Token cost |
|---|---|---|---|
| review | 0.90 / 0.75 | 28K / 21K | +32% |
| generate | 0.85 / 0.70 | 20K / 19K | +4% |
| reviewer | 0.92 / 0.45 | 36K / 20K | +79% |
| generator | 0.90 / 0.60 | 30K / 19K | +59% |
| grader | 0.87 / 0.86 | 27K / 20K | +35% |
| eval-runner | 0.90 / 0.60 | 24K / 19K | +30% |
| plan-reviewer | 0.92 / 0.78 | 26K / 19K | +38% |
| self-eval-runner | 1.00 / 0.30 | 28K / 18K | +51% |

> Quality wins are systemic (+15–70pp), but every skill costs more tokens than baseline. The trade-off is intentional — skills inject structured rules that produce better, more consistent output at higher per-call cost.

**Overall: A-**

## License

MIT
