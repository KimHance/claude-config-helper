"""Oracle JSON reports → baseline file patcher.

Reads JSON reports produced by the oracle-check step, splits each baseline
markdown file by ## headings, replaces only the sections marked
`changed: true`, and writes the file back. Sections marked `changed: false`
or absent from the report are left byte-for-byte unchanged.
"""
from __future__ import annotations

import re
from typing import Dict, Tuple


_H2_RE = re.compile(r"^## (.+?)\s*$", re.MULTILINE)


def split_by_h2(md: str) -> Tuple[str, Dict[str, str]]:
    """Split a markdown string at every level-2 heading.

    Returns (head, sections) where head is everything before the first ##
    and sections maps each heading text to its body (everything between
    that ## and the next ## or end-of-file).
    """
    matches = list(_H2_RE.finditer(md))
    if not matches:
        return md, {}
    head = md[: matches[0].start()]
    sections: Dict[str, str] = {}
    for i, m in enumerate(matches):
        name = m.group(1).strip()
        body_start = m.end()
        body_end = matches[i + 1].start() if i + 1 < len(matches) else len(md)
        body = md[body_start:body_end]
        body = body.lstrip("\n")
        sections[name] = body
    return head, sections


def merge_by_h2(head: str, sections: Dict[str, str], order: list[str]) -> str:
    """Reassemble a markdown string in the given section order.

    `order` is the canonical section name list (from criteria-mapping
    `section_names`). Sections not in `order` are appended at the end in
    insertion order.
    """
    head = head.rstrip() + "\n\n" if head.strip() else ""
    parts = [head]
    seen = set()
    for name in order:
        if name in sections:
            body = sections[name].rstrip() + "\n"
            parts.append(f"## {name}\n{body}\n")
            seen.add(name)
    for name, body in sections.items():
        if name not in seen:
            body = body.rstrip() + "\n"
            parts.append(f"## {name}\n{body}\n")
    out = "".join(parts).rstrip() + "\n"
    return out
