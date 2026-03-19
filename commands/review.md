---
description: "Review Claude configuration files. Use `/review` for total review, or `/review <path>` to target a specific file or directory."
---

Spawn the `reviewer` subagent to review Claude Code configuration files in the current project.

**Mode detection:**
- `/review` (no arguments) → **Total mode**: Scan all categories, benchmark all skills/agents
- `/review <path>` (with argument) → **Target mode**: Review and benchmark only the specified file or directory

Examples:
- `/review` — Full review of everything
- `/review skills/review/` — Review only the review skill
- `/review agents/grader.md` — Review only the grader agent

Pass the mode and target path (if any) to the reviewer subagent.

**After the reviewer completes**, read `docs/claude-config-review-report.md` and output the following sections to the terminal:
1. Summary table (with Benchmark column)
2. Top 3 issues
3. Key observations (if present)
4. Report file path: `docs/claude-config-review-report.md`

Do NOT rely on the reviewer's return message for terminal output — always read from the report file directly.
