import pytest

from scripts.fallback_search import FallbackResult, resolve_remove_candidate


@pytest.mark.httpx_mock(assert_all_responses_were_requested=False)
def test_found_in_other_language(httpx_mock):
    """Original /en/ 404, /ko/ 200 with quote → UPDATE."""
    httpx_mock.add_response(
        url="https://code.claude.com/docs/en/skills", status_code=404
    )
    httpx_mock.add_response(
        url="https://code.claude.com/docs/ko/skills",
        text="설명: Lowercase letters and numbers only",
    )
    httpx_mock.add_response(
        url="https://code.claude.com/docs/llms.txt",
        text="https://code.claude.com/docs/en/skills.md\nhttps://code.claude.com/docs/ko/skills.md",
    )
    result = resolve_remove_candidate(
        url="https://code.claude.com/docs/en/skills",
        quote="Lowercase letters and numbers only",
    )
    assert result.action == "UPDATE_URL"
    assert "ko/skills" in result.new_url


@pytest.mark.httpx_mock(assert_all_responses_were_requested=False)
def test_404_and_no_match_returns_delete(httpx_mock):
    httpx_mock.add_response(url="https://code.claude.com/docs/en/skills", status_code=404)
    httpx_mock.add_response(url="https://code.claude.com/docs/ko/skills", status_code=404)
    httpx_mock.add_response(
        url="https://code.claude.com/docs/llms.txt",
        text="https://code.claude.com/docs/en/skills.md",
    )
    httpx_mock.add_response(
        url="https://code.claude.com/docs/en/changelog", text="no deprecation here"
    )
    result = resolve_remove_candidate(
        url="https://code.claude.com/docs/en/skills",
        quote="Lowercase letters and numbers only",
    )
    assert result.action == "DELETE"


@pytest.mark.httpx_mock(assert_all_responses_were_requested=False)
def test_changelog_deprecation_returns_delete_with_note(httpx_mock):
    httpx_mock.add_response(url="https://code.claude.com/docs/en/skills", status_code=404)
    httpx_mock.add_response(url="https://code.claude.com/docs/ko/skills", status_code=404)
    httpx_mock.add_response(
        url="https://code.claude.com/docs/llms.txt",
        text="https://code.claude.com/docs/en/skills.md",
    )
    httpx_mock.add_response(
        url="https://code.claude.com/docs/en/changelog",
        text="v2.1.200: Removed legacy 'name' field from frontmatter (deprecated).",
    )
    result = resolve_remove_candidate(
        url="https://code.claude.com/docs/en/skills",
        quote="legacy 'name' field",
    )
    assert result.action == "DELETE"
    assert result.changelog_note is not None
