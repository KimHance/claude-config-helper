"""CLI entry: Job 1 — nav-fetch + page-fetch."""
import argparse
import sys
from pathlib import Path

import yaml

from scripts.nav_fetch import (
    NavExtractError,
    extract_docs_config,
    extract_pages_to_fetch,
    fetch_all_pages,
    fetch_entry_html,
    write_nav_json,
)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--mapping", required=True, type=Path)
    ap.add_argument("--out-nav", required=True, type=Path)
    ap.add_argument("--out-fetched", required=True, type=Path)
    args = ap.parse_args()

    mapping = yaml.safe_load(args.mapping.read_text()) or {}
    excluded_tabs = mapping.get("excluded_tabs", [])

    try:
        html = fetch_entry_html()
        nav = extract_docs_config(html)
    except NavExtractError as e:
        print(f"FATAL: nav extraction failed: {e}", file=sys.stderr)
        return 1
    except Exception as e:
        print(f"FATAL: entry html fetch failed: {e}", file=sys.stderr)
        return 1

    structure = extract_pages_to_fetch(nav, excluded_tabs=excluded_tabs)
    write_nav_json(structure, args.out_nav)

    paths = fetch_all_pages(structure, args.out_fetched)
    print(f"fetched {len(paths)} pages → {args.out_fetched}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
