"""file-exists and substring verifiers."""
from pathlib import Path


def check_file_exists(item: dict, *, base_dir: Path) -> tuple[bool, str]:
    spec = item["verifier"]
    target = base_dir / spec["target"]
    if target.exists():
        return True, f"{spec['target']} exists"
    return False, f"{spec['target']} not found in {base_dir}"


def check_substring(item: dict, *, base_dir: Path) -> tuple[bool, str]:
    spec = item["verifier"]
    target = base_dir / spec["target"]
    if not target.exists():
        return False, f"target {spec['target']} not found in {base_dir}"
    body = target.read_text(encoding="utf-8")
    if spec["needle"] in body:
        return True, f"needle found in {spec['target']}"
    return False, f"needle {spec['needle']!r} not found in {spec['target']}"
