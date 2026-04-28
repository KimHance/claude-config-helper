"""U2 Diff: classify existing items against fresh body."""
from enum import Enum
from typing import Iterable


class ItemStatus(str, Enum):
    STABLE = "stable"
    UPDATE_CANDIDATE = "update_candidate"
    REMOVE_CANDIDATE = "remove_candidate"


def _shingle(text: str, k: int = 5) -> set[str]:
    """Return set of k-gram word shingles for fuzzy match."""
    words = text.lower().split()
    return {" ".join(words[i : i + k]) for i in range(len(words) - k + 1)}


def _near_match(quote: str, body: str, threshold: float = 0.3) -> bool:
    """Return True if at least `threshold` of quote's shingles overlap body's shingles."""
    qs = _shingle(quote)
    if not qs:
        return False
    bs = _shingle(body)
    overlap = qs & bs
    return len(overlap) / len(qs) >= threshold


def classify_items(items: Iterable[dict], body: str) -> dict[str, ItemStatus]:
    """For each item, decide STABLE/UPDATE/REMOVE based on its quote vs body."""
    out: dict[str, ItemStatus] = {}
    for item in items:
        quote = item["source"]["quote"]
        if quote in body:
            out[item["id"]] = ItemStatus.STABLE
        elif _near_match(quote, body):
            out[item["id"]] = ItemStatus.UPDATE_CANDIDATE
        else:
            out[item["id"]] = ItemStatus.REMOVE_CANDIDATE
    return out
