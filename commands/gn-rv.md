---
description: Generate Claude config files, then review and benchmark them for quality in one step
---

Run the full Claude config workflow using the `gn-rv` skill:

1. Generate config files via `generator`
2. Review + benchmark via `reviewer`
3. Iterate based on user feedback
4. Optionally optimize descriptions

**After the reviewer completes**, read `docs/claude-config-review-report.md` and output the following sections to the terminal:
1. Summary table (with Benchmark column)
2. Top 3 issues
3. Key observations (if present)
4. Report file path: `docs/claude-config-review-report.md`

Do NOT rely on the reviewer's return message for terminal output — always read from the report file directly.
