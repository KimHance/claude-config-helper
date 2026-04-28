from pathlib import Path

from scripts.fetch import fetch_category, fetch_sitemap


def test_fetch_category_writes_file(tmp_path, httpx_mock):
    httpx_mock.add_response(
        url="https://code.claude.com/docs/en/skills",
        text="# Skills\n\nFrontmatter content here.",
    )
    out = fetch_category("skills", "https://code.claude.com/docs/en/skills", out_dir=tmp_path)
    assert out.exists()
    assert "Skills" in out.read_text()


def test_fetch_category_404_raises(tmp_path, httpx_mock):
    import httpx
    import pytest
    httpx_mock.add_response(url="https://code.claude.com/docs/en/skills", status_code=404)
    with pytest.raises(httpx.HTTPStatusError):
        fetch_category("skills", "https://code.claude.com/docs/en/skills", out_dir=tmp_path)


def test_fetch_sitemap_writes_snapshot(tmp_path, httpx_mock):
    httpx_mock.add_response(
        url="https://code.claude.com/docs/llms.txt",
        text="https://code.claude.com/docs/en/skills.md\nhttps://code.claude.com/docs/en/hooks.md",
    )
    out = fetch_sitemap(out_dir=tmp_path)
    assert out.exists()
    body = out.read_text()
    assert "skills.md" in body
