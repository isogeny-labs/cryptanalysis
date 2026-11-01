# Protocol: Tier 1 wall time of a 128-entry GLV table at 42-46 bits

**Frozen before any Tier 1 timing.** The workflow that produces the timing starts only after this
file is pushed and its PR is open (a later push, after a `[skip ci]` first push).

## Question

Held-out round #1332 (seed 20261102) confirmed that a forced 128-entry r-adding table in
`glv_rho_solve` saves about 2% of `curve_solve` group operations against main's 32 entries, pooled
over j = 1728 and j = 0 at 42 / 44 / 46 bits: 0.9802 [0.9627, 0.9978]. A 64-entry table was not
confirmed. That is an operation count; no wall-time claim exists. A larger table changes memory
traffic and, in this walk, the number of fruitless cycles and escapes, so the cost per operation can
move either way. Code-change PR #1335 raises the cap from 32 to 128 (`rr * 2 <= 128`) and says it must
not merge before 34-41 bits are tested. This round measures wall time at 42-46 bits on the
repository's Tier 1 path (AGENTS.md "CPU performance evidence tiers", docs/ISOLATED_BENCHMARKS.md).
It is not a test of 34-41 bits, where the change also alters the table and nothing is measured.

## Arms (both built by the workflow from these commits)

| arm | what it is | source |
|---|---|---|
| ref | main, table cap 32 (r = 32 at 42-46 bits) | `1ee4f47e962aac7f0f09781e34fccfaec1c6456e` |
| cand | #1335's head: main plus the cap 128 (r = 128 at 42-46 bits) | `a50f66e58a29100bdde45edb5fa480e5a650bbf5` |

The two commits differ in `src/curve.c` only: the constant `32` becomes `128` in the table rule and
the comment is extended. Build on the runner: `cmake -DCMAKE_BUILD_TYPE=Release -DCA_CUPQC=OFF`,
target `cryptanalysis_static`, then `cc -O3 -std=c11 -static` for `bench_glv_panel.c`. Binary hashes
are recorded by the runner (`binaries.sha256`), not frozen. The authoring-VM builds hash
`4b5036ec…` (ref) and `a8d681a5…` (cand), printed in the workflow log for comparison; if the runner's
bytes differ the report says so.

## Workload (frozen panels, `make_panel.py`)

- **Families:** j = 1728 (`y^2 = x^3 + a x`, p = 1 mod 4) and j = 0 (`y^2 = x^3 + b`, p = 1 mod 3),
  through `ca_curve_solve` (GLV).
- **Sizes:** subgroup order `r` of 42, 44 and 46 bits, cofactor at most 16, prime `r`, sampled exactly
  as #1332's `run.py` (`sample_curve`).
- **Targets:** 20 curves per cell and one target per curve, so six panels of 20 targets (j1728 and j0
  at 42, 44, 46). Seed **20261103**, new (not 20261017, 20261022-20261025, 20261031, 20261102). Curves
  come from `"20261103:<family>:<bits>"`, scalars from `"20261103:<p>:<a>:<b>:0"`; the walk seed is
  7 + target index. The panels hold public points only.
- **Expected results** (FNV-1a hash of the true scalars, computed by `make_panel.py`, not by a binary):

| cell | expected result |
|---|---|
| j1728 42 | `add90c0620e05454` |
| j1728 44 | `3cdad2dad2b47a28` |
| j1728 46 | `b4d2498d85594f80` |
| j0 42 | `2238fdc8de800392` |
| j0 44 | `c0fd377da42fe994` |
| j0 46 | `38e3bf6fa208938d` |

- **Sizing.** The workflow job limit is 90 minutes. One pass of both arms over all six panels took
  about 135 s on the (shared) authoring VM, so 15 alternating pairs are about 34 minutes there; the
  runner is expected to be slower, and 20 targets leaves room for a runner about 1.6 times slower
  plus the builds. No wall-time number from the authoring VM is reported anywhere.

## Disclosed before freezing (deterministic counts, not timings)

