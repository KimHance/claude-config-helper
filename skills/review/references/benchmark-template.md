# Benchmark Report Template

## Format for benchmark.json

```json
{
  "skill_name": "<skill-name>",
  "iteration": 1,
  "timestamp": "<ISO 8601>",
  "summary": {
    "total_evals": 3,
    "with_skill": {
      "pass_rate": 0.85,
      "avg_tokens": 12345,
      "std_tokens": 567,
      "avg_duration_ms": 5000,
      "std_duration_ms": 200
    },
    "baseline": {
      "pass_rate": 0.45,
      "avg_tokens": 23456,
      "std_tokens": 789,
      "avg_duration_ms": 8000,
      "std_duration_ms": 300
    },
    "delta": {
      "pass_rate": "+40%",
      "tokens": "-47%",
      "duration": "-37%"
    }
  },
  "per_eval": [
    {
      "eval_name": "descriptive-name",
      "with_skill_pass_rate": 1.0,
      "baseline_pass_rate": 0.5,
      "with_skill_tokens": 10000,
      "baseline_tokens": 20000,
      "with_skill_duration_ms": 4000,
      "baseline_duration_ms": 7000
    }
  ],
  "analyst_observations": [
    "assertion 'X' passed in both runs — non-discriminating",
    "eval 'Y' showed high variance — possibly flaky"
  ]
}
```

## Format for Review Report Benchmark Section

When embedding in `docs/claude-config-review-report.md`, use this template per category:

```markdown
#### Benchmark: <skill-or-agent-name>

| Metric | With Skill | Baseline | Delta |
|--------|-----------|----------|-------|
| Pass rate | 85% | 45% | +40% |
| Avg tokens | 12,345 | 23,456 | -47% |
| Avg duration | 5.0s | 8.0s | -37% |

<details>
<summary>Per-eval breakdown</summary>

| Eval | W/ Skill | Baseline |
|------|----------|----------|
| claude-md-generation | 3/3 pass | 1/3 pass |
| skill-scaffold-quality | 2/3 pass | 1/3 pass |

</details>

<details>
<summary>Analyst notes</summary>

- assertion 'X' non-discriminating (passed both)
- eval 'Y' high variance

</details>
```

## timing.json Format

Captured immediately when each subagent completes:

```json
{
  "total_tokens": 84852,
  "duration_ms": 23332,
  "total_duration_seconds": 23.3
}
```
