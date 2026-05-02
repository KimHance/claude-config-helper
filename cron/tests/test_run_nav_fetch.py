from pathlib import Path

from scripts.nav_fetch import write_nav_json


def test_write_nav_json_minimal(tmp_path):
    structure = {
        "language": "en",
        "tabs": [
            {"tab": "Reference", "groups": [{"group": "R", "pages": ["en/r"]}]}
        ],
        "excluded_tabs": [],
    }
    out = tmp_path / "nav.json"
    write_nav_json(structure, out, source="https://x")
    import json
    data = json.loads(out.read_text())
    assert data["language"] == "en"
    assert data["source"] == "https://x"
    assert "fetched_at" in data
