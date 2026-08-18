# Methodology

`rerun-to-green` answers one question with public data:

> When a CI run fails, and the exact same code (same workflow, same commit) is run
> again, how often does it go green without any code change?

## Data source

GitHub REST API, `List workflow runs for a repository`:

```
GET /repos/{owner}/{repo}/actions/runs?per_page=100
```

Public metadata only: `head_sha`, `conclusion`, `event`, `run_attempt`,
`created_at`, `run_started_at`, `updated_at`, `workflow_id`, `path`.

No source code, no logs, no PR text, no user data.

## Sample

32 curated open-source repositories that use GitHub Actions, across languages and
sizes. All public. A 90-day window was requested; repositories with more than 6,000
runs in that window were capped at the 6,000 most recent runs.

| Group | Repos |
|---|---|
| Python | apache/airflow, pandas-dev/pandas, numpy/numpy, home-assistant/core, ansible/ansible, encode/django-rest-framework, psf/requests |
| TypeScript/JS | microsoft/playwright, sveltejs/svelte, vercel/next.js, microsoft/TypeScript, angular/angular, pnpm/pnpm, vuejs/core, vitejs/vite, webpack/webpack, eslint/eslint, n8n-io/n8n, jquery/jquery |
| Rust | rust-lang/rust, denoland/deno |
| Go | golang/go, kubernetes/kubernetes, grafana/grafana, hashicorp/terraform, prometheus/prometheus, etcd-io/etcd |
| Java/Kotlin | spring-projects/spring-boot |
| C/C++ | godotengine/godot, grpc/grpc |
| Ruby | rails/rails |
| ML (Python/C++) | pytorch/pytorch |

## Definitions

**Run** — one workflow execution (a `workflow_runs` entry).

**Red** — conclusion `failure` or `timed_out`.

**Green** — conclusion `success`.

**Episode** — all executions of the same `(repository, workflow_id, head_sha)`.
Because the exact same commit can be run more than once (a rerun, a manual dispatch,
a scheduled re-run), the episode is the natural unit: it is one "attempt sequence"
for one code state.

**Same-commit re-run** — an episode with more than one execution
(`n_entries > 1` or `run_attempt > 1`).

**Recovered (entry-level)** — an episode that had at least one red execution and whose
final execution is green.

## Why two recovery numbers?

GitHub records re-runs in two ways, so we report two numbers:

1. **Entry-level (same-commit recovery):** a red run entry followed by a later green
   run entry with the same `head_sha`. This catches every same-commit recovery —
   including scheduled/workflow re-runs that are not "pressing rerun".
2. **Attempt-level (press-rerun):** runs where `run_attempt ≥ 2`. The GitHub API
   collapses attempts into one entry, so we validate with a random sample:
   for each sampled run we fetch attempt #1 (`GET .../attempts/1`) to confirm it
   genuinely failed, then check the final conclusion.

## Time-to-green

For recovered episodes: minutes from the first red execution's start to the first
green execution's completion. Reported as median and P90 over recovered episodes.

## Pipeline

```
src/fetch_runs.py          -> data/raw/*.json.gz   (raw run metadata)
src/analyze.py             -> data/processed/*     (episodes + summary)
src/validate_attempts.py   -> sample validation of attempt-based recovery
```

## Caveats

- Episodes that end red but were re-run on a *new* commit are not "same-commit
  re-runs" by definition — they were fixed with a code change.
- A green same-commit re-run does not prove the code is correct; it proves the
  failure was not caused by the commit itself in that run.
- The attempt-based number is conditional on a developer choosing to re-run, which
  is a selected sample (developers usually re-run runs they suspect are flaky).
