"""U1 Fetch: WebFetch wrapper for docs/changelog/sitemap."""
from datetime import datetime, timezone
from pathlib import Path

import httpx


def fetch_category(name: str, url: str, *, out_dir: Path) -> Path:
    """Fetch a docs page; raise on non-200."""
    out_dir.mkdir(parents=True, exist_ok=True)
    resp = httpx.get(url, follow_redirects=True, timeout=60.0)
    resp.raise_for_status()
    out = out_dir / f"{name}.md"
    out.write_text(resp.text, encoding="utf-8")
    # sidecar metadata for fetched_at
    (out_dir / f"{name}.meta.txt").write_text(
        f"url={url}\nfetched_at={datetime.now(timezone.utc).isoformat()}\nstatus={resp.status_code}\n"
    )
    return out


def fetch_sitemap(*, out_dir: Path, sitemap_url: str = "https://code.claude.com/docs/llms.txt") -> Path:
    out_dir.mkdir(parents=True, exist_ok=True)
    resp = httpx.get(sitemap_url, follow_redirects=True, timeout=60.0)
    resp.raise_for_status()
    out = out_dir / "sitemap.txt"
    out.write_text(resp.text, encoding="utf-8")
    return out


def fetch_changelog(*, out_dir: Path) -> Path:
    return fetch_category("_changelog", "https://code.claude.com/docs/en/changelog", out_dir=out_dir)
