"""Aggregator: group-result*.json flatten → dedup → cchelp 카테고리 binding."""
import fnmatch
from collections import OrderedDict


def flatten_group_results(group_results: list[dict]) -> list[dict]:
    """모든 group result 의 records 를 [{tab, group, record}] flat list 로 변환."""
    out: list[dict] = []
    for gr in group_results:
        if gr.get("status") == "failed":
            continue
        for rec in gr.get("records", []):
            out.append({"tab": gr["tab"], "group": gr["group"], "record": rec})
    return out


def _tab_priority(tab: str, priority_tabs: list[str]) -> int:
    try:
        return priority_tabs.index(tab)
    except ValueError:
        return len(priority_tabs)


def dedup_records(flat: list[dict], *, priority_tabs: list[str]) -> list[dict]:
    """
    같은 id 충돌 시 priority winner 선정 + 비-winner source → additional_sources[].

    Returns: list[record_with_meta] — record 자체 dict, _tab/_group 첨부.
    """
    by_id: OrderedDict[str, list[dict]] = OrderedDict()
    for entry in flat:
        rid = entry["record"]["id"]
        by_id.setdefault(rid, []).append(entry)

    deduped: list[dict] = []
    for rid, entries in by_id.items():
        if len(entries) == 1:
            e = entries[0]
            r = dict(e["record"])
            r["_tab"] = e["tab"]
            r["_group"] = e["group"]
            deduped.append(r)
            continue

        # priority 정렬 — 가장 우선 (lowest index) 가 winner
        entries_sorted = sorted(entries, key=lambda e: _tab_priority(e["tab"], priority_tabs))
        winner = entries_sorted[0]
        losers = entries_sorted[1:]

        winner_record = dict(winner["record"])
        winner_record["_tab"] = winner["tab"]
        winner_record["_group"] = winner["group"]
        winner_record["additional_sources"] = [
            {
                "url": l["record"]["source"]["url"],
                "fetched_at": l["record"]["source"]["fetched_at"],
                "quote": l["record"]["source"]["quote"],
            }
            for l in losers
        ]
        deduped.append(winner_record)

    return deduped


def page_matches_filter(page: str, page_filter: str | None) -> bool:
    """page slug 가 page_filter (glob) 매칭하는지. None 이면 모두 매치."""
    if page_filter is None:
        return True
    # page 는 'en/<slug>' 형식; 마지막 segment 만 비교
    last = page.rsplit("/", 1)[-1]
    return fnmatch.fnmatch(last, page_filter)


def _bind_record(record: dict, binding: dict) -> str | None:
    """record 의 (tab, group, page) 가 어느 cchelp 카테고리에 매칭하는지."""
    tab = record.get("_tab", "")
    group = record.get("_group", "")
    page = record.get("page", "")
    for cat in binding.get("categories", []):
        for rule in cat["bind"]:
            if rule["tab"] != tab:
                continue
            if rule["group"] != group:
                continue
            if not page_matches_filter(page, rule.get("page_filter")):
                continue
            return cat["name"]
    return None


def bind_to_categories(deduped: list[dict], binding: dict) -> list[dict]:
    """
    record list 를 binding rules 와 매칭 → category 결정.

    매칭 안 되면 record.category_hint 가 cchelp 카테고리 list 에 있는지 확인,
    있으면 그 카테고리 사용. 그래도 없으면 'discovered:<page-slug>'.
    """
    known_categories = {c["name"] for c in binding.get("categories", [])}
    out: list[dict] = []
    for rec in deduped:
        cat = _bind_record(rec, binding)
        if cat is None:
            hint = rec.get("category_hint", "")
            if hint in known_categories:
                cat = hint
            else:
                page = rec.get("page", "unknown").replace("/", "-")
                cat = f"discovered:{page}"
        # 정리: 내부 meta (_tab/_group) 제거하고 category 박기
        clean = {k: v for k, v in rec.items() if not k.startswith("_") and k != "category_hint"}
        clean["category"] = cat
        out.append(clean)
    return out


def build_plan_records(bound: list[dict]) -> list[dict]:
    """bound records → plan.json 형식 (action ADD record list)."""
    return [
        {
            "category": r["category"],
            "action": "ADD",
            "item_id": r["id"],
            "payload": {k: v for k, v in r.items() if k != "category"} | {"category": r["category"]},
        }
        for r in bound
    ]
