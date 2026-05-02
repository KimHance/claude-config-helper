from pathlib import Path

import pytest

from scripts.nav_fetch import (
    NavExtractError,
    extract_docs_config,
    extract_pages_to_fetch,
    fetch_page_md,
    slug_safe,
)

FIXTURES = Path(__file__).parent / "fixtures"


def test_extract_docs_config_from_sample_html():
    html = (FIXTURES / "sample-hydrate.html").read_text()
    nav = extract_docs_config(html)
    assert "languages" in nav
    en = next(l for l in nav["languages"] if l["language"] == "en")
    assert len(en["tabs"]) == 2


def test_extract_docs_config_raises_on_no_chunk():
    with pytest.raises(NavExtractError):
        extract_docs_config("<html><body>no chunks here</body></html>")


def test_extract_docs_config_raises_on_malformed_chunk():
    html = '<script>self.__next_f.push([1,"docsConfig but not json"])</script>'
    with pytest.raises(NavExtractError):
        extract_docs_config(html)


def test_extract_pages_excludes_tabs():
    nav = {
        "languages": [{
            "language": "en",
            "tabs": [
                {"tab": "Build with Claude Code", "groups": [
                    {"group": "Agents", "pages": ["en/sub-agents", "en/agent-teams"]}
                ]},
                {"tab": "Agent SDK", "groups": [
                    {"group": "SDK", "pages": ["en/agent-sdk/overview"]}
                ]},
            ]
        }]
    }
    out = extract_pages_to_fetch(nav, excluded_tabs=["Agent SDK"])
    assert out["tabs"][0]["tab"] == "Build with Claude Code"
    assert len(out["tabs"]) == 1
    pages = [p for tab in out["tabs"] for grp in tab["groups"] for p in grp["pages"]]
    assert "en/sub-agents" in pages
    assert "en/agent-sdk/overview" not in pages


def test_slug_safe():
    assert slug_safe("Build with Claude Code") == "build-with-claude-code"
    assert slug_safe("Tools and plugins") == "tools-and-plugins"
    assert slug_safe("Settings & Permissions!") == "settings-permissions"


def test_fetch_page_md_appends_md_suffix(tmp_path, httpx_mock):
    httpx_mock.add_response(
        url="https://code.claude.com/docs/en/skills.md",
        text="# Skills\n\nbody",
    )
    out = fetch_page_md("en/skills", tmp_path)
    assert out.name == "en__skills.md"
    assert "# Skills" in out.read_text()
