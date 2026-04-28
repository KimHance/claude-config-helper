"""Line-count verifier."""
from pathlib import Path


def check_line_count(item: dict, *, base_dir: Path) -> tuple[bool, str]:
    spec = item["verifier"]
    target = base_dir / spec["target"]
    max_lines = spec["max"]
    min_lines = spec.get("min", 0)

    if not target.exists():
        return False, f"target {spec['target']} not found in {base_dir}"
    n = sum(1 for _ in target.read_text(encoding="utf-8").splitlines())
    if n > max_lines:
        return False, f"{spec['target']} has {n} lines, exceeds max {max_lines}"
    if n < min_lines:
        return False, f"{spec['target']} has {n} lines, below min {min_lines}"
    return True, f"{spec['target']} has {n} lines (within [{min_lines}, {max_lines}])"
