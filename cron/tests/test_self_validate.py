from scripts.self_validate import compute_signals, BSignal, CSignal


def test_no_regression_no_b_signal():
    prev = [{"id": "a", "passed": True}, {"id": "b", "passed": True}]
    curr = [{"id": "a", "passed": True}, {"id": "b", "passed": True}]
    b = compute_signals(prev, curr).b_signal
    assert b.regressions == []


def test_regression_detected():
    prev = [{"id": "a", "passed": True}, {"id": "b", "passed": True}]
    curr = [{"id": "a", "passed": True}, {"id": "b", "passed": False}]
    b = compute_signals(prev, curr).b_signal
    assert "b" in b.regressions


def test_new_failures_not_regression():
    """직전 cron 에 없던 새 항목이 fail 인 건 회귀가 아님."""
    prev = [{"id": "a", "passed": True}]
    curr = [{"id": "a", "passed": True}, {"id": "new", "passed": False}]
    b = compute_signals(prev, curr).b_signal
    assert "new" not in b.regressions


def test_c_signal_ratio_drop():
    prev_metric = {"with_skill": 0.9, "baseline": 0.4}  # ratio = (0.9-0.4)/0.4 = 1.25
    curr_metric = {"with_skill": 0.6, "baseline": 0.5}  # ratio = (0.6-0.5)/0.5 = 0.20
    c = compute_signals([], [], prev_metric=prev_metric, curr_metric=curr_metric).c_signal
    # 1.25 → 0.20, 절대 차이 = 1.05, 퍼센트로 105 → 임계값 0.20 절대 초과
    assert c.dropped


def test_c_signal_stable():
    prev_metric = {"with_skill": 0.9, "baseline": 0.4}
    curr_metric = {"with_skill": 0.92, "baseline": 0.4}
    c = compute_signals([], [], prev_metric=prev_metric, curr_metric=curr_metric).c_signal
    assert not c.dropped
