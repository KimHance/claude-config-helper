import json
from pathlib import Path
from unittest.mock import patch

import yaml

from scripts.run_apply import main


def test_run_apply_preserves_additional_sources(tmp_path):
    """run_apply 가 payload 의 additional_sources 를 yml 에 그대로 직렬화."""
    plan = [
        {
            "category": "hooks",
            "action": "ADD",
            "item_id": "hook-x",
            "payload": {
                "id": "hook-x",
                "type": "qualitative",
                "proposition": "p",
                "verifier": {"kind": "llm-judge", "rubric": "r" * 30},
                "source": {
                    "url": "https://docs/hooks",
                    "fetched_at": "2026-05-02T00:00:00Z",
                    "quote": "main quote here",
                },
                "additional_sources": [
                    {
                        "url": "https://docs/hooks-guide",
                        "fetched_at": "2026-05-02T00:00:00Z",
                        "quote": "extra guide quote",
                    }
                ],
                "severity": "critical",
                "category": "hooks",
            },
        }
    ]
    review = {"approved": ["hook-x"]}
    refs_dir = tmp_path / "refs"
    refs_dir.mkdir()

    plan_file = tmp_path / "plan.json"
    plan_file.write_text(json.dumps(plan))
    review_file = tmp_path / "review.json"
    review_file.write_text(json.dumps(review))

    # Call main() with patched sys.argv
    with patch("sys.argv", [
        "run_apply",
        "--plan", str(plan_file),
        "--review", str(review_file),
        "--refs-dir", str(refs_dir),
    ]):
        main()

    hooks_yml = refs_dir / "hooks.yml"
    assert hooks_yml.exists()
    items = yaml.safe_load(hooks_yml.read_text())
    assert len(items) == 1
    assert items[0]["additional_sources"][0]["url"] == "https://docs/hooks-guide"
