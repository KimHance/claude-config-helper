# Grading Rubric for Eval Benchmarks

## Assertion Design Principles

- **Objectively verifiable**: Each assertion must be checkable against concrete output
- **Descriptive naming**: Names clarify what's tested (e.g., "skill-md-under-500-lines" not "length-check")
- **Non-redundant**: Remove assertions that always pass/fail regardless of skill version

## Assertion Examples by Category

### CLAUDE.md
- `claude-md-exists`: CLAUDE.md file was generated
- `claude-md-under-200-lines`: File stays concise
- `claude-md-imperative-tone`: Uses imperative voice, not narrative
- `claude-md-has-routing`: Contains routing/delegation rules
- `claude-md-no-stale-refs`: All referenced files actually exist

### Skills
- `skill-md-has-frontmatter`: Has name and description in frontmatter
- `skill-md-description-has-when`: Description explains when to trigger
- `skill-md-under-500-lines`: SKILL.md stays lean
- `skill-has-references-dir`: Uses progressive disclosure with references/
- `skill-refs-exist`: All referenced files actually exist

### Agents
- `agent-has-frontmatter`: Has name, description, model fields
- `agent-has-examples`: Description includes trigger examples
- `agent-model-justified`: Model choice matches workload complexity
- `agent-has-workflow`: Contains step-by-step workflow

### Commands
- `command-has-frontmatter`: Has description field
- `command-delegates`: Complex commands delegate to agents/skills

## grading.json Format

```json
{
  "eval_id": 0,
  "eval_name": "descriptive-name",
  "with_skill": [
    { "text": "assertion description", "passed": true, "evidence": "concrete reason" }
  ],
  "baseline": [
    { "text": "assertion description", "passed": false, "evidence": "concrete reason" }
  ],
  "analyst_notes": "observations about patterns, non-discriminating assertions, variance"
}
```

**Field names are strict**: `text`, `passed`, `evidence`. No alternatives.

## Grading Thresholds for Review Report

| Pass Rate | Benchmark Grade |
|-----------|----------------|
| 90-100%   | A              |
| 75-89%    | B              |
| 60-74%    | C              |
| 40-59%    | D              |
| 0-39%     | F              |
