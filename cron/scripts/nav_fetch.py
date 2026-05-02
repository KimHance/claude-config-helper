"""Mintlify hydrate parse + docsConfig 추출 + page .md 병렬 fetch."""
import json
import re
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from pathlib import Path

import httpx

DOCS_BASE = "https://code.claude.com/docs"
ENTRY_URL = f"{DOCS_BASE}/en/skills"  # hydrate chunk 가 들어있는 임의 page


class NavExtractError(Exception):
    """Mintlify hydrate 형식 변경 또는 추출 실패."""


def _decode_chunk(chunk: str) -> str:
    """Next.js push payload 의 escape 시퀀스 디코딩."""
    return chunk.encode().decode("unicode_escape")


def _extract_balanced_object(text: str, key_marker: str) -> str | None:
    """JSON 안의 특정 key 다음 balanced { ... } 객체 substring 반환."""
    idx = text.find(key_marker)
    if idx == -1:
        return None
    j = idx + len(key_marker)
    while j < len(text) and text[j] in " \n\t":
        j += 1
    if j >= len(text) or text[j] != "{":
        return None
    depth = 0
    start = j
    while j < len(text):
        c = text[j]
        if c == "{":
            depth += 1
        elif c == "}":
            depth -= 1
            if depth == 0:
                return text[start : j + 1]
        j += 1
    return None


def extract_docs_config(html: str) -> dict:
    """Streaming SSR chunks 에서 docsConfig.navigation 객체 추출."""
    chunks = re.findall(r'self\.__next_f\.push\(\[1,"(.*?)"\]\)', html, re.DOTALL)
    target = next((c for c in chunks if "docsConfig" in c), None)
    if target is None:
        raise NavExtractError("docsConfig chunk not found in hydrate stream")
    try:
        decoded = _decode_chunk(target)
    except UnicodeDecodeError as e:
        raise NavExtractError(f"chunk decode error: {e}")
    nav_str = _extract_balanced_object(decoded, '"navigation":')
    if nav_str is None:
        raise NavExtractError("navigation object not found in docsConfig")
    try:
        return json.loads(nav_str)
    except json.JSONDecodeError as e:
        raise NavExtractError(f"navigation JSON parse error: {e}")


def extract_pages_to_fetch(nav: dict, *, excluded_tabs: list[str], language: str = "en") -> dict:
    """nav 에서 excluded_tabs 제외 후 fetch 대상 구조 반환."""
    lang_entry = next((l for l in nav["languages"] if l["language"] == language), None)
    if lang_entry is None:
        raise NavExtractError(f"language '{language}' not found")
    excluded = set(excluded_tabs)
    out_tabs = []
    for tab in lang_entry["tabs"]:
        if tab["tab"] in excluded:
            continue
        out_tabs.append(tab)
    return {"language": language, "tabs": out_tabs, "excluded_tabs": list(excluded)}


def slug_safe(name: str) -> str:
    """group 이름을 파일명/artifact 안전한 slug 로 변환."""
    s = re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")
    return s or "unnamed"


def fetch_page_md(page_slug: str, out_dir: Path) -> Path:
    """page slug (예: en/skills) → .md fetch + 저장."""
    out_dir.mkdir(parents=True, exist_ok=True)
    url = f"{DOCS_BASE}/{page_slug}.md"
    resp = httpx.get(url, follow_redirects=True, timeout=60.0)
    resp.raise_for_status()
    fname = page_slug.replace("/", "__") + ".md"
    out = out_dir / fname
    out.write_text(resp.text, encoding="utf-8")
    return out


def fetch_all_pages(structure: dict, out_dir: Path, *, max_workers: int = 10) -> list[Path]:
    """structure 의 모든 page 병렬 fetch."""
    pages = [
        p
        for tab in structure["tabs"]
        for grp in tab["groups"]
        for p in _flatten_pages(grp.get("pages", []))
    ]
    paths: list[Path] = []
    with ThreadPoolExecutor(max_workers=max_workers) as ex:
        futures = {ex.submit(fetch_page_md, p, out_dir): p for p in pages}
        for fut in as_completed(futures):
            paths.append(fut.result())
    return paths


def _flatten_pages(pages: list) -> list[str]:
    """sub-group 의 nested pages 까지 flatten."""
    out: list[str] = []
    for p in pages:
        if isinstance(p, str):
            out.append(p)
        elif isinstance(p, dict) and "pages" in p:
            out.extend(_flatten_pages(p["pages"]))
    return out


def fetch_entry_html(*, url: str = ENTRY_URL) -> str:
    """hydrate chunk 가 박힌 entry page HTML fetch."""
    resp = httpx.get(url, follow_redirects=True, timeout=60.0)
    resp.raise_for_status()
    return resp.text


def write_nav_json(structure: dict, out_path: Path, *, source: str = ENTRY_URL) -> None:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "fetched_at": datetime.now(timezone.utc).isoformat(),
        "source": source,
        **structure,
    }
    out_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False))
