---
name: gn-rv
description: End-to-end orchestration — generates Claude config files, then reviews them with benchmark evaluation for quality
---

# Claude Config Setup (Generate + Review + Benchmark)

Orchestrates a full Claude configuration workflow: generate files, benchmark-evaluate them, and iterate until satisfactory.

## Workflow

### Phase 1: Generate

Spawn the `generator` subagent to create configuration files.

1. Assess the project's tech stack and structure
2. Determine which config files are needed
3. Generate files using templates from `generate` skill
4. Verify generated files for consistency

**Wait for generation to complete before proceeding.**

### Phase 2: Snapshot (if updating)

If modifying existing skills or agents (not creating from scratch):
1. Copy the original skill/agent to `/tmp/cchelp-eval-<name>/skill-snapshot/`
2. This snapshot serves as the baseline for benchmark comparison

### Phase 3: Review + Benchmark

Spawn the `reviewer` subagent with full benchmark evaluation.

The reviewer will:
1. Scan all generated Claude-related files
2. Evaluate each category against checklists from `review` skill
3. For Skills/Subagents: run parallel eval (with-skill + baseline simultaneously)
4. Grade each category incorporating benchmark results
5. Embed benchmark tables in the review report
6. Clean up `/tmp/cchelp-eval-*/` cache

### Phase 4: Iterate (user-driven)

After review results are presented:

1. Ask the user: "수정할 부분이 있으면 말씀해주세요. 만족하시면 완료합니다."
2. If changes requested:
   - Spawn `generator` again with targeted fixes
   - Re-run Phase 3 (new iteration in the benchmark)
   - Present updated results
   - Ask again
3. If satisfied: proceed to Phase 5

This is not an automatic loop — every iteration requires explicit user approval.

### Phase 5: Description Optimize (optional)

When all grades are satisfactory, offer trigger optimization:

1. Ask: "description 트리거 정확도도 최적화할까요?"
2. If accepted:
   - Generate 20 test queries (10 should-trigger, 10 should-not-trigger)
   - Split 60% train / 40% test
   - Evaluate and optimize description (3 runs per query, max 5 iterations)
   - Select best by test score
   - Present before/after comparison with scores
   - Apply if user approves
3. If declined: complete

## Output

- Generated config files in their target paths
- Terminal summary table with grades and benchmark deltas
- Detailed report at `docs/claude-config-review-report.md` with embedded benchmark tables
- Optimized descriptions (if Phase 5 was accepted)
