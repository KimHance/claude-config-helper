from pathlib import Path

from scripts.category_discovery import (
    CategoryCandidate,
    diff_sitemap,
    is_review_worthy,
)


def test_diff_finds_new_pages():
    old = "https://code.claude.com/docs/en/skills.md\nhttps://code.claude.com/docs/en/hooks.md"
    new = old + "\nhttps://code.claude.com/docs/en/agent-teams.md"
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
