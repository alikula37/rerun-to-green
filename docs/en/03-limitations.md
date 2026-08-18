# Limitations

Everything in this repo is measured from public GitHub Actions metadata. That
gives us a real, reproducible number — but it has hard limits. Read these before
quoting the headline.

## What we cannot say

**Green after rerun ≠ the code is correct.**
It means the failure was not caused by the commit in that particular run. It can
still be a real bug that only shows up under certain conditions.

**This is not an AI-effect study.**
We do not know which runs were written by an AI tool, and we do not attribute
failures (or recoveries) to AI. The recovery loop costs time whoever wrote the code.

**No causality.**
We measured what happens, not why. Reruns that turn green usually mean flaky tests,
network or environment issues — but we only see run metadata, not log content, so we
cannot confirm the root cause from this dataset.

## Measurement limits

**Selection bias (attempt-level ~75%).**
Developers re-run runs they *suspect* are flaky. The ~75% is conditional on a
developer choosing to rerun — it is not the probability that a random red run
recovers.

**Attempt collapse.**
The GitHub API returns one entry per run with its current `run_attempt`. Intermediate
attempt conclusions are invisible in bulk; we validate attempt #1 on a random sample
instead of exhaustively.

**Window and cap.**
Data covers up to 90 days (2026). Repositories with more than 6,000 runs in that
window were capped at the 6,000 most recent runs, so for very busy repos the window
is shorter. Results are a snapshot, not a trend.

**Repository selection.**
We curated 32 active OSS repos that use GitHub Actions. They are not a random sample
of all repositories, and per-repo results vary widely (0–77% recovery).

**Episode boundary.**
We treat same-`(workflow, SHA)` runs as one episode. A same-SHA run that appears
much later (e.g., a workflow re-dispatch days later) is still counted, which is why
P90 time-to-green is long.

## The honest framing

> "Of the runs GitHub recorded as re-runs on a failed first attempt, ~75% finished
> green — same commit, no code change." — measured, sample-validated, snapshot of
> 2026 public CI. It does not say your rerun will work, or that the code is correct.
