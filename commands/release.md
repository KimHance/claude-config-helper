---
description: Run review, update README with results, bump version, commit, push, and tag
---

Release workflow for cchelp plugin:

1. Ask the user for the version number (major/minor/patch bump)
2. Spawn `reviewer` subagent to review the current project
3. Update the `## Self-Review` section in `README.md` with the review results and new version
4. Bump version in `.claude-plugin/plugin.json` and `.claude-plugin/marketplace.json`
5. Show the user a summary of all changes and ask for confirmation before proceeding
6. Commit all changes with message: `Release vX.Y.Z`
7. Push to origin and create git tag `vX.Y.Z`
