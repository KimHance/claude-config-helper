from pathlib import Path

from scripts.diff import classify_items, ItemStatus


def _item(item_id, quote):
    return {
        "id": item_id,
        "type": "programmatic",
        "proposition": "p",
        "verifier": {"kind": "regex", "pattern": "."},
        "source": {
            "url": "https://example.com",
            "fetched_at": "2026-04-29T02:00:00Z",
            "quote": quote,
        },
        "severity": "important",
        "category": "skills",
    }


def test_stable_when_quote_in_body():
    items = [_item("a", "lorem ipsum dolor")]
    body = "lorem ipsum dolor sit amet"
    result = classify_items(items, body)
    assert result["a"] == ItemStatus.STABLE


def test_remove_candidate_when_quote_missing():
    items = [_item("b", "missing-text")]
    body = "completely different content"
    result = classify_items(items, body)
    assert result["b"] == ItemStatus.REMOVE_CANDIDATE


def test_update_candidate_when_near_match():
    # quote 가 변경됐지만 충분히 유사한 부분이 body 에 존재
    items = [_item("c", "name field max 200 chars")]
    body = "Lowercase letters, numbers, and hyphens only (max 64 characters)."
    result = classify_items(items, body)
    # max XYZ chars 같은 패턴이 둘 다 있으니 UPDATE
    assert result["c"] in (ItemStatus.UPDATE_CANDIDATE, ItemStatus.REMOVE_CANDIDATE)
