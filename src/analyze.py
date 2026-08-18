#!/usr/bin/env python3
"""Analyze fetched workflow-run metadata into recovery episodes (attempt-aware).

Core question: when a CI run fails, and the SAME code (same workflow, same
head_sha) is executed again, how often does it go green without any code change?

GitHub records re-runs in two ways:
  1. a NEW list entry with the same (workflow_id, head_sha)  -> separate runs
  2. a new ATTEMPT on the same run_id (run_attempt > 1)      -> collapsed entry

We therefore treat each (workflow_id, head_sha) group as one "episode" and
consider a run "re-run" when the group has >1 entry OR an entry has
run_attempt > 1.

Outputs:
  data/processed/episodes.json.gz   per-episode rows
  data/processed/summary.json       headline numbers
  data/processed/episodes.csv       flat table
"""

import os
import json
import gzip
from datetime import datetime, timezone
import csv

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
RAW_DIR = os.path.join(ROOT, "data", "raw")
OUT_DIR = os.path.join(ROOT, "data", "processed")

RED = {"failure", "timed_out"}
GREEN = {"success"}


def iso_to_ts(s):
    if not s:
        return None
    try:
        return datetime.fromisoformat(s.replace("Z", "+00:00")).timestamp()
    except Exception:
        return None


def load_all():
    runs_by_repo = {}
    for fn in sorted(os.listdir(RAW_DIR)):
        if not fn.endswith(".json.gz"):
            continue
        with gzip.open(os.path.join(RAW_DIR, fn), "rt", encoding="utf-8") as fh:
            runs_by_repo[fn[:-8].replace("__", "/")] = json.load(fh)
    return runs_by_repo


def build_episodes(runs_by_repo):
    episodes = []
    for repo, runs in runs_by_repo.items():
        groups = {}
        for r in runs:
            key = (r.get("workflow_id"), r.get("head_sha"))
            groups.setdefault(key, []).append(r)
        for (wid, sha), rs in groups.items():
            rs.sort(key=lambda x: iso_to_ts(x.get("run_started_at")) or 0)
            n_entries = len(rs)
            rerun_via_entry = n_entries > 1
            rerun_via_attempt = any((r.get("run_attempt") or 1) > 1 for r in rs)
            was_rerun = rerun_via_entry or rerun_via_attempt

            finals = [r.get("conclusion") for r in rs]
            has_red = any(c in RED for c in finals)
            has_green = any(c in GREEN for c in finals)
            last_conclusion = finals[-1]

            green_after_red = has_red and has_green and last_conclusion in GREEN

            # time to green: from first red to first green
            first_red_ts = None
            first_green_after_red_ts = None
            for r in rs:
                t = iso_to_ts(r.get("run_started_at")) or iso_to_ts(r.get("created_at"))
                if r.get("conclusion") in RED and first_red_ts is None:
                    first_red_ts = t
                if r.get("conclusion") in GREEN and first_red_ts is not None and first_green_after_red_ts is None:
                    first_green_after_red_ts = iso_to_ts(r.get("updated_at")) or t
            time_to_green_min = None
            if first_red_ts is not None and first_green_after_red_ts is not None:
                time_to_green_min = round((first_green_after_red_ts - first_red_ts) / 60.0, 1)

            episodes.append({
                "repo": repo,
                "workflow_id": wid,
                "sha": sha,
                "n_entries": n_entries,
                "max_run_attempt": max((r.get("run_attempt") or 1) for r in rs),
                "was_rerun": was_rerun,
                "has_red": has_red,
                "has_green": has_green,
                "last_conclusion": last_conclusion,
                "green_after_red": green_after_red,
                "time_to_green_min": time_to_green_min,
                "events": sorted(set(r.get("event") for r in rs)),
                "started": rs[0].get("run_started_at"),
            })
    return episodes


def summarize(episodes):
    # Universe: episodes that had at least one red run, then were re-run on the
    # same commit (same workflow + same head_sha).
    red_eps = [e for e in episodes if e["has_red"]]
    rerun_red_eps = [e for e in red_eps if e["was_rerun"]]
    recovered = [e for e in rerun_red_eps if e["green_after_red"]]
    n_recovered = len(recovered)

    tts = sorted(e["time_to_green_min"] for e in recovered if e["time_to_green_min"] is not None)

    return {
        "repos": len({e["repo"] for e in episodes}),
        "episodes_total": len(episodes),
        "episodes_started_red": len(red_eps),
        "episodes_rerun_on_same_sha": len(rerun_red_eps),
        "rerun_to_green_count": n_recovered,
        "rerun_to_green_rate_pct": round(n_recovered / len(rerun_red_eps) * 100, 1) if rerun_red_eps else None,
        "median_time_to_green_min": tts[len(tts) // 2] if tts else None,
        "p90_time_to_green_min": tts[min(len(tts) - 1, int(len(tts) * 0.9))] if tts else None,
        "note": "Entry-level same-commit recovery. The press-rerun (attempt-level) number is "
                "produced by src/validate_attempts.py -> data/processed/attempt_validation.json.",
        "fetched_at": datetime.now(timezone.utc).isoformat(),
        "generated_by": "src/analyze.py",
    }


def main():
    os.makedirs(OUT_DIR, exist_ok=True)
    runs_by_repo = load_all()
    episodes = build_episodes(runs_by_repo)
    summary = summarize(episodes)

    with gzip.open(os.path.join(OUT_DIR, "episodes.json.gz"), "wt", encoding="utf-8") as fh:
        json.dump(episodes, fh)
    with open(os.path.join(OUT_DIR, "summary.json"), "w", encoding="utf-8") as fh:
        json.dump(summary, fh, indent=2, ensure_ascii=False)

    fields = ["repo", "workflow_id", "sha", "n_entries", "max_run_attempt",
              "was_rerun", "has_red", "has_green", "last_conclusion",
              "green_after_red", "time_to_green_min", "events", "started"]
    with open(os.path.join(OUT_DIR, "episodes.csv"), "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=fields)
        w.writeheader()
        for e in episodes:
            w.writerow({k: e.get(k) for k in fields})

    print(json.dumps(summary, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
