---
description: Review all Claude configuration files in the current project for quality and best practices
---

Spawn the `claude-config-reviewer` subagent to perform a comprehensive review of all Claude Code configuration files in the current project and user environment.

The agent will:
1. Scan for all Claude-related files (CLAUDE.md, memory, skills, agents, commands, hooks, settings, MCP)
2. Evaluate each category against best-practice checklists
3. Cross-validate references between files
4. Output a summary table with grades in the terminal
5. Write a detailed report to `docs/claude-config-review-report.md`
