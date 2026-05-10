"""Aggregate per-sample (with-skill, baseline, grader) results into grading.json."""
from __future__ import annotations
import json
import sys
from pathlib import Path


def aggregate_grading(category: str, samples: list[dict]) -> dict:
    n = len(samples)
    if n == 0:
        return {
            "category": category,
            "samples": [],
            "aggregate": {
                "score_with_skill": 0,
                "score_baseline": 0,
                "avg_total_with_skill": 0,
                "avg_total_baseline": 0,
                "token_savings_pct": 0.0,
            },
        }
    sum_with_score = sum(s["with_skill"]["score"] for s in samples)
    sum_base_score = sum(s["baseline"]["score"] for s in samples)
    sum_with_total = sum(
        s["with_skill"]["usage"].get("input", 0) + s["with_skill"]["usage"].get("output", 0)
        for s in samples
    )
    sum_base_total = sum(
        s["baseline"]["usage"].get("input", 0) + s["baseline"]["usage"].get("output", 0)
        for s in samples
    )
    return {
        "category": category,
        "samples": samples,
        "aggregate": {
            "score_with_skill": sum_with_score / n,
            "score_baseline": sum_base_score / n,
            "avg_total_with_skill": sum_with_total // n,
            "avg_total_baseline": sum_base_total // n,
            "token_savings_pct": (1 - sum_with_total / sum_base_total) if sum_base_total else 0.0,
        },
    }


def main() -> int:
    print(
        "run_benchmark.py: aggregator only. End-to-end reviewer/grader spawn lives in workflow YAML.",
        file=sys.stderr,
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
