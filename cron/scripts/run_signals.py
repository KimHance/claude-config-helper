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
    prev_metric = _read_or_empty(args.prev_metric)
    curr_metric = _read_or_empty(args.curr_metric)

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
