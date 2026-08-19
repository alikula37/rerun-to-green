#!/usr/bin/env python3
"""Validate attempt-based rerun recovery on a random sample (concurrent).

For runs with run_attempt >= 2 (GitHub recorded an explicit re-run), fetch
attempt #1 to learn its conclusion, then measure:
  * what fraction of genuinely failed first attempts end green,
  * how much of "rerun" activity is actually approval-gated (action_required).
Uses a small thread pool to absorb slow/transient DNS failures.
"""
import gzip, json, glob, os, random, sys, urllib.request
from collections import Counter
from concurrent.futures import ThreadPoolExecutor, as_completed

token = os.environ.get("GH_TOKEN", "").strip()

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
RAW_DIR = os.path.join(ROOT, "data", "raw")


def load_candidates():
    cands = []
    for p in glob.glob(os.path.join(RAW_DIR, "*.json.gz")):
        repo = os.path.basename(p)[:-8].replace("__", "/")
        with gzip.open(p, "rt") as fh:
            runs = json.load(fh)
        for r in runs:
            if (r.get("run_attempt") or 1) > 1:
                cands.append((repo, r["id"], r.get("conclusion")))
    return cands


def fetch_attempt1(repo, rid):
    url = f"https://api.github.com/repos/{repo}/actions/runs/{rid}/attempts/1"
    for attempt in range(4):
        try:
            req = urllib.request.Request(url)
            req.add_header("Accept", "application/vnd.github+json")
            req.add_header("Authorization", f"Bearer {token}")
            req.add_header("User-Agent", "rerun-to-green")
            with urllib.request.urlopen(req, timeout=20) as resp:
                d = json.loads(resp.read().decode())
            return (d.get("conclusion") or "none",)
        except Exception:
            if attempt == 3:
                return ("fetch_failed",)
    return ("fetch_failed",)


def main():
    if not token:
        print("SKIP: GH_TOKEN not set; attempt-level validation requires a GitHub token.")
        print("Add a GH_TOKEN secret to the repository to enable this step.")
        return
    cands = load_candidates()
    print(f"total runs with attempt>=2: {len(cands)}", flush=True)
    random.seed(42)
    random.shuffle(cands)
    sample = cands[:400]

    cross = Counter()
    n_fetch_failed = 0
    with ThreadPoolExecutor(max_workers=8) as ex:
        futs = {ex.submit(fetch_attempt1, repo, rid): (repo, rid, final)
                for repo, rid, final in sample}
        for i, fut in enumerate(as_completed(futs), 1):
            repo, rid, final = futs[fut]
            (a1,) = fut.result()
            cross[(a1, final or "none")] += 1
            if a1 == "fetch_failed":
                n_fetch_failed += 1
            if i % 100 == 0:
                print(f"processed {i}...", flush=True)

    print(f"\nprocessed: {len(sample)} (fetch_failed: {n_fetch_failed})")
    for k in sorted(cross, key=lambda x: (str(x[0]), str(x[1]))):
        print("  ", k, cross[k])
    f_fail = sum(v for (a, f), v in cross.items() if a == "failure")
    f_fail_green = sum(v for (a, f), v in cross.items() if a == "failure" and f == "success")
    ar = sum(v for (a, f), v in cross.items() if a == "action_required")
    ar_green = sum(v for (a, f), v in cross.items() if a == "action_required" and f == "success")
    print(f"\nfailure-first attempts: {f_fail}, final green: {f_fail_green} "
          f"= {f_fail_green / f_fail * 100 if f_fail else 0:.1f}%")
    print(f"action_required-first attempts: {ar}, final green: {ar_green} "
          f"= {ar_green / ar * 100 if ar else 0:.1f}%")

    result = {
        "sampled_rerun_runs": len(sample),
        "fetch_failed": n_fetch_failed,
        "failure_first": f_fail,
        "failure_first_final_green": f_fail_green,
        "failure_first_green_rate_pct": round(f_fail_green / f_fail * 100, 1) if f_fail else None,
        "action_required_first": ar,
        "action_required_first_final_green": ar_green,
        "note": "Attempt-level 'press rerun' recovery: among runs GitHub recorded as "
                "re-run at least once (run_attempt>=2) whose first attempt genuinely "
                "failed, what fraction finished green.",
        "generated_by": "src/validate_attempts.py",
    }
    out = os.path.join(ROOT, "data", "processed", "attempt_validation.json")
    with open(out, "w", encoding="utf-8") as fh:
        json.dump(result, fh, indent=2, ensure_ascii=False)
    print(f"\nwrote {out}")


if __name__ == "__main__":
    main()
