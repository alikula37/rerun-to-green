# Results

Measured 2026-08-19 on 143,061 public GitHub Actions runs from 32 repositories
(up to 90 days of history; heavy repos capped at the 6,000 most recent runs).

## Headline

| Question | Answer |
|---|---|
| Failed runs re-run on the exact same commit | **~18%** (1,785 / 10,047) |
| Same-commit re-run episodes that turned green (entry-level) | **~28%** (498 / 1,785) |
| Press-rerun case (attempt-level, sampled) | **~75%** (63/83) |
| Median time-to-green (recovered episodes) | **3.8 min** |
| P90 time-to-green (recovered episodes) | **171 min (~2.9 h)** |

## What the two recovery rates are

- **Entry-level (~28%)**: every same-commit recovery seen in the run list — includes
  scheduled re-runs and re-triggered workflows, not just a human pressing rerun.
- **Attempt-level (~75%)**: runs GitHub recorded as re-run at least once
  (`run_attempt ≥ 2`) whose first attempt genuinely failed (validated on a random
  sample of 400 re-run runs — 83 had a genuinely failed first attempt, 63 finished
  green — via `GET .../attempts/1`).

## Recovery by event type (entry-level)

| Trigger | Red episodes | Same-commit re-run | Recovered | Rate |
|---|---:|---:|---:|---:|
| Developer-triggered (push, PR, dispatch) | 9,296 | 1,371 | 306 | 22.3% |
| Automated (schedule, workflow_run, ...) | 729 | 400 | 189 | 47.2% |
| Other | 22 | 14 | 3 | 21.4% |

Automated re-runs recover more often (nightly/periodic jobs recovering on a later
run) — which is expected: those runs are not tied to a code change at all.

## Per-repository (entry-level)

| Repository | Red episodes | Same-commit re-run | Recovered | Rate |
|---|---:|---:|---:|---:|
| microsoft/playwright | 1,200 | 229 | 145 | 63.3% |
| rust-lang/rust | 1,168 | 18 | 2 | 11.1% |
| godotengine/godot | 932 | 277 | 1 | 0.4% |
| denoland/deno | 894 | 113 | 20 | 17.7% |
| hashicorp/terraform | 554 | 153 | 67 | 43.8% |
| etcd-io/etcd | 494 | 37 | 6 | 16.2% |
| home-assistant/core | 461 | 18 | 5 | 27.8% |
| vitejs/vite | 458 | 91 | 13 | 14.3% |
| apache/airflow | 457 | 90 | 8 | 8.9% |
| prometheus/prometheus | 425 | 53 | 41 | 77.4% |
| pytorch/pytorch | 392 | 95 | 6 | 6.3% |
| pandas-dev/pandas | 343 | 8 | 1 | 12.5% |
| vuejs/core | 313 | 182 | 107 | 58.8% |
| grafana/grafana | 243 | 43 | 1 | 2.3% |
| spring-projects/spring-boot | 223 | 23 | 8 | 34.8% |
| vercel/next.js | 196 | 103 | 18 | 17.5% |
| pnpm/pnpm | 180 | 58 | 11 | 19.0% |
| rails/rails | 169 | 13 | 2 | 15.4% |
| angular/angular | 160 | 51 | 7 | 13.7% |
| eslint/eslint | 145 | 16 | 7 | 43.8% |
| webpack/webpack | 136 | 11 | 0 | 0.0% |
| sveltejs/svelte | 135 | 20 | 0 | 0.0% |
| numpy/numpy | 117 | 30 | 9 | 30.0% |
| n8n-io/n8n | 109 | 27 | 7 | 25.9% |
| grpc/grpc | 78 | 13 | 2 | 15.4% |
| encode/django-rest-framework | 23 | 1 | 0 | 0.0% |
| golang/go | 21 | 0 | 0 | — |
| microsoft/TypeScript | 18 | 11 | 4 | 36.4% |
| psf/requests | 2 | 1 | 0 | 0.0% |
| jquery/jquery | 1 | 0 | 0 | — |

> Wide per-repo spread (0–77%) reflects very different CI setups: matrix builds,
> flaky-test handling, approval-gated environments. This is why the headline number
> is an aggregate, not a promise about any single project.
