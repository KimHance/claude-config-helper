"""Compose PR-body bench section + suspicion flags. No threshold gating."""
from __future__ import annotations
import json
import sys
from pathlib import Path


def format_bench_from_data(gradings: list[dict]) -> dict:
    """Format bench summary from a list of grading dicts (in-memory path).

    Each item must have shape: {"category": str, "aggregate": {...}}.
    """
    rows: list[str] = []
    suspicious_q = False
    suspicious_e = False
    for g in sorted(gradings, key=lambda x: x.get("category", "")):
        a = g.get("aggregate", {})
        with_q, base_q = a.get("score_with_skill"), a.get("score_baseline")
        with_t, base_t = a.get("avg_total_with_skill"), a.get("avg_total_baseline")
        savings = a.get("token_savings_pct", 0.0)
        if with_q is not None and base_q is not None and with_q < base_q:
            suspicious_q = True
        if with_t is not None and base_t is not None and with_t > base_t:
            suspicious_e = True
        rows.append(f"| {g['category']} | {with_q:.2f} / {base_q:.2f} | {with_t:,} / {base_t:,} | {savings*100:+.0f}% |")
    md = ""
    if rows:
        md = (
            "| 카테고리 | 품질 (with / base) | 평균 토큰 (with / base) | 절감 |\n"
            "|---|---|---|---|\n" + "\n".join(rows) + "\n"
        )
    return {
        "bench_present": bool(rows),
        "bench_quality_suspicious": suspicious_q,
        "bench_efficiency_suspicious": suspicious_e,
        "markdown": md,
    }


def format_bench(grading_dir: Path) -> dict:
    """File-based path. Reads grading.json files from subdirs of grading_dir."""
    gradings: list[dict] = []
    for cat_dir in sorted(p for p in grading_dir.iterdir() if p.is_dir()):
        gf = cat_dir / "grading.json"
        if not gf.exists():
            continue
        gradings.append(json.loads(gf.read_text()))
    return format_bench_from_data(gradings)


def main() -> int:
    # Two CLI modes:
    #   format_bench_results.py <grading_dir> <out_summary.json>   (file-based)
    #   format_bench_results.py --inline <out_summary.json>         (read JSON list from stdin)
    if len(sys.argv) == 3 and sys.argv[1] == "--inline":
        gradings = json.loads(sys.stdin.read())
        out = format_bench_from_data(gradings)
        Path(sys.argv[2]).write_text(json.dumps(out, indent=2))
        print(out["markdown"])
        return 0
    if len(sys.argv) == 3:
        out = format_bench(Path(sys.argv[1]))
        Path(sys.argv[2]).write_text(json.dumps(out, indent=2))
        print(out["markdown"])
        return 0
    print("Usage: format_bench_results.py <grading_dir> <out_summary.json>\n"
          "       format_bench_results.py --inline <out_summary.json>  (stdin = JSON list)",
          file=sys.stderr)
    return 2


if __name__ == "__main__":
    sys.exit(main())
