import re
from pathlib import Path

import yaml

AGENTS_DIR = Path(__file__).parent.parent.parent / "agents"
FRONTMATTER_RE = re.compile(r"^---\s*\n(.*?)\n---\s*\n", re.DOTALL)


def _read_frontmatter(path: Path) -> dict:
    m = FRONTMATTER_RE.match(path.read_text(encoding="utf-8"))
    assert m, f"{path} has no frontmatter"
    return yaml.safe_load(m.group(1))


def test_self_eval_runner_exists():
    path = AGENTS_DIR / "self-eval-runner.md"
    assert path.exists(), f"{path} not found"


def test_self_eval_runner_frontmatter():
    fm = _read_frontmatter(AGENTS_DIR / "self-eval-runner.md")
    assert fm["name"] == "self-eval-runner"
    assert "thin executor" in fm["description"].lower()
    assert fm["model"] in {"haiku", "sonnet", "inherit"}, "thin executor should use cheap model"


def test_self_eval_runner_has_workflow_section():
    body = (AGENTS_DIR / "self-eval-runner.md").read_text(encoding="utf-8")
    assert "## Process" in body or "## Workflow" in body
    assert "verifier" in body.lower()
    assert "no llm judgment" in body.lower() or "no opinion" in body.lower() or "기계" in body
