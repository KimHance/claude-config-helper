---
name: gn-rv
description: |
  End-to-end Claude config orchestration — generates config files then reviews them for quality.
  <example>user: "클로드 세팅 만들고 리뷰까지 해줘" assistant: uses gn-rv skill</example>
  <example>user: "generate and review claude config" assistant: uses gn-rv skill</example>
  <example>user: "설정 파일 생성하고 검증해줘" assistant: uses gn-rv skill</example>
---

# Claude Config Setup (Generate + Review)

Orchestrates a full Claude configuration workflow: generate files first, then review them for quality.

## Workflow

### Phase 1: Generate

Spawn the `generator` subagent to create configuration files.

1. Assess the project's tech stack and structure
2. Determine which config files are needed
3. Generate files using templates from `generate` skill
4. Verify generated files for consistency

**Wait for generation to complete before proceeding.**

### Phase 2: Review

Spawn the `reviewer` subagent to audit the generated files.

1. Scan all generated Claude-related files
2. Evaluate each category against checklists from `review` skill
3. Cross-validate references between files
4. Grade each category (A–F)
5. Output summary table + detailed report

### Phase 3: Fix (if needed)

If the review finds **Critical** or **Important** issues:

1. Present the issues to the user
2. Ask whether to auto-fix or skip
3. If auto-fix: spawn `generator` again with targeted fixes
4. If skip: leave as-is with the review report for manual follow-up

## Output

- Generated config files in their target paths
- Terminal summary table with grades
- Detailed report at `docs/claude-config-review-report.md`
- List of any remaining issues (if fix was skipped)
