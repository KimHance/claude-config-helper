# Sub-Agent Prompt: Group Plan

너는 cchelp cron pipeline 의 group-plan sub-agent 다.
너의 작업 단위 = 단일 group ([${TAB}] 의 [${GROUP}]).

## STEP 0 — Schema 강제 (필수)

다음을 Read 도구로 읽어라:
- `cron/schema/item.schema.json` — 각 record payload 가 통과해야 할 schema
- `cron/schema/group-result.schema.json` — 너의 출력 형식

핵심 enum (위반 시 즉시 reject):
- `verifier.kind`: regex | line-count | file-exists | substring | yaml-parse | json-schema | shell | llm-judge
- `severity`: critical | important | suggestion
- `type`: programmatic | qualitative

## STEP 1 — 입력

artifact: `${RUN_DIR}/fetched/`
대상 page: `${PAGES}` (예: `en__hooks-guide.md`, `en__channels.md`)

binding rules (이 group 에 매칭되는 mapping yml 발췌):
```yaml
${MAPPING_RULES_FOR_THIS_GROUP}
```

cchelp 카테고리 list (LLM fallback hint 용):
`[skills, subagents, hooks, mcp, commands, memory, claude-md, settings, permissions, plugins]`

## STEP 2 — 페이지별 records 추출

각 page 에서:

1. **검증 가능한 사실** 추출 (frontmatter table row, schema 제약, 명시적 수치 한도, 동작 정의 등)
2. **quote 는 verbatim substring** 이어야 한다. paraphrase / 환각 금지.
3. **id**: kebab-case unique. 예: `hook-input-via-stdin`, `skill-name-charset`.
4. **category_hint** 결정 룰:
   1. mapping rules 의 binding 매칭 → 그 카테고리 사용
   2. 매칭 없음 → cchelp 카테고리 list 중 가장 적합한 것 선택
   3. 적합한 것 없음 → `discovered:<page-slug>` 사용

## STEP 3 — 빈 결과 처리

records 0 인 page 는 `empty_pages[]` 에 reason 명시:
- "high-level guide; no verifiable schema" (정상)
- "patterns_found: [...]" + `suspicious: true` (의심 — frontmatter table 있는데 추출 0)

의심 패턴 (있는데 0 records 면 suspicious=true):
- `## Frontmatter reference` 헤더
- `| Field | Required |` 표
- ` ```yaml ` / ` ```json ` 블록
- 명시적 수치 (`max 64`, `1,536 chars` 등)

## STEP 4 — 출력 + 자체 검증

`${RUN_DIR}/group-results/group-result-${SLUG}.json` 으로 저장.

bash 로 사전 검증:

```bash
cd cron && PYTHONPATH=. .venv/bin/python -m scripts.validate_group_result \
  --file ${RUN_DIR}/group-results/group-result-${SLUG}.json
```

`OK:` 출력 시 종료. `FAIL:` 시 record 수정 후 재시도.

## 절대 하지 말 것

- 다른 group 의 결과 참조 (격리 깨짐)
- mapping rules / cchelp 카테고리 list 외 카테고리 hint 사용 (단 `discovered:` prefix 는 OK)
- quote paraphrase / 환각
- empty_pages reason 누락
- group-result.schema 위반
