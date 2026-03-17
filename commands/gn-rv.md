---
description: Generate Claude config files and review them for quality in one step
---

Run the full Claude config workflow using the `gn-rv` skill:

1. Spawn `generator` to create config files for the current project
2. Spawn `reviewer` to audit the generated files
3. If critical/important issues are found, offer to auto-fix them

This combines `/generate` and `/review` into a single end-to-end flow.