`group_ops` on the frozen panels, counted by the authoring-VM binaries (the walks are seeded, so these
are exact for any host). The panel is small, so these ratios carry the variance of one realization of
the walks: the per-target CV of `group_ops` is about 0.47 (#1332), so a 20-target cell sum has a CV of
about 10% per arm.

| cell | ops ref | ops cand | ops ref / cand |
|---|---|---|---|
| j1728 42 | 28,180,383 | 25,794,973 | 1.092 |
| j1728 44 | 53,269,322 | 51,601,990 | 1.032 |
| j1728 46 | 107,933,124 | 104,232,246 | 1.036 |
| j0 42 | 21,620,931 | 17,386,651 | 1.244 |
| j0 44 | 46,977,145 | 39,779,807 | 1.181 |
| j0 46 | 74,981,067 | 76,282,978 | 0.983 |

Consequence for reading the result: the wall-time ratio of a cell is (ops ratio on the panel) times
(ns-per-operation ratio). The ops ratio is already fixed by the panel and is not the test here.
**The quantity this round measures is the cost per group operation**, and the wall ratio on a panel
is a statement about that panel.

## Executable and timer

`bench_glv_panel.c`: sets up every group and target first (outside the timer), then times, with
`CLOCK_MONOTONIC` (`online_ms`) and process CPU time (`cpu_ms`), the sum of `ca_curve_solve` on each
target plus a replay check (found . G == target). It prints `verified=1` only if every replay
matched, with the operation total and the scalar hash.

## Host and gate

A GitHub-hosted `ubuntu-24.04` runner, started by
`.github/workflows/glv-table-walltime-above40-tier1.yml`, `scripts/isolated_bench.py run` in Tier 1:
**15 alternating reference/candidate pairs** per cell, both arms pinned to one CPU. Six manifests
(`manifest_<family>_<bits>.json`), run in the order j1728 42, j0 42, j1728 44, j0 44, j1728 46,
j0 46. The runner invalidates any pair with a throttle, OOM, steal-time increment, major fault,
failed verification, timeout, or changed input, source or binary. One workflow run is started; it is
not repeated or retried to improve a result (a failed infrastructure step before any pair is
reported as such).

## Claim rule

- **Reported per cell, no pooling across sizes or families:** the runner's median paired ratio
  (ref `online_ms` / cand `online_ms`; above 1 means cand is faster) with its 95% paired bootstrap
  interval over the 15 pairs, the valid-pair count, the CPU-time ratio (from `cpu_ms`), the operation
  ratio (from `ops`), and ns per operation for each arm (median `online_ms` over `ops`).
- **Speedup:** claimed only where the runner fills `paired_speedup` (interval lower bound above 1).
  Even then it is scoped to that panel on that instance, and the report states the panel's ops ratio
  beside it.
- **Slowdown:** "resolved slower" means the interval's upper bound is below 1.
- **Otherwise:** not resolved.
- **Cost per operation:** the ns-per-operation ratio (ref / cand) is the wall ratio divided by the
  ops ratio, and its interval is the wall interval divided by the same constant (the operation counts
  are identical in every pair). It is reported for each cell. "Cand costs more per operation" is
  claimed only where that interval's upper bound is below 1 and "cand costs less" only where its
  lower bound is above 1.
- **Projection, labelled as such:** (#1332's pooled 0.9802 operation ratio) times (a cell's measured
  ns-per-operation ratio, cand / ref) is quoted only as a descriptive projection that combines two
  samples of different curves. It is not a claim.
- **Failed preflight or gates:** the rows are kept and no tier is assigned.

## Predictions, written before the run (they can be wrong)

I expect the table size to change the cost per operation little (a 128-entry table is 128 group
elements, about 6 KiB with the two scalar tables, which fits in L1/L2), and the setup cost is a
negligible part of a 20-target cell at 42 bits and above. So:

- **P1 (cost per operation):** in every cell, cand's ns per operation is within +/-3% of ref's
  (ref/cand ns-per-operation ratio in [0.97, 1.03]).
- **P2 (wall follows operations):** in every cell the wall ratio is within 3% of the panel's ops ratio
  (the table above). Consequently the sign of "faster or slower" follows the ops ratio: cand faster
  (interval lower bound above 1) in j1728 42 and j0 42 and 44; j1728 44 and 46 near 1.03 and
  resolved faster if the noise allows; **j0 46 slower** (ops ratio 0.983, upper bound below 1).
- **P3 (no hidden cost):** I do not expect a resolved ns-per-operation increase of more than 3% in any
  cell. If one appears, it is the finding and it would explain why a 2% operation saving does not
  become a 2% wall saving.

## What follows

- **If P1 and P2 hold:** the 128-entry table's wall effect at 42-46 bits is its operation effect.
  The report says so, per cell, with the panel-realization caveat, and the 34-41 bit range is still
  untested. This round makes no wall-time claim for the unpooled population, since 20 targets per cell
  carry about 10% walk-to-walk noise against a 2% effect.
- **If P3 fails:** the report says that cand costs more per operation in the named cells and that the
  2% operation saving of #1332 should not be read as a wall-time saving until a larger panel is run.

## Limits

- **Scope:** two families, 42-46 bits, single thread, one runner instance and CPU model, one run.
- **Intervals** come from 15 pairs of the same frozen 20-target panel, so they describe timing noise on
  that panel, not variation across curves or walks. They are narrow for that reason, and they cannot
  confirm or refute a 2% effect on the population. Only the ns-per-operation ratio is a
  panel-independent quantity, and only for this runner and these builds.
- **Not tested:** 34-41 bits, where #1335 also changes the table; sizes above 46; multi-thread; memory
  use and cache behavior directly; the cycle escape's share of the cost.

## Data files

The report and chart are committed. Raw receipts live in the workflow artifact (30 days).
Data-suffixed files over the artifact-store thresholds (docs/artifacts.md) stay out of Git; the
session that made this experiment has no store credentials. Summaries and hashes are committed
instead.
