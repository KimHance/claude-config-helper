"""CLI entry: category auto-discovery."""
import argparse
import json
import re
from pathlib import Path

import httpx
import yaml

from scripts.category_discovery import diff_sitemap, is_review_worthy


def _load_known_urls(mapping_path: Path | None) -> set[str]:
    """Return set of docs_url already declared in criteria-mapping.yml."""
    if not mapping_path or not mapping_path.exists():
        return set()
    data = yaml.safe_load(mapping_path.read_text()) or {}
    return {entry["docs_url"].rstrip("/") for entry in data.get("mappings", []) if entry.get("docs_url")}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--new-sitemap", required=True, type=Path)
    ap.add_argument("--prev-sitemap", required=False, type=Path)
    ap.add_argument(
        "--mapping",
        required=False,
        type=Path,
        help="criteria-mapping.yml path; URLs already in mapping are excluded from discovery",
    )
    ap.add_argument("--out", required=True, type=Path)
    args = ap.parse_args()

    new = args.new_sitemap.read_text()
    prev = args.prev_sitemap.read_text() if args.prev_sitemap and args.prev_sitemap.exists() else ""

    diff = diff_sitemap(prev, new)
    known = _load_known_urls(args.mapping)

    discovered = []
    for url in diff.added:
        if not url.endswith(".md"):
            continue
        # mapping 에 이미 있는 URL 은 discovery 노이즈 — 제외
        if url[: -len(".md")].rstrip("/") in known:
            continue
        try:
            resp = httpx.get(url, follow_redirects=True, timeout=30.0)
        except httpx.HTTPError:
            continue
        if resp.status_code != 200:
            continue
        if not is_review_worthy(resp.text):
            continue
        # 카테고리 이름 = url 의 마지막 path segment (.md 제거)
        m = re.search(r"/([^/]+)\.md$", url)
        if not m:
            continue
        discovered.append({"name": m.group(1), "url": url.replace(".md", "")})

    args.out.write_text(json.dumps({"discovered_categories": discovered}, indent=2))


if __name__ == "__main__":
    main()
