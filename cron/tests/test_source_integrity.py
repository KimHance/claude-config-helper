from datetime import datetime, timezone
from unittest.mock import patch

import httpx
import pytest

from verifiers.source_integrity import (
    SourceIntegrityResult,
    check_source_integrity,
)


def _item(quote="hello world", fetched_at=None):
    return {
        "source": {
            "url": "https://example.com/docs",
            "fetched_at": fetched_at or datetime.now(timezone.utc).isoformat(),
            "quote": quote,
        }
    }


def test_quote_substring_match_pass(httpx_mock):
    httpx_mock.add_response(url="https://example.com/docs", text="lorem hello world ipsum")
    result = check_source_integrity(_item(), now=datetime.now(timezone.utc))
    assert result.ok
    assert result.url_status == 200


def test_quote_not_found_fails(httpx_mock):
    httpx_mock.add_response(url="https://example.com/docs", text="completely different content")
    result = check_source_integrity(_item(), now=datetime.now(timezone.utc))
    assert not result.ok
    assert "quote not found" in result.reason


def test_url_404_fails(httpx_mock):
    httpx_mock.add_response(url="https://example.com/docs", status_code=404)
    result = check_source_integrity(_item(), now=datetime.now(timezone.utc))
    assert not result.ok
    assert "404" in result.reason


def test_fetched_at_too_old_fails():
    old = "2020-01-01T00:00:00+00:00"
    item = _item(fetched_at=old)
    result = check_source_integrity(item, now=datetime.now(timezone.utc), skip_http=True)
    assert not result.ok
    assert "fetched_at" in result.reason


def test_fetched_at_within_window_passes(httpx_mock):
    httpx_mock.add_response(url="https://example.com/docs", text="hello world")
    result = check_source_integrity(_item(), now=datetime.now(timezone.utc))
    assert result.ok
