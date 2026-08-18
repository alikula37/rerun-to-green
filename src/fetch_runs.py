#!/usr/bin/env python3
"""Fetch GitHub Actions workflow-run metadata for a list of public repos.

Only public workflow-run metadata is used:
  * id, head_sha, conclusion, status, event
  * run_attempt, run_started_at, created_at, updated_at
  * workflow_id / path
No source code, no logs, no user data is stored.

Usage:
  GH_TOKEN=<token> python3 src/fetch_runs.py
  (GH_TOKEN is optional; without it the GitHub API rate limit is 60 req/hr)
"""

import json
import os
import sys
import time
import urllib.request
import urllib.parse
import gzip
from datetime import datetime, timedelta, timezone

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
REPOS_FILE = os.path.join(HERE, "repos.txt")
RAW_DIR = os.path.join(ROOT, "data", "raw")
PER_PAGE = 100
API = "https://api.github.com"


def load_repos():
    repos = []
    with open(REPOS_FILE, "r", encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            repos.append(line)
    return repos


def api_get(url, token, retries=4):
    req = urllib.request.Request(url)
    req.add_header("Accept", "application/vnd.github+json")
    req.add_header("X-GitHub-Api-Version", "2022-11-28")
    req.add_header("User-Agent", "rerun-to-green")
    if token:
        req.add_header("Authorization", f"Bearer {token}")
    for attempt in range(retries):
        try:
            with urllib.request.urlopen(req, timeout=60) as resp:
                return json.loads(resp.read().decode("utf-8")), resp.headers
        except urllib.error.URLError as e:
            if attempt == retries - 1:
                raise
            print(f"  transient network error ({e}), retrying in {2 ** attempt}s", flush=True)
            time.sleep(2 ** attempt)
        except urllib.error.HTTPError as e:
            if e.code in (502, 503, 504) and attempt < retries - 1:
                time.sleep(2 ** attempt)
                continue
            raise


def fetch_repo_runs(repo, token, since, max_pages=60):
    """Fetch all completed workflow runs newer than `since` (datetime)."""
    all_runs = []
    params = {"per_page": PER_PAGE, "exclude_pull_requests": "false"}
    page = 1
    done = False
    while page <= max_pages:
        url = f"{API}/repos/{repo}/actions/runs?" + urllib.parse.urlencode(params)
        try:
            data, headers = api_get(url, token)
        except urllib.error.HTTPError as e:
            if e.code == 403 and "rate limit" in e.read().decode("utf-8", "ignore").lower():
                print(f"  rate-limited on {repo} at page {page}", flush=True)
                return all_runs, False
            if e.code == 404:
                print(f"  repo not found: {repo}", flush=True)
                return all_runs, True
            print(f"  http error {e.code} on {repo} page {page}", flush=True)
            time.sleep(2)
            continue

        runs = data.get("workflow_runs", [])
        if not runs:
            break

        # Stop when we pass the time window (runs are newest-first)
        for r in runs:
            created = r.get("created_at")
            if created:
                created_dt = datetime.fromisoformat(created.replace("Z", "+00:00"))
                if created_dt < since:
                    done = True
                    break
                all_runs.append(r)
        if done:
            break

        # Link header for pagination
        link = headers.get("Link", "")
        if f'rel="next"' not in link:
            break
        params["page"] = page + 1
        page += 1
    return all_runs, True


def main():
    token = os.environ.get("GH_TOKEN", "")
    days = int(os.environ.get("WINDOW_DAYS", "90"))
    since = datetime.now(timezone.utc) - timedelta(days=days)
    repos = load_repos()

    os.makedirs(RAW_DIR, exist_ok=True)
    manifest = {"window_days": days, "fetched_at": datetime.now(timezone.utc).isoformat(),
                "repos": [], "rate_limit_remaining": None}
    total = 0

    for repo in repos:
        safe = repo.replace("/", "__")
        out = os.path.join(RAW_DIR, f"{safe}.json.gz")
        if os.path.exists(out) and not os.environ.get("FORCE_REFETCH"):
            print(f"skip {repo} (already fetched)", flush=True)
            with gzip.open(out, "rt", encoding="utf-8") as fh:
                runs = json.load(fh)
            manifest["repos"].append({"repo": repo, "runs": len(runs)})
            total += len(runs)
            continue
        print(f"fetching {repo} ...", flush=True)
        runs, ok = fetch_repo_runs(repo, token, since)
        if not ok:
            print(f"  STOPPED: rate limit hit at {repo}. continue later with GH_TOKEN.", flush=True)
            break
        # keep only fields we need
        slim = [{
            "id": r.get("id"),
            "head_sha": r.get("head_sha"),
            "conclusion": r.get("conclusion"),
            "status": r.get("status"),
            "event": r.get("event"),
            "run_attempt": r.get("run_attempt"),
            "run_number": r.get("run_number"),
            "workflow_id": r.get("workflow_id"),
            "path": r.get("path"),
            "created_at": r.get("created_at"),
            "run_started_at": r.get("run_started_at"),
            "updated_at": r.get("updated_at"),
        } for r in runs]
        with gzip.open(out, "wt", encoding="utf-8") as fh:
            json.dump(slim, fh)
        manifest["repos"].append({"repo": repo, "runs": len(slim)})
        total += len(slim)
        print(f"  {len(slim)} runs", flush=True)
        time.sleep(0.5)  # be gentle

    print(f"\nTOTAL runs collected: {total}")
    with open(os.path.join(ROOT, "data", "manifest.json"), "w", encoding="utf-8") as fh:
        json.dump(manifest, fh, indent=2)


if __name__ == "__main__":
    main()
