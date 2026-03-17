# claude-config-helper

> Claude Code 설정 파일을 리뷰하고 생성해주는 커스텀 마켓플레이스 플러그인

---

## What is this?

Claude Code를 사용할 때 작성하는 다양한 설정 파일들 — `CLAUDE.md`, 메모리, 스킬, 서브에이전트, 훅, MCP 등 — 이 잘 작성되었는지 **리뷰**해주고, 새 프로젝트에서 이 파일들을 **생성**해주는 플러그인입니다.

## Features

### Review (`claude-config-reviewer`)

8개 카테고리에 대해 best practice 체크리스트 기반으로 평가하고 등급을 매겨줍니다.

| Category | What it checks |
|----------|---------------|
| CLAUDE.md | 구조, 명확성, 컨텍스트 효율성, 중복 여부 |
| Memory | frontmatter, 인덱스 구조, 타입 정합성, 날짜 형식 |
| Skills | SKILL.md 구조, description 품질, 토큰 효율성 |
| Agents | trigger 예시, 모델 선택, 역할 명확성 |
| Commands | 네이밍, frontmatter, 위임 구조 |
| Hooks | 이벤트 매칭, 스크립트 실행 가능성, 성능 |
| Settings | 권한 범위, 보안, 레벨 분리 |
| MCP | 서버 구성, 툴 중복, 시크릿 관리 |

**Output:** 터미널 요약 테이블 + `docs/claude-config-review-report.md` 상세 리포트

### Generate (`claude-config-generator`)

프로젝트의 기술 스택을 분석하고, 템플릿 기반으로 Claude 설정 파일들을 생성합니다.

- 프로젝트에 맞춘 `CLAUDE.md` 생성
- 메모리 시스템 초기 구성
- 스킬/에이전트/커맨드 스캐폴딩
- 훅, settings, MCP 설정 생성

### Setup (`setup-claude-config`)

생성과 리뷰를 한 번에 실행하는 오케스트레이션 워크플로우입니다.

1. **Generate** — `claude-config-generator`로 설정 파일 생성
2. **Review** — `claude-config-reviewer`로 생성된 파일 품질 검증
3. **Fix** — Critical/Important 이슈 발견 시 자동 수정 제안

## Usage

### Natural Language (자동 스폰)

```
클로드 세팅 리뷰해줘
AI 관련 세팅 리뷰해줘
클로드 세팅 만들어줘
프로젝트 AI 세팅 초기화해줘
클로드 세팅 만들고 리뷰까지 해줘
```

### Slash Commands

```
/review-claude-config    # 설정 파일 리뷰
/generate-claude-config  # 설정 파일 생성
/setup-claude-config     # 생성 + 리뷰 한 번에
```

## Installation

`~/.claude/settings.json`에 추가:

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
    "claude-config-helper@claude-config-helper": true
  }
}
```

## Plugin Structure

```
claude-config-helper/
├── .claude-plugin/          # Plugin & marketplace metadata
├── agents/
│   ├── claude-config-reviewer.md    # Review agent
│   └── claude-config-generator.md   # Generator agent
├── skills/
│   ├── review-claude-config/        # Review checklists (8 categories)
│   ├── generate-claude-config/      # Generation templates (8 types)
│   └── setup-claude-config/         # Generate + Review orchestration
├── commands/
│   ├── review-claude-config.md      # /review-claude-config
│   ├── generate-claude-config.md    # /generate-claude-config
│   └── setup-claude-config.md       # /setup-claude-config
└── CLAUDE.md
```

## License

MIT
