# cchelp

Claude Code 설정 파일(CLAUDE.md, 스킬, 에이전트, 메모리, 훅, MCP 등)을 리뷰하고 생성하는 플러그인.

## Routing

- Claude config **review** tasks → `reviewer` subagent
- Claude config **generation/scaffolding** tasks → `generator` subagent
- Claude config **full setup** (generate + review) → `gn-rv` skill
- Review criteria are in the `review` skill
- Generation templates are in the `generate` skill