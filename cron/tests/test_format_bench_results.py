from pathlib import Path
import json
from scripts.format_bench_results import format_bench


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
