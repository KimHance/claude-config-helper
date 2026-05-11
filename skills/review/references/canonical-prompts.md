# Canonical Bench Prompts

Fixed prompt set for benchmark evals. `eval-runner` reads from this file instead of generating new prompts each run, so scores are comparable across runs (eliminates "prompt drift" run-to-run variance).

**Rules:**
- Each target gets a stable list of 3 prompts (simple / medium / complex).
- Prompts are written to stress-test the skill or agent's core behavior — not to be easy.
- Add new entries when a new skill/agent is introduced. Do NOT renumber existing entries — `eval_name` is used as a tracking key across runs.
- If a target is not listed here, eval-runner falls back to generating prompts (legacy behavior).

---

## Skills

### `skills/review/SKILL.md`

1. **review-skill-target-mode-claude-md** *(simple)*
   `Review CLAUDE.md against docs/baseline/claude-md.md. Produce summary table + top issues + grade.`

2. **review-skill-checklist-coverage-skill-file** *(medium)*
   `Review skills/generate/SKILL.md. Walk each checklist item from docs/baseline/skills.md (Fundamentals, Advanced, Recommended, Anti-patterns). Mark pass/warn/fail per item with reasoning. Final grade with explicit justification.`

3. **review-skill-cross-validation-full-report** *(complex)*
   `Total-mode review of all skills + agents. Cross-validate references (skills referenced in CLAUDE.md exist; agents referenced in commands exist). Integrate bench_data: [{"category":"review","aggregate":{"score_with_skill":0.85,"score_baseline":0.60,"avg_total_with_skill":20000,"avg_total_baseline":15000,"token_savings_pct":-0.33}}]. Produce full report with summary table, per-category grades, top 3 issues, key observations.`

### `skills/generate/SKILL.md`

1. **generate-skill-claude-md-typescript** *(simple)*
   `Generate a CLAUDE.md for a TypeScript + Express + Prisma + Jest project. Project-tailored, imperative tone, under 200 lines.`

2. **generate-skill-db-migrate** *(medium)*
   `Generate a SKILL.md for a "db-migrate" skill that runs database migrations safely. Include disable-model-invocation if appropriate, allowed-tools, workflow steps, safety rules, and a references/ file pointer for the rollback procedure.`

3. **generate-skill-hooks-and-scripts** *(complex)*
   `Generate a complete hooks.json plus two companion bash scripts: (1) PreToolUse hook blocking 'git push --force' on main; (2) PostToolUse hook running 'npm run lint --silent' after Write edits to .ts files. Include stdin JSON parsing, regex matching, proper exit codes, and a final verification note (chmod +x reminder).`

---

## Agents

### `agents/reviewer.md`

1. **reviewer-agent-basic-frontmatter-audit** *(simple)*
   `Review agents/reviewer.md for baseline compliance. Check required frontmatter fields, description quality, model selection, and tools allowlist per docs/baseline/subagents.md. Produce grade + issues list.`

2. **reviewer-agent-bench-data-integration** *(medium)*
   `Run a targeted review of agents/reviewer.md with this bench_data: [{"category":"reviewer","aggregate":{"score_with_skill":0.88,"score_baseline":0.41,"avg_total_with_skill":14200,"avg_total_baseline":27800,"token_savings_pct":0.489}}]. Produce summary table with the Benchmark column populated (not N/A), per-metric detail table (Pass rate / Avg tokens / Avg duration with N/A rows preserved), and grade adjusted by the bench delta.`

3. **reviewer-agent-cross-validation-full** *(complex)*
   `Full targeted review of agents/reviewer.md. Cross-validate every reference it makes (docs/baseline/*.md files, docs/claude-config-review-report.md, mentioned commands/skills). Verify the report writing path is correct. Integrate bench_data: [{"category":"reviewer","aggregate":{"score_with_skill":0.91,"score_baseline":0.38,"avg_total_with_skill":13100,"avg_total_baseline":29400,"token_savings_pct":0.554}}]. Produce complete report with cross-validation results, benchmark table, grade, and top issues.`

### `agents/generator.md`

