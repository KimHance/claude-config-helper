---
description: Generate Claude config files and review them for quality in one step
---

Run the full Claude config setup workflow using the `setup-claude-config` skill:

1. Spawn `claude-config-generator` to create config files for the current project
2. Spawn `claude-config-reviewer` to audit the generated files
3. If critical/important issues are found, offer to auto-fix them

This combines `/generate-claude-config` and `/review-claude-config` into a single end-to-end flow.
