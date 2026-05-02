"""U3 Plan: build change records from diff statuses + new additions."""
from dataclasses import dataclass, asdict
from enum import Enum
from typing import Literal


class ItemStatus(str, Enum):
    """Classification status for items during diff phase."""
    STABLE = "stable"
    UPDATE_CANDIDATE = "update_candidate"
    REMOVE_CANDIDATE = "remove_candidate"


@dataclass
class PlanRecord:
    category: str
    action: Literal["ADD", "UPDATE", "REMOVE"]
    item_id: str
    payload: dict | None  # full new item for ADD/UPDATE, None for REMOVE

    def to_dict(self) -> dict:
        return asdict(self)


def build_plan(
    *,
    category: str,
    existing_items: list[dict],
    statuses: dict[str, ItemStatus],
    additions: list[dict],
) -> list[PlanRecord]:
    """
    Compose change records.

    - REMOVE_CANDIDATE → ADD a REMOVE record (fallback search runs separately before commit)
    - UPDATE_CANDIDATE → record requires a new payload; here we mark the id, payload-filling
      happens in the LLM-driven prompt step
    - STABLE → skip
    - additions → ADD records (already full payloads from LLM extraction)
    """
    records: list[PlanRecord] = []
    items_by_id = {it["id"]: it for it in existing_items}

    for item_id, status in statuses.items():
        if status == ItemStatus.STABLE:
            continue
        if status == ItemStatus.REMOVE_CANDIDATE:
            records.append(PlanRecord(category=category, action="REMOVE", item_id=item_id, payload=None))
        elif status == ItemStatus.UPDATE_CANDIDATE:
            # payload will be filled by LLM step; for now we carry the existing item
            records.append(
                PlanRecord(
                    category=category,
                    action="UPDATE",
                    item_id=item_id,
                    payload=items_by_id[item_id],
                )
            )

    for new_item in additions:
        records.append(
            PlanRecord(
                category=category,
                action="ADD",
                item_id=new_item["id"],
                payload=new_item,
            )
        )

    return records
