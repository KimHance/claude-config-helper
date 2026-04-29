from pathlib import Path

from scripts.category_discovery import (
    CategoryCandidate,
    diff_sitemap,
    extract_md_urls,
    is_review_worthy,
)


def test_diff_finds_new_pages():
    old = "https://code.claude.com/docs/en/skills.md\nhttps://code.claude.com/docs/en/hooks.md"
    new = old + "\nhttps://code.claude.com/docs/en/agent-teams.md"
    diff = diff_sitemap(old, new)
    assert any("agent-teams" in url for url in diff.added)
    assert diff.removed == []


def test_extract_md_urls_handles_markdown_link_format():
    """llms.txt 의 실제 형식 (markdown link list)."""
    body = """# Claude Code Docs

- [Skills](https://code.claude.com/docs/en/skills.md): description here
- [Hooks](https://code.claude.com/docs/en/hooks.md): another description
"""
    urls = extract_md_urls(body)
    assert "https://code.claude.com/docs/en/skills.md" in urls
    assert "https://code.claude.com/docs/en/hooks.md" in urls
    assert len(urls) == 2


def test_diff_sitemap_markdown_link_format():
    """diff_sitemap 이 markdown-link sitemap 에서도 작동해야 함."""
    old = "- [Skills](https://code.claude.com/docs/en/skills.md): old"
    new = """- [Skills](https://code.claude.com/docs/en/skills.md): old
- [Agent Teams](https://code.claude.com/docs/en/agent-teams.md): new"""
    diff = diff_sitemap(old, new)
    assert any("agent-teams" in url for url in diff.added)
    assert diff.removed == []


def test_is_review_worthy_frontmatter_table_yes():
    body = """
# Agent Teams

## Frontmatter reference

| Field | Required | Description |
| :--- | :--- | :--- |
| `name` | Yes | ... |
"""
    assert is_review_worthy(body)


def test_is_review_worthy_quickstart_no():
    body = """
# Quickstart Tutorial

This is a getting-started guide. Just follow these steps.
"""
    assert not is_review_worthy(body)


def test_is_review_worthy_overview_with_no_schema_no():
    body = """
# Overview

This is general information about Claude Code without any frontmatter table or schema.
"""
    assert not is_review_worthy(body)
