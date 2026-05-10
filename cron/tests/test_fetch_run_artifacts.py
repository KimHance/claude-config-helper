from scripts.fetch_run_artifacts import parse_artifact_list


def test_parse_artifact_list_picks_zip_urls():
    api_response = {
        "artifacts": [
            {"name": "baseline-sync-results-123", "archive_download_url": "https://api.github.com/.../zip"},
            {"name": "other", "archive_download_url": "https://api.github.com/.../zip-other"},
        ]
    }
    picked = parse_artifact_list(api_response, name_prefix="baseline-sync-results")
    assert len(picked) == 1
    assert picked[0]["name"] == "baseline-sync-results-123"


def test_get_token_env_override(monkeypatch):
    from scripts.fetch_run_artifacts import get_token
    monkeypatch.setenv("CRON_TOKEN_OVERRIDE", "ghp_fake")
    assert get_token() == "ghp_fake"
