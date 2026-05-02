from datetime import datetime, timezone

from scripts.plan import build_plan, PlanRecord, ItemStatus


def _item(id_):
    return {
        "id": id_,
        "type": "programmatic",
        "proposition": "p",
        "verifier": {"kind": "regex", "pattern": "."},
        "source": {
            "url": "https://example.com",
            "fetched_at": "2026-04-29T02:00:00Z",
            "quote": "q",
        },
        "severity": "important",
        "category": "skills",
    }


def test_plan_contains_remove_record():
    items = [_item("rem1")]
    statuses = {"rem1": ItemStatus.REMOVE_CANDIDATE}
    plan = build_plan(category="skills", existing_items=items, statuses=statuses, additions=[])
    assert any(r.action == "REMOVE" and r.item_id == "rem1" for r in plan)


def test_plan_contains_addition():
    new_item = _item("new1")
    plan = build_plan(category="skills", existing_items=[], statuses={}, additions=[new_item])
    assert any(r.action == "ADD" and r.item_id == "new1" for r in plan)


def test_plan_skips_stable():
    items = [_item("st1")]
    statuses = {"st1": ItemStatus.STABLE}
    plan = build_plan(category="skills", existing_items=items, statuses=statuses, additions=[])
    assert plan == []
