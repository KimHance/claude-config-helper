"""Fallback search for REMOVE candidates: sitemap + cross-language + changelog."""
import re
from dataclasses import dataclass
from typing import Literal

import httpx

CHANGELOG_URL = "https://code.claude.com/docs/en/changelog"
SITEMAP_URL = "https://code.claude.com/docs/llms.txt"


@dataclass
class FallbackResult:
    action: Literal["UPDATE_URL", "DELETE"]
    new_url: str | None = None
    changelog_note: str | None = None


def _swap_locale(url: str) -> str | None:
    """If url contains /en/ → /ko/, /ko/ → /en/."""
    if "/en/" in url:
        return url.replace("/en/", "/ko/")
    if "/ko/" in url:
        return url.replace("/ko/", "/en/")
    return None


def _quote_present(url: str, quote: str) -> bool:
    try:
        resp = httpx.get(url, follow_redirects=True, timeout=30.0)
        return resp.status_code == 200 and quote in resp.text
    except httpx.HTTPError:
        return False


def _search_changelog_for_quote(quote: str) -> str | None:
    """Return ±200-char window around quote in changelog if present, else None."""
    try:
        resp = httpx.get(CHANGELOG_URL, follow_redirects=True, timeout=30.0)
    except httpx.HTTPError:
        return None
    if resp.status_code != 200:
        return None
    body = resp.text
    # 단순 substring 매칭. 환각 방지.
    if quote not in body:
        # 단어 단위 fuzzy: quote 의 첫 3 단어로 매칭 시도
        keywords = quote.split()[:3]
        if not keywords:
            return None
        pattern = r"\s+".join(re.escape(w) for w in keywords)
        m = re.search(pattern, body, re.IGNORECASE)
        if not m:
            return None
        idx = m.start()
    else:
        idx = body.find(quote)
    return body[max(0, idx - 200) : idx + 200]


def resolve_remove_candidate(*, url: str, quote: str) -> FallbackResult:
    """Decide whether REMOVE candidate is truly gone or just moved."""
    # Step 1: cross-language probe
    other = _swap_locale(url)
    if other and _quote_present(other, quote):
        return FallbackResult(action="UPDATE_URL", new_url=other)

    # Step 2: sitemap fuzzy match (look for nearby slug)
    try:
        sitemap = httpx.get(SITEMAP_URL, follow_redirects=True, timeout=30.0).text
    except httpx.HTTPError:
        sitemap = ""
    # llms.txt 는 markdown link 형식. URL 만 추출 후 .md 제거해서 base URL 로 변환.
    from scripts.category_discovery import extract_md_urls

    candidates = [u[: -len(".md")] for u in extract_md_urls(sitemap)]
    # base slug (마지막 path segment) 가 같은 것들
    base = url.rstrip("/").rsplit("/", 1)[-1]
    for cand in candidates:
        if cand == url or cand.rstrip("/").rsplit("/", 1)[-1] != base:
            continue
        if _quote_present(cand, quote):
            return FallbackResult(action="UPDATE_URL", new_url=cand)

    # Step 3: changelog deprecation note
    note = _search_changelog_for_quote(quote)
    return FallbackResult(action="DELETE", changelog_note=note)
