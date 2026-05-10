from pathlib import Path
import json
from scripts.format_bench_results import format_bench, format_bench_from_data


def test_format_bench_marks_suspicious(tmp_path: Path):
    grading_dir = tmp_path / "bench"
    (grading_dir / "skills").mkdir(parents=True)
    (grading_dir / "skills" / "grading.json").write_text(json.dumps({
        "category": "skills",
        "aggregate": {
            "score_with_skill": 0.6, "score_baseline": 0.7,
            "avg_total_with_skill": 14000, "avg_total_baseline": 12000,
            "token_savings_pct": -0.166,
        },
    }))
    out = format_bench(grading_dir)
    assert out["bench_quality_suspicious"] is True
    assert out["bench_efficiency_suspicious"] is True
    assert "skills" in out["markdown"]


def test_format_bench_empty_dir(tmp_path: Path):
    out = format_bench(tmp_path)
    assert out["bench_present"] is False
    assert out["markdown"].strip() == ""


def test_format_bench_from_data_inline():
    gradings = [
        {"category": "skills",
         "aggregate": {"score_with_skill": 0.9, "score_baseline": 0.5,
                       "avg_total_with_skill": 4000, "avg_total_baseline": 12000,
                       "token_savings_pct": 0.667}},
        {"category": "subagents",
         "aggregate": {"score_with_skill": 0.4, "score_baseline": 0.6,
                       "avg_total_with_skill": 15000, "avg_total_baseline": 10000,
                       "token_savings_pct": -0.5}},
    ]
    out = format_bench_from_data(gradings)
    assert out["bench_present"] is True
    assert out["bench_quality_suspicious"] is True   # subagents w<base
    assert out["bench_efficiency_suspicious"] is True  # subagents w>base tokens
    assert "skills" in out["markdown"] and "subagents" in out["markdown"]


def test_format_bench_from_data_empty():
    out = format_bench_from_data([])
    assert out["bench_present"] is False
    assert out["markdown"].strip() == ""
