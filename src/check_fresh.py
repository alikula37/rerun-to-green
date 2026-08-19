#!/usr/bin/env python3
"""Check that committed processed results match a fresh regeneration.

Regenerates episodes + summary in memory from the committed raw data
(data/raw/*.json.gz) and compares the metric fields against the committed
data/processed/summary.json. Exits 0 if they match, 1 otherwise.

Used by .github/workflows/analyze.yml so the published numbers always
correspond to the raw data in the repository.
"""
import os
import sys
import json

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "src"))

import analyze  # noqa: E402

FIELDS = [
    "repos", "episodes_total", "episodes_started_red",
    "episodes_rerun_on_same_sha", "rerun_to_green_count",
    "rerun_to_green_rate_pct", "median_time_to_green_min",
    "p90_time_to_green_min",
]


def main():
    committed_path = os.path.join(ROOT, "data", "processed", "summary.json")
    with open(committed_path, encoding="utf-8") as fh:
        committed = json.load(fh)

    runs = analyze.load_all()
    episodes = analyze.build_episodes(runs)
    fresh = analyze.summarize(episodes)

    diffs = []
    for f in FIELDS:
        if committed.get(f) != fresh.get(f):
            diffs.append((f, committed.get(f), fresh.get(f)))

    if diffs:
        print("FRESHNESS CHECK FAILED - committed data/processed does not match data/raw.")
        print("Run `python3 src/analyze.py` and commit the updated data/processed/*.")
        for f, c, fr in diffs:
            print(f"  {f}: committed={c} fresh={fr}")
        sys.exit(1)

    print(f"FRESHNESS CHECK PASSED - {fresh['episodes_total']} episodes, "
          f"same-commit rerun-to-green {fresh['rerun_to_green_rate_pct']}%.")


if __name__ == "__main__":
    main()
