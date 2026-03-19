# Trigger Test Template for Description Optimization

## Eval Query Format

Generate 20 queries as JSON:

```json
[
  { "query": "detailed user prompt", "should_trigger": true },
  { "query": "adjacent domain query", "should_trigger": false }
]
```

## Should-Trigger Queries (10)

Queries that SHOULD activate the skill/agent. Cover:

1. **Direct requests** — Explicitly names the task (e.g., "review my CLAUDE.md")
2. **Indirect requests** — Needs the skill but doesn't name it (e.g., "check if my AI config follows best practices")
3. **Casual phrasing** — Informal language (e.g., "클로드 세팅 좀 봐줘")
4. **Formal phrasing** — Professional language (e.g., "audit Claude Code configuration quality")
5. **Partial scope** — Only one category (e.g., "are my agent definitions correct?")
6. **Full scope** — Everything at once (e.g., "full Claude config review")
7. **Typos/abbreviations** — Realistic user input (e.g., "review claud config")
8. **Context-heavy** — With file paths and specifics (e.g., "check agents/reviewer.md quality")
9. **Competitive** — Could match another skill but this one should win
10. **Uncommon use case** — Edge case that still applies

## Should-NOT-Trigger Queries (10)

Queries that should NOT activate the skill/agent. Focus on **near-misses**:

1. **Keyword overlap** — Shares words but means something different (e.g., "review this PR" vs "review config")
2. **Adjacent domain** — Related but different tool needed (e.g., "generate a CLAUDE.md" → generator, not reviewer)
3. **General coding** — Programming task, not config review (e.g., "fix this TypeScript error")
4. **Other AI tools** — Not Claude-specific (e.g., "review my OpenAI config")
5. **System settings** — User-level, not project-level (e.g., "check my ~/.claude/settings.json")
6. **Vague** — Too ambiguous to trigger confidently (e.g., "help me with Claude")
7. **Read-only** — Just wants to see a file, not review it (e.g., "show me CLAUDE.md")
8. **Meta** — Asking about the tool itself (e.g., "what does the reviewer agent do?")
9. **Tricky near-miss** — Very close but subtly wrong scope
10. **Different workflow** — Needs gn-rv, not standalone review

## Optimization Process

1. **Split**: 60% train (12 queries), 40% test (8 queries)
2. **Evaluate**: Run each query 3 times against current description
3. **Propose**: Generate improved description based on train failures
4. **Re-evaluate**: Test new description on both train and test sets
5. **Iterate**: Up to 5 rounds maximum
6. **Select**: Pick description with best test score (avoids overfitting)

## Output

Present before/after comparison:
```
Before: "Reviews Claude Code configuration files..."
After:  "Comprehensive quality audit for Claude Code configs..."
Score:  Train 11/12 → 12/12, Test 7/8 → 8/8
```
