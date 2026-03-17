---
description: Run review, update README with results, bump version, commit, push, and tag
---

Release workflow for cchelp plugin:

1. Spawn `reviewer` subagent to review the current project
2. Update the `## Self-Review` section in `README.md` with the review results and new version
3. Bump version in `.claude-plugin/plugin.json` and `.claude-plugin/marketplace.json`
4. Commit all changes with message: `Release vX.Y.Z`
5. Push to origin and create git tag `vX.Y.Z`

Ask the user for the version number (major/minor/patch bump) before proceeding.
