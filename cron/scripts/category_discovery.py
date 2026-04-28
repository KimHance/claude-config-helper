"""Category auto-discovery via sitemap diff + frontmatter/schema heuristic."""
import re
from dataclasses import dataclass


@dataclass
class SitemapDiff:
    added: list[str]
    removed: list[str]


def diff_sitemap(old: str, new: str) -> SitemapDiff:
    old_set = {line.strip() for line in old.splitlines() if line.strip()}
    new_set = {line.strip() for line in new.splitlines() if line.strip()}
    return SitemapDiff(
        added=sorted(new_set - old_set),
        removed=sorted(old_set - new_set),
    )


# 휴리스틱: review-worthy = frontmatter table 또는 schema 존재
FRONTMATTER_TABLE_RE = re.compile(
    r"##\s*Frontmatter\s+reference|"
    r"\|\s*Field\s*\|\s*Required",
    re.IGNORECASE,
)
SCHEMA_BLOCK_RE = re.compile(r"```(?:json|yaml|jsonc)\s*\n.*?```", re.DOTALL)
GUIDE_BLACKLIST_RE = re.compile(
    r"^#\s*(quickstart|getting started|overview|troubleshooting|tutorial)",
    re.IGNORECASE | re.MULTILINE,
)


def is_review_worthy(body: str) -> bool:
    if FRONTMATTER_TABLE_RE.search(body):
        return True
    if SCHEMA_BLOCK_RE.search(body) and not GUIDE_BLACKLIST_RE.search(body):
        return True
    return False


@dataclass
class CategoryCandidate:
    name: str
    url: str
    body: str
