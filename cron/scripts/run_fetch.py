"""CLI entry: U1 fetch. Reads criteria-mapping.yml, fetches all categories + sitemap + changelog."""
import argparse
from pathlib import Path

import yaml

from scripts.fetch import fetch_category, fetch_changelog, fetch_sitemap


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--mapping", required=True, type=Path)
    ap.add_argument("--out-dir", required=True, type=Path)
    args = ap.parse_args()

    mapping = yaml.safe_load(args.mapping.read_text())
    for entry in mapping.get("mappings", []):
        name = entry["name"] if "name" in entry else entry["keywords"][0]
        url = entry["docs_url"]
        print(f"fetch {name} {url}")
        fetch_category(name, url, out_dir=args.out_dir)
    fetch_sitemap(out_dir=args.out_dir)
    fetch_changelog(out_dir=args.out_dir)


if __name__ == "__main__":
    main()
