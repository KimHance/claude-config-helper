"""Assemble PR body from template + placeholders."""
from __future__ import annotations
import json
import re
import sys
from pathlib import Path


_BLOCK_RE = re.compile(r"\{\{IF\s+(\w+)\}\}(.*?)\{\{END\}\}", re.DOTALL)


def render(template: str, values: dict) -> str:
    def block_sub(m: re.Match) -> str:
        key, body = m.group(1), m.group(2)
        return body if values.get(key) else ""
    out = _BLOCK_RE.sub(block_sub, template)
    for k, v in values.items():
        out = out.replace(f"{{{{{k}}}}}", str(v))
    return out


def main() -> int:
    if len(sys.argv) != 4:
        print("Usage: assemble_pr_body.py <template> <values.json> <out.md>", file=sys.stderr)
        return 2
    tmpl = Path(sys.argv[1]).read_text()
    values = json.loads(Path(sys.argv[2]).read_text())
    Path(sys.argv[3]).write_text(render(tmpl, values))
    return 0


if __name__ == "__main__":
    sys.exit(main())
