"""CLI entry: Save state for next cron run.

Copies key pipeline outputs to cron/state/ so the next weekly run can
compute B/C signals against prior results.
"""
import argparse
import shutil
from pathlib import Path


def main():
    ap = argparse.ArgumentParser(
        description="Save pipeline state files for the next cron run."
    )
    ap.add_argument("--fetched-dir", required=True, type=Path,
                    help="Directory containing fetched outputs (must have sitemap.txt)")
    ap.add_argument("--curr-eval", required=True, type=Path,
                    help="Current self_eval.json path")
    ap.add_argument("--curr-metric", required=True, type=Path,
                    help="Current baseline_eval.json path")
    ap.add_argument("--state-dir", required=True, type=Path,
                    help="State directory to write into (e.g. cron/state)")
    args = ap.parse_args()

    args.state_dir.mkdir(parents=True, exist_ok=True)

    copies = [
        (args.fetched_dir / "sitemap.txt", args.state_dir / "sitemap.snapshot.txt"),
        (args.curr_eval, args.state_dir / "last_self_eval.json"),
        (args.curr_metric, args.state_dir / "last_metric.json"),
    ]

    for src, dst in copies:
        if src.exists():
            shutil.copy2(src, dst)
            print(f"saved {src} -> {dst}")
        else:
            print(f"skip (not found): {src}")


if __name__ == "__main__":
    main()
