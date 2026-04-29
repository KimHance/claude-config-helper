"""CLI entry: B/C signal computation."""
import argparse
import json
from dataclasses import asdict
from pathlib import Path

from scripts.self_validate import compute_signals


def _read_or_empty(path: Path):
    if not path or not path.exists():
        return None
    return json.loads(path.read_text())


def _to_metric(eval_list, baseline_data):
    """
    Compute {with_skill, baseline} pass-rate metric.

    self-eval-runner emits both self_eval.json and baseline_eval.json as
    JSON arrays of {id, passed, evidence}. Convert two arrays into a single
    metric dict by computing pass rate of each. If baseline is already a
    metric dict (legacy/manual), pass through.
    """
    if not eval_list or not baseline_data:
        return None
    if isinstance(baseline_data, dict):
        return baseline_data
    if isinstance(eval_list, list) and isinstance(baseline_data, list):
        if not eval_list or not baseline_data:
            return None
        with_pass = sum(1 for r in eval_list if r.get("passed")) / len(eval_list)
        bl_pass = sum(1 for r in baseline_data if r.get("passed")) / len(baseline_data)
        return {"with_skill": with_pass, "baseline": bl_pass}
    return None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--prev-eval", type=Path)
    ap.add_argument("--curr-eval", required=True, type=Path)
    ap.add_argument("--prev-metric", type=Path)
    ap.add_argument("--curr-metric", type=Path)
    ap.add_argument("--out", required=True, type=Path)
    args = ap.parse_args()

    prev_eval = _read_or_empty(args.prev_eval) or []
    curr_eval = _read_or_empty(args.curr_eval) or []
    prev_metric_raw = _read_or_empty(args.prev_metric)
    curr_metric_raw = _read_or_empty(args.curr_metric)

    prev_metric = _to_metric(prev_eval, prev_metric_raw)
    curr_metric = _to_metric(curr_eval, curr_metric_raw)

    signals = compute_signals(prev_eval, curr_eval, prev_metric=prev_metric, curr_metric=curr_metric)
    args.out.write_text(
        json.dumps(
            {
                "b_signal": asdict(signals.b_signal),
                "c_signal": asdict(signals.c_signal),
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
