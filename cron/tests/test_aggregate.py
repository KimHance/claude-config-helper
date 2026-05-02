from scripts.aggregate import (
    bind_to_categories,
    dedup_records,
    flatten_group_results,
    page_matches_filter,
)


def _record(id_, source_url, page, quote="some valid quote", category_hint="hooks"):
    return {
        "id": id_,
        "type": "qualitative",
        "proposition": "p" + id_,
        "verifier": {"kind": "llm-judge", "rubric": "rrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrr"},
        "source": {"url": source_url, "fetched_at": "2026-05-02T00:00:00Z", "quote": quote},
        "severity": "important",
        "category_hint": category_hint,
        "page": page,
    }


def test_flatten_collects_all_records():
    g1 = {
        "tab": "Build with Claude Code", "group": "Automation", "status": "ok",
        "records": [_record("a", "u1", "en/hooks-guide")],
        "empty_pages": [], "errors": [],
    }
    g2 = {
        "tab": "Reference", "group": "Reference", "status": "ok",
        "records": [_record("b", "u2", "en/hooks")],
        "empty_pages": [], "errors": [],
    }
    flat = flatten_group_results([g1, g2])
    assert len(flat) == 2
    assert {r["record"]["id"] for r in flat} == {"a", "b"}
    # tab/group meta 가 record 에 attach 됐는지
    a = next(r for r in flat if r["record"]["id"] == "a")
    assert a["tab"] == "Build with Claude Code"
    assert a["group"] == "Automation"


def test_dedup_priority_reference_wins():
    flat = [
        {"tab": "Build with Claude Code", "group": "Automation",
         "record": _record("hook-x", "https://docs/hooks-guide", "en/hooks-guide", quote="guide quote")},
        {"tab": "Reference", "group": "Reference",
         "record": _record("hook-x", "https://docs/hooks", "en/hooks", quote="reference quote")},
    ]
    priority_tabs = ["Reference", "Configuration", "Administration", "Build with Claude Code"]
    deduped = dedup_records(flat, priority_tabs=priority_tabs)
    assert len(deduped) == 1
    winner = deduped[0]
    assert winner["source"]["url"] == "https://docs/hooks"  # Reference 우선
    assert winner["additional_sources"][0]["url"] == "https://docs/hooks-guide"
    assert winner["additional_sources"][0]["quote"] == "guide quote"


def test_dedup_no_collision_passes_through():
    flat = [
        {"tab": "Reference", "group": "Reference",
         "record": _record("a", "u1", "en/x")},
        {"tab": "Reference", "group": "Reference",
         "record": _record("b", "u2", "en/y")},
    ]
    deduped = dedup_records(flat, priority_tabs=["Reference"])
    assert len(deduped) == 2
    assert all("additional_sources" not in r for r in deduped)


def test_page_matches_filter_glob():
    assert page_matches_filter("en/hooks-guide", "hooks*")
    assert page_matches_filter("en/hooks", "hooks*")
    assert not page_matches_filter("en/skills", "hooks*")
    assert page_matches_filter("en/skills", "skills")
    assert page_matches_filter("en/skills", None)  # filter 없으면 모두 매치


def test_bind_to_categories_with_rules():
    deduped = [
        {**_record("hook-x", "https://docs/hooks", "en/hooks", category_hint="hooks"),
         "_tab": "Reference", "_group": "Reference"},
        {**_record("skill-y", "https://docs/skills", "en/skills", category_hint="skills"),
         "_tab": "Build with Claude Code", "_group": "Tools and plugins"},
    ]
    binding = {
        "categories": [
            {"name": "hooks", "bind": [{"tab": "Reference", "group": "Reference", "page_filter": "hooks*"}], "review_file": "hooks.yml"},
            {"name": "skills", "bind": [{"tab": "Build with Claude Code", "group": "Tools and plugins", "page_filter": "skills"}], "review_file": "skills.yml"},
        ]
    }
    bound = bind_to_categories(deduped, binding)
    by_cat = {r["category"] for r in bound}
    assert by_cat == {"hooks", "skills"}
