"""U5 Self-validate: compute B (regression) and C (ratio drop) signals."""
from dataclasses import dataclass


@dataclass
class BSignal:
    regressions: list[str]


@dataclass
class CSignal:
    prev_ratio: float | None
    curr_ratio: float | None
    dropped: bool


@dataclass
class Signals:
    b_signal: BSignal
    c_signal: CSignal


C_DROP_THRESHOLD = 0.20  # 절대 차이 (ratio 0.5 → 0.3 = 0.20 dropped)


def _ratio(metric: dict | None) -> float | None:
    if not metric:
        return None
    bl = metric.get("baseline")
    if not bl or bl == 0:
        return None
    return (metric["with_skill"] - bl) / bl


def compute_signals(
    prev_results: list[dict],
    curr_results: list[dict],
    *,
    prev_metric: dict | None = None,
    curr_metric: dict | None = None,
) -> Signals:
    prev_pass = {r["id"]: r["passed"] for r in prev_results}
    curr_pass = {r["id"]: r["passed"] for r in curr_results}

    regressions = [
        item_id
        for item_id, prev_p in prev_pass.items()
        if prev_p and item_id in curr_pass and not curr_pass[item_id]
    ]
    b = BSignal(regressions=regressions)

    prev_r = _ratio(prev_metric)
    curr_r = _ratio(curr_metric)
    dropped = (
        prev_r is not None
        and curr_r is not None
        and (prev_r - curr_r) >= C_DROP_THRESHOLD
    )
    c = CSignal(prev_ratio=prev_r, curr_ratio=curr_r, dropped=dropped)

    return Signals(b_signal=b, c_signal=c)
