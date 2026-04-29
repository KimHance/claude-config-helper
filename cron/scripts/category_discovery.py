"""Category auto-discovery via sitemap diff + frontmatter/schema heuristic."""
import re
from dataclasses import dataclass


@dataclass
class SitemapDiff:
    added: list[str]
    removed: list[str]


# llms.txt 의 형식은 markdown link list (`- [Title](URL): desc`).
# 또한 일부 테스트 / 옛 형식은 plain newline-separated URL 목록.
# 둘 다 대응하기 위해 정규식으로 .md URL 만 추출.
URL_RE = re.compile(r"https?://[^\s)<>]+\.md")


def extract_md_urls(text: str) -> set[str]:
    """Extract all `.md` URLs from sitemap text (handles both markdown-link and plain formats)."""
    return set(URL_RE.findall(text))


def diff_sitemap(old: str, new: str) -> SitemapDiff:
    old_urls = extract_md_urls(old)
    new_urls = extract_md_urls(new)
    return SitemapDiff(
        added=sorted(new_urls - old_urls),
        removed=sorted(old_urls - new_urls),
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
