from scripts.run_benchmark import aggregate_grading


def test_aggregate_grading_computes_savings():
    samples = [
        {"with_skill": {"score": 0.9, "usage": {"input": 4000, "output": 400}},
         "baseline":   {"score": 0.7, "usage": {"input": 12000, "output": 400}}},
    ]
    out = aggregate_grading("skills", samples)
    assert out["category"] == "skills"
    assert out["aggregate"]["score_with_skill"] == 0.9
    assert out["aggregate"]["score_baseline"] == 0.7
    assert out["aggregate"]["avg_total_with_skill"] == 4400
    assert out["aggregate"]["avg_total_baseline"] == 12400
    assert round(out["aggregate"]["token_savings_pct"], 3) == round(1 - 4400/12400, 3)


def test_aggregate_grading_two_samples_averages():
    samples = [
        {"with_skill": {"score": 1.0, "usage": {"input": 1000, "output": 100}},
         "baseline":   {"score": 0.5, "usage": {"input": 2000, "output": 100}}},
        {"with_skill": {"score": 0.0, "usage": {"input": 3000, "output": 100}},
         "baseline":   {"score": 0.5, "usage": {"input": 4000, "output": 100}}},
    ]
    out = aggregate_grading("subagents", samples)
    assert out["aggregate"]["score_with_skill"] == 0.5
    assert out["aggregate"]["score_baseline"] == 0.5
    # avg_total: with = (1100+3100)/2 = 2100; base = (2100+4100)/2 = 3100
    assert out["aggregate"]["avg_total_with_skill"] == 2100
    assert out["aggregate"]["avg_total_baseline"] == 3100


def test_aggregate_grading_empty_samples_safe():
    out = aggregate_grading("skills", [])
    assert out["category"] == "skills"
    assert out["aggregate"]["score_with_skill"] == 0
    assert out["aggregate"]["token_savings_pct"] == 0.0
