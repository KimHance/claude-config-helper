"""Source integrity check (Plan Review U3.5 step 1)."""
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

import httpx


@dataclass
class SourceIntegrityResult:
    ok: bool
    reason: str
    url_status: int | None = None


WINDOW = timedelta(hours=1)


def check_source_integrity(
    item: dict,
    *,
    now: datetime,
    skip_http: bool = False,
) -> SourceIntegrityResult:
    src = item["source"]
    fetched_at = datetime.fromisoformat(src["fetched_at"].replace("Z", "+00:00"))

    if abs(now - fetched_at) > WINDOW:
        return SourceIntegrityResult(
            ok=False,
            reason=f"fetched_at {src['fetched_at']} outside ±1h window of {now.isoformat()}",
        )

    if skip_http:
        return SourceIntegrityResult(ok=True, reason="http skipped (test)")

    try:
        resp = httpx.get(src["url"], follow_redirects=True, timeout=30.0)
    except httpx.HTTPError as e:
        return SourceIntegrityResult(ok=False, reason=f"fetch error: {e}")

    if resp.status_code != 200:
        return SourceIntegrityResult(
            ok=False,
            reason=f"url {src['url']} returned {resp.status_code}",
            url_status=resp.status_code,
        )

    if src["quote"] not in resp.text:
        return SourceIntegrityResult(
            ok=False,
            reason=f"quote not found in body of {src['url']}",
            url_status=200,
        )

    return SourceIntegrityResult(ok=True, reason="url 200 + quote substring match", url_status=200)