1. **generator-agent-claude-md-nextjs** *(simple)*
   `As the generator agent, scaffold a CLAUDE.md for a Next.js 14 App Router project using TypeScript, Tailwind, Prisma, and Vitest. Follow generator agent's 4-step process (Assess → Confirm → Generate → Verify). Show the generated file content plus the verification block.`

2. **generator-agent-skill-and-references** *(medium)*
   `As the generator agent, scaffold a "pr-review" skill with SKILL.md plus one references/heuristics.md file. The skill should automate PR code review (fetch diff, flag issues by severity, post comment). Show both files and verification.`

3. **generator-agent-full-fastapi-setup** *(complex)*
   `As the generator agent, full Claude Code setup for a FastAPI microservice (SQLAlchemy + Alembic + pytest + ruff). Generate: CLAUDE.md, memory/MEMORY.md + 3 typed memory files, agents/api-dev.md subagent with frontmatter and 4 trigger examples, and .claude/settings.json with appropriate allow/deny rules. Show all files plus final verification table.`

### `agents/grader.md`

1. **grader-agent-clear-winner** *(simple)*
   `Grade these eval results inline. Return ONLY the fenced JSON per grader spec — no prose.
{"category":"grader","with_skill":{"samples":[{"eval_name":"grader-basic-json-output","prompt":"Return the grading result as JSON.","output":"\\n\\`\\`\\`json\\n{\\"category\\":\\"grader\\",\\"aggregate\\":{\\"score_with_skill\\":0.9,\\"score_baseline\\":0.4,\\"avg_total_with_skill\\":1200,\\"avg_total_baseline\\":2400,\\"token_savings_pct\\":0.5}}\\n\\`\\`\\`"}],"usage":{"total_tokens":1200,"duration_ms":3000}},"baseline":{"samples":[{"eval_name":"grader-basic-json-output","prompt":"Return the grading result as JSON.","output":"The with_skill version did better, ~0.9 vs 0.4. Token savings ~50%."}],"usage":{"total_tokens":2400,"duration_ms":4500}}}`

2. **grader-agent-both-structured-formula-error** *(medium)*
   `Grade these eval results. Detect any formula errors in computed fields (token_savings_pct = 1 - with/baseline). Return ONLY the JSON.
{"category":"grader","with_skill":{"samples":[{"eval_name":"grader-structured","prompt":"Score and return aggregate JSON.","output":"\\n\\`\\`\\`json\\n{\\"aggregate\\":{\\"score_with_skill\\":0.85,\\"score_baseline\\":0.60,\\"avg_total_with_skill\\":1800,\\"avg_total_baseline\\":2200,\\"token_savings_pct\\":0.18}}\\n\\`\\`\\`"}],"usage":{"total_tokens":1800,"duration_ms":4000}},"baseline":{"samples":[{"eval_name":"grader-structured","prompt":"Score and return aggregate JSON.","output":"\\`\\`\\`json\\n{\\"aggregate\\":{\\"score_with_skill\\":0.85,\\"score_baseline\\":0.60,\\"avg_total_with_skill\\":1800,\\"avg_total_baseline\\":2200,\\"token_savings_pct\\":0.25}}\\n\\`\\`\\`"}],"usage":{"total_tokens":2200,"duration_ms":5000}}}`

3. **grader-agent-multi-rule-in-memory-discipline** *(complex)*
   `Grade these eval results. Apply multi-rule scoring per docs/baseline/subagents.md: rubric coverage, schema fidelity, in-memory discipline (no file writes), formula correctness. Return ONLY the JSON.
{"category":"grader","with_skill":{"samples":[{"eval_name":"grader-full-pipeline","prompt":"Score in-memory only.","output":"\\n\\`\\`\\`json\\n{\\"category\\":\\"grader\\",\\"aggregate\\":{\\"score_with_skill\\":0.92,\\"score_baseline\\":0.35,\\"avg_total_with_skill\\":2100,\\"avg_total_baseline\\":3800,\\"token_savings_pct\\":0.447}}\\n\\`\\`\\`"}],"usage":{"total_tokens":2100,"duration_ms":5500}},"baseline":{"samples":[{"eval_name":"grader-full-pipeline","prompt":"Score in-memory only.","output":"Saved grading-report.txt. with_skill ~0.92, baseline ~0.35, token savings ~45%."}],"usage":{"total_tokens":3800,"duration_ms":7200}}}`

