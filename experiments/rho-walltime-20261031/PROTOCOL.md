# Protocol: Tier 1 wall time of the plain negation-map rho change (#1327)

**Frozen before any Tier 1 timing.** The workflow that produces the timing starts only after this
file is pushed and its PR is open (a separate dispatch, after a `[skip ci]` push).

## Question

#1327 makes four changes to `ca_rho_solve` (src/rho.c) for the negation map: (F) an immediate 2- or
4-cycle escape, (B) fixed-base tables for setup, (D128) 128 distinguished points per walk instead of
32, (R1.5) a larger table. Its held-out confirmation (seed 20261026) shows group operations at
0.748 [0.741, 0.756] of main's pooled over 20-40 bits, and says in its own limits that larger
tables, a smaller DP spacing and fixed-base tables change memory traffic, so the wall effect is
unknown. This round measures it, on the repository's Tier 1 path (AGENTS.md "CPU performance
evidence tiers", docs/ISOLATED_BENCHMARKS.md).

## Observation disclosed before freezing (exploratory, not part of this experiment)

On the authoring VM (a 4-vCPU KVM that fails the Tier 1 preflight and was shared with another
heavy job), the frozen panels and binaries gave, in single runs pinned to one CPU:

| bits | operations ref / cand | wall ms, ref | wall ms, cand | wall ms, var |
|---|---|---|---|---|
| 28 | 2.58M / 1.64M | 204 | 147 | not run |
| 32 | 5.67M / 5.31M | 364 | 576 | not run |
| 36 | 25.3M / 22.1M (var 22.4M) | 1713-2131 (6 runs) | 2533-3211 (6 runs) | 2027, 2235 (2 runs) |
| 40 | 87.2M / 80.0M | 5857 | 7461 | not run |

Candidate CPU time, not just wall time, was higher at 36 bits. These are not measurements of the
change: the host was contended and the runs are few. They are why this round has a third arm and
why the predictions below are stated now.

## Arms (all built by the workflow from these commits)

| arm | what it is | source |
|---|---|---|
| ref | #1327's base | `3321bbfb129b6101a6279bb40edb1b51ff61f7e6` |
| cand | #1327's head (identical code to `a4d8111`; the head adds one cppcheck suppression comment) | `921b595559fdf8a91cff627cb60bc962ba56b50b` |
| var | cand with the old DP spacing (32 per walk) in place of D128; **a measurement arm, not proposed** | cand + `d32.patch` |

Build on the runner: `cmake -DCMAKE_BUILD_TYPE=Release -DCA_CUPQC=OFF`, target
`cryptanalysis_static`, then `cc -O3 -std=c11 -static` for `bench_rho_panel.c`. Binary hashes are
recorded by the runner (`binaries.sha256`), not frozen. The authoring-VM builds, with the same
compiler version, hashed `e0ac43df…` (ref), `45ac6774…` (cand), `9d4add68…` (var); if the runner's
bytes differ the report says so.

## Workload (frozen panels, `make_panel.py`)

- **Curves:** generic `y^2 = x^3 + a x + b` over `F_p` with `a, b != 0`, so no GLV structure and
  `ca_curve_solve` runs the negation-map rho with default parameters (one thread).
- **Sampling:** `p` a random prime of `bits + 3` bits; `r` the largest prime factor of `#E` with
  exactly `bits` bits and cofactor at most 16.
- **Sizes:** `r` of 28, 32, 36 and 40 bits. **100 targets per size** (20 curves x 5 targets).
- **Seed:** 20261101, new. Walk seed 7 + target index. The panels hold public points only.
- **Expected results:** the FNV-1a hash of the true scalars, computed by `make_panel.py`, not by
  any binary.

| bits | expected result |
|---|---|
| 28 | `83f07e54545bc4bf` |
| 32 | `fd7b198b5937fcb5` |
| 36 | `8c5f56a20412cfc9` |
| 40 | `0f2e31dd46ae5627` |

## Executable and timer

`bench_rho_panel.c`: sets up every group and target first (outside the timer), then times, with
`CLOCK_MONOTONIC` (`online_ms`) and process CPU time (`cpu_ms`), the sum of `ca_curve_solve` on each
target plus a replay check (found . G == target). It prints `verified=1` only if every replay
matched, with the operation total and the scalar hash.

## Host and gate

A GitHub-hosted `ubuntu-24.04` runner, started by `.github/workflows/rho-walltime-tier1.yml`,
`scripts/isolated_bench.py run` in Tier 1: **15 alternating reference/candidate pairs** per size and
comparison, both arms pinned to one CPU. Eight manifests: sizes 28, 32, 36, 40 for ref vs cand
(`manifest_<bits>.json`) and for ref vs var (`manifest_<bits>_var.json`).

The runner invalidates any pair with a throttle, OOM, steal-time increment, major fault, failed
verification, timeout, or changed input, source or binary.

## Claim rule

- **Reported per size and comparison:** the runner's median paired ratio (ref `online_ms` / other
  arm's `online_ms`; above 1 means the other arm is faster) with its 95% paired bootstrap interval,
  the valid-pair count, CPU-time ratio and operation ratio.
- **Speedup:** a Tier 1 speedup is claimed only where the runner fills `paired_speedup` (interval
  lower bound above 1).
- **Slowdown:** "resolved slower" means the interval's upper bound is below 1.
- **Otherwise:** not resolved.
- **Failed preflight or gates:** the rows are kept and no tier is assigned.
- **No pooling across sizes:** the panels are per size, so size does not weight the result.

## Predictions, written before the run (they can be wrong)

- **P1:** cand is faster than ref at 28 bits.
- **P2:** cand is slower than ref at 32, 36 and 40 bits, resolved at 36 and 40.
- **P3:** var is not slower than ref at 36 and 40 bits, while using about the same operations as
  cand. If P2 and P3 both hold, the denser DP spacing is the cause of the wall-time cost.

## What follows

- **If P2 holds:** #1327 as written trades 13% fewer operations for a wall-time regression at
  32-40 bits. The report then says so, and proposes the variant without D128 as a follow-up. That
  variant has its own operation-count record to settle first: in the selection round (#1093) D128
  alone saved no operations (pooled 1.002). It would need a fresh held-out confirmation under its
  own frozen protocol before any claim.
- **If P2 fails:** #1327's wall-time effect is reported as measured.

## Limits

- **Scope:** generic curves, single thread, 28-40 bits, one runner instance and CPU model per run.
- **Panels:** 100 targets per size.
- **Not measured:** memory use and cache behavior directly.

## Data files

The report and chart are committed. Raw receipts live in the workflow artifact (30 days). Data-suffixed
files over the artifact-store thresholds (docs/artifacts.md) stay out of Git; the session that made
this experiment has no store credentials. Summaries and hashes are committed instead.
