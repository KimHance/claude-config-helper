"""Fetch GitHub Actions artifacts for a given run id (no gh CLI)."""
from __future__ import annotations
import json
import os
import subprocess
import sys
import urllib.error
import urllib.request
import zipfile
from pathlib import Path


class _NoAuthRedirectHandler(urllib.request.HTTPRedirectHandler):
    """Follow redirects but strip Authorization on cross-origin hops (e.g. GitHub → Azure Blob)."""

    def redirect_request(self, req, fp, code, msg, headers, newurl):
        new_req = super().redirect_request(req, fp, code, msg, headers, newurl)
        if new_req is not None:
            new_req.headers.pop("Authorization", None)
            new_req.unredirected_hdrs.pop("Authorization", None)
        return new_req


def parse_artifact_list(api_response: dict, name_prefix: str) -> list[dict]:
    return [a for a in api_response.get("artifacts", []) if a["name"].startswith(name_prefix)]


def get_token() -> str:
    env = os.environ.get("CRON_TOKEN_OVERRIDE")
    if env:
        return env
    out = subprocess.check_output(
        ["git", "credential-osxkeychain", "get"],
        input=b"url=https://github.com\n\n",
    ).decode()
    for line in out.splitlines():
        if line.startswith("password="):
            return line[len("password="):]
    raise RuntimeError("No token in osxkeychain")


def fetch_artifacts(owner: str, repo: str, run_id: str, out_dir: Path, name_prefix: str = "") -> list[Path]:
    token = get_token()
    url = f"https://api.github.com/repos/{owner}/{repo}/actions/runs/{run_id}/artifacts"
    req = urllib.request.Request(url, headers={
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json",
    })
    with urllib.request.urlopen(req) as r:
        data = json.loads(r.read())
    out_dir.mkdir(parents=True, exist_ok=True)
    opener = urllib.request.build_opener(_NoAuthRedirectHandler)
    extracted: list[Path] = []
    for art in parse_artifact_list(data, name_prefix):
        zip_path = out_dir / f"{art['name']}.zip"
        z_req = urllib.request.Request(art["archive_download_url"],
                                        headers={"Authorization": f"Bearer {token}"})
        with opener.open(z_req) as r:
            zip_path.write_bytes(r.read())
        with zipfile.ZipFile(zip_path) as zf:
            zf.extractall(out_dir / art["name"])
        extracted.append(out_dir / art["name"])
    return extracted


def main() -> int:
    if len(sys.argv) < 4:
        print("Usage: fetch_run_artifacts.py <owner/repo> <run_id> <out_dir> [name_prefix]", file=sys.stderr)
        return 2
    owner, repo = sys.argv[1].split("/", 1)
    run_id = sys.argv[2]
    out_dir = Path(sys.argv[3])
    prefix = sys.argv[4] if len(sys.argv) >= 5 else ""
    paths = fetch_artifacts(owner, repo, run_id, out_dir, prefix)
    print(json.dumps({"extracted": [str(p) for p in paths]}, indent=2))
    return 0 if paths else 1


if __name__ == "__main__":
    sys.exit(main())