### `agents/eval-runner.md`

1. **eval-runner-agent-skill-target** *(simple)*
   `target_path=skills/review/SKILL.md
mode=with_skill

Follow eval-runner's process: read target, use canonical-prompts from skills/review/references/canonical-prompts.md, execute each, return inline JSON per schema. No file writes.`

2. **eval-runner-agent-baseline-discipline** *(medium)*
   `target_path=agents/grader.md
mode=baseline

Follow eval-runner's process in baseline mode — do NOT load the grader's skill or behaviors; use only general knowledge. Use canonical-prompts. Return inline JSON.`

3. **eval-runner-agent-mixed-targets-end-to-end** *(complex)*
   `target_path=agents/eval-runner.md
mode=with_skill

Self-evaluation: read your own target file, follow your own process, execute canonical prompts, return inline JSON. Ensure no file writes, exact schema, target_path/mode fields correct, samples array contains eval_name/prompt/output per item.`

### `agents/plan-reviewer.md`

1. **plan-reviewer-single-approval** *(simple)*
   `Run 4-step verification for a single plan record. plan.json has R001: proposition="Tool names must be kebab-case", source.quote="all tool names should follow kebab-case conventions for consistency across integrations", verifier.kind="regex", verifier.pattern="^[a-z][a-z0-9-]*$". Checks 1-3 pass programmatically. Fetched body contains the verbatim quote. Produce plan_review.json output with verdict, approved_records, rejected_records, summary.`

2. **plan-reviewer-partial-verifier-mismatch** *(medium)*
   `Run 4-step verification for two records. R002: proposition="Description max length is 64 characters", verifier.kind="regex", verifier.pattern=".{0,100}" (intentional proposition-verifier drift), source.quote="keep descriptions concise, ideally under 64 characters". R003: proposition="Skill frontmatter requires a description field", verifier.kind="yaml-parse" checking for 'description' key, source.quote="Every skill must include a description in its frontmatter." Checks 1-3 pass for both. Produce plan_review.json catching R002's drift.`

3. **plan-reviewer-aborted-self-justification-trap** *(complex)*
   `Run 4-step verification for four records. R004 has hash mismatch in Check 1. R005 has llm-judge rubric="ok" (only 2 chars, fails Check 3 minimum 30). R006 has clean proposition+quote match, all checks should pass. R007 has planner self-justification ("as discussed in PR #2") and proposition "Skills must not exceed 500 lines" but fetched body says "Skills should be kept focused and maintainable" with NO line count specified. Produce plan_review.json — should result in verdict=aborted (75% rejection > 50% threshold) with proper quote_used fields.`

### `agents/self-eval-runner.md`

1. **self-eval-runner-single-programmatic** *(simple)*
   `Run the verifier for item 'skill-name-charset' from refs_path=docs/baseline/skills.md against target_path=skills/review/SKILL.md (target_kind=skill). Return ONLY the JSON array with id/passed/evidence. No commentary, no suggestions, no opinions — thin executor only.`

2. **self-eval-runner-mixed-verifier-types** *(medium)*
   `Run all verifiers for items agent-name-charset (regex), agent-description-present (substring), agent-role-clarity (llm-judge) from refs_path=docs/baseline/subagents.md against target_path=agents/reviewer.md (target_kind=agent). Return ONLY the JSON array. For llm-judge, cite verbatim quote evidence. No interpretation.`

3. **self-eval-runner-full-baseline-doc** *(complex)*
   `Run ALL verifier items from refs_path=docs/baseline/claude-md.md against target_path=CLAUDE.md (target_kind=claude-md). Includes file-exists, line-count, regex (no-secrets), and llm-judge items (has-project-context, routing-present, constraints-present). Return ONLY the JSON array — no commentary, no recommendations, no opinions.`
