# Protocol: Tier 1 wall time of the size-dependent GLV table cap (#1341) at 38-48 bits

**Frozen before any Tier 1 timing.** The workflow that produces the timing starts only after this
file is pushed and its PR is open (a later push, after a `[skip ci]` first push). No wall-time
number from the authoring VM has been looked at: the authoring-VM runs below printed the operation
count, the recovered-scalar hash and `verified` only, and their timers were filtered out.

## Question

#1341 changes `glv_rho_solve` in `src/curve.c` only: the r-adding table cap is `lg >= 40 ? 128 : 32`
(`lg` is the bit length of the subgroup order), where main caps the table at 32 for every size. Held-out
operation counts (#1340, seed 20261106) gave a pooled ratio main / candidate of 0.9849 [0.9725, 0.9978]
at 40-43 bits, j1728 0.968 [0.953, 0.984] and j0 1.002 [0.986, 1.019] (descriptive). That is an
operation count; this round asks what the change costs in **wall time** on the repository's Tier 1 path
(AGENTS.md "CPU performance evidence tiers", docs/ISOLATED_BENCHMARKS.md). The predecessor round
(experiments/glv-table-walltime-above40-20261103, #1337) timed the unconditional cap 128 (#1335) at 42,
44, 46 bits and found that the per-operation cost did not rise and the wall ratio followed each panel's
operation ratio. This round times the size-dependent rule, adds the 40-41 bit boundary, the 48-bit size
above anything measured, and a **38-bit null cell** where the two builds run identical code.

## Arms (both built by the workflow from these commits)

| arm | what it is | source |
|---|---|---|
| ref | main, table cap 32 at every size | `1ee4f47e962aac7f0f09781e34fccfaec1c6456e` |
| cand | #1341 head: `rcap = lg >= 40 ? 128 : 32` | `e71ebecaf3a076590ddd3affa4878b4c80d85095` |

cand's parent is ref. The diff is `src/curve.c` only (the `rcap` line and a comment). Build on the runner:
`cmake -DCMAKE_BUILD_TYPE=Release -DCA_CUPQC=OFF`, target `cryptanalysis_static`, then
`cc -O3 -std=c11 -static` for `bench_glv_panel.c`. Binary hashes are recorded by the runner
(`binaries.sha256`), not frozen. The authoring-VM builds hash `4b5036ec...` (ref, identical to the
predecessor round's ref) and `46ec2439...` (cand), printed in the workflow log for comparison; if the
runner's bytes differ the report says so.

**The 38-bit cell is a null/identity cell.** Below 40 bits both arms pick the same table (cap 32), so
the two builds execute the same walks (the authoring-VM operation counts are equal, below). Any wall
difference there is timing noise plus a binary-layout effect of the changed `src/curve.c`; it measures
the noise floor of this method and is not an effect of the change. It is reported as such and is not
pooled into anything. 40 and 41 bits are the boundary where the cap first becomes 128 (the table is
128 when the budget allows it; at these sizes it does, per the cap rule in `src/curve.c`).

## Workload (frozen panels, `make_panel.py`)

- **Families, never pooled:** j = 1728 (`y^2 = x^3 + a x`, p = 1 mod 4) and j = 0 (`y^2 = x^3 + b`,
  p = 1 mod 3), through `ca_curve_solve` (GLV). Separate manifests per family and size: 14 cells.
- **Sizes and targets per cell** (one target per curve; chosen now, before any timing):

| bits | 38 (null) | 40 | 41 | 42 | 44 | 46 | 48 |
|---|---|---|---|---|---|---|---|
| targets | 20 | 30 | 30 | 30 | 20 | 20 | 20 |

  30 targets at 40-42 bits, where a target costs about 0.1-0.2 s, narrow the walk-realization spread
  (the per-arm CV of a cell's operation sum is about 0.47 / sqrt(targets)); the budget does not allow
  more above 44 bits. Subgroup order `r` has exactly that many bits, prime, cofactor at most 16, sampled
  exactly as the predecessor's `make_panel.py` (which copied #1332's `sample_curve`).
- **Seed 20261107**, new (not 20261017, 20261022-20261025, 20261031, 20261102, 20261103, 20261106).
  Curves come from `"20261107:<family>:<bits>"`, scalars from `"20261107:<p>:<a>:<b>:0"`; the walk seed is
  7 + target index. The panels hold public points only; the scalars never reach a timed process.
- **Expected results** (FNV-1a hash of the true scalars, computed by `make_panel.py`, not by a binary):

| cell | expected result | cell | expected result |
|---|---|---|---|
| j1728 38 | `df0e321174cab70d` | j0 38 | `9aedb9a35af40064` |
| j1728 40 | `e17910cf4d6d0a22` | j0 40 | `bc1c64b3522430a2` |
| j1728 41 | `08c446f53a24a1d1` | j0 41 | `10c8b94b6652f498` |
| j1728 42 | `71f73a5e27536b25` | j0 42 | `292a1304c2716d4a` |
| j1728 44 | `6f7d867cfd4fe4f8` | j0 44 | `5ba26e797b37f1b2` |
| j1728 46 | `85052ca772d3c208` | j0 46 | `02f564dd7c4be57b` |
| j1728 48 | `6f24ba6e350b1abd` | j0 48 | `c867c507fbe9bdda` |

- **Sizing.** The workflow limit is 90 minutes. The predecessor's runner measured about 118 ns per
  operation (j1728) and 151 ns (j0). With the operation counts below, one alternating pair over all 14
  cells is about 200 s, so 15 pairs are about 51 minutes plus 5-6 minutes of builds. 48 bits is about
  45% of the measurement time. A **time guard** protects the receipts: a cell that would start after 65
  minutes of job time is skipped, written as `skipped_<cell>.txt`, and reported as not run (it would be
  the last cells, 48 bits). Pairs per cell are fixed at 15 and not reduced.

## Disclosed before freezing (deterministic counts, not timings)

`group_ops` on the frozen panels from the authoring-VM binaries (the walks are seeded, so these are exact
on any host). Every run returned the expected hash with `verified=1`.

| cell | ops ref | ops cand | ops ref / cand |
|---|---|---|---|
| j1728 38 | 5,367,135 | 5,367,135 | 1.000 (identical) |
| j1728 40 | 19,980,537 | 19,238,143 | 1.039 |
| j1728 41 | 30,445,863 | 32,046,409 | 0.950 |
| j1728 42 | 35,456,302 | 37,730,289 | 0.940 |
| j1728 44 | 52,641,620 | 43,876,222 | 1.200 |
| j1728 46 | 70,559,505 | 86,368,560 | 0.817 |
| j1728 48 | 180,476,457 | 177,447,193 | 1.017 |
| j0 38 | 5,373,344 | 5,373,344 | 1.000 (identical) |
| j0 40 | 15,432,496 | 19,918,027 | 0.775 |
| j0 41 | 24,851,387 | 24,428,846 | 1.017 |
| j0 42 | 34,299,162 | 31,931,176 | 1.074 |
| j0 44 | 44,895,611 | 40,815,005 | 1.100 |
| j0 46 | 80,807,883 | 73,508,313 | 1.099 |
| j0 48 | 158,525,474 | 167,137,135 | 0.948 |

**These panel ratios are one realization of seeded walks and scatter widely** (0.775 to 1.200), as the
per-arm CV of about 0.47 / sqrt(targets) (9-11%) predicts; they are not an estimate of the population
saving (#1340's pooled 0.9849). The wall ratio of a cell is (its ops ratio) times (the ns-per-operation
ratio); the ops ratio is fixed by the panel and is not the test here. **The quantity this round
measures is the cost per group operation, in each cell, and the wall ratio on that panel.**

## Executable and timer

`bench_glv_panel.c`, unchanged from the predecessor round: sets up every group and target first (outside
the timer), then times, with `CLOCK_MONOTONIC` (`online_ms`) and process CPU time (`cpu_ms`), the sum of
`ca_curve_solve` over the targets plus a replay check (found . G == target). It prints `verified=1` only
if every replay matched, with the operation total and the scalar hash.

## Host and gate

A GitHub-hosted `ubuntu-24.04` runner, started by
`.github/workflows/glv-cap-by-size-tier1.yml`, `scripts/isolated_bench.py run` in Tier 1: **15 alternating
reference/candidate pairs** per cell, both arms pinned to one CPU. Fourteen manifests
(`manifest_<family>_<bits>.json`), run in the order j1728 then j0 at 38, 40, 41, 42, 44, 46, 48. The
runner invalidates any pair with a throttle, OOM, steal-time increment, major fault, failed verification,
timeout, or changed input, source or binary. One workflow run is started. It is repeated only if it fails
before any pair ran for a reason in the workflow and not in the code, and then with the repair written
as an amendment file (never an edit of this one); a run that produced pairs is never repeated to improve
a result.

## Claim rule (same as the predecessor)

- **Reported per cell, no pooling across sizes or families:** the runner's median paired ratio
  (ref `online_ms` / cand `online_ms`; above 1 means cand is faster) with its 95% paired bootstrap
  interval over the 15 pairs, the valid-pair count, the CPU-time ratio (`cpu_ms`), the operation ratio
  (`ops`), and ns per operation for each arm (median `online_ms` over `ops`).
- **Speedup:** claimed only where the runner fills `paired_speedup` (interval lower bound above 1). Even
  then it is scoped to that panel on that instance, and the report states the panel's ops ratio beside it.
- **Slowdown:** "resolved slower" means the interval's upper bound is below 1.
- **Otherwise:** not resolved.
- **Cost per operation:** ns-per-operation ratio (ref / cand) = wall ratio / ops ratio, interval scaled
  by the same constant. "Cand costs more per operation" only where that interval's upper bound is below
  1, "cand costs less" only where its lower bound is above 1.
- **Null cells:** at 38 bits the same quantity is the noise floor and layout effect, reported as a
  deviation from 1.000. A resolved 38-bit deviation bounds how much of any other cell's per-operation
  difference can be read as an effect of the cap.
- **Projection (descriptive, not a claim):** #1340's pooled 0.9849 times a cell's cand / ref ns-per-op
  ratio, only for 40-42 bits, combining two samples of different curves.
- **Failed preflight or gates:** the rows are kept and no tier is assigned.

## Predictions, written before the run (they can be wrong)

- **P0 (null cell):** at 38 bits the ref/cand wall ratio is within +/-1% of 1.000 for both families
  (identical code and operation counts).
- **P1 (cost per operation):** at 40-48 bits, in every cell the ns-per-operation ratio (ref / cand) is in
  [0.97, 1.03]; the 128-entry table (about 6 KiB with its scalar tables) stays in L1/L2 and setup is
  negligible beside 10^6-10^8 walk steps. If a direction exists it is cand slightly cheaper per
  operation at j0 (fewer fruitless cycles), as the predecessor round saw (1.013-1.024 at 42-44).
- **P2 (wall follows operations):** in every cell at 40-48 bits the wall ratio is within 3% of the
  panel's ops ratio (table above). So cand is resolved faster in the cells whose ops ratio is at least
  1.04 (j1728 44, j0 42, j0 44, j0 46) and resolved slower in the cells whose ops ratio is at most 0.96
  (j1728 41, 42, 46; j0 40, 48). Cells with an ops ratio inside 0.97-1.03 (j1728 40 at 1.039 and
  j1728 48 at 1.017 and j0 41 at 1.017) may go either way; I make no sign prediction for them.
- **P3 (no hidden cost):** no cell at 40-48 bits has a resolved ns-per-operation increase of more than
  3%. In particular 48 bits, above anything timed before, is not worse per operation than 46.
- **P4 (what this does not show):** the 14 intervals will be narrow (under 1% wide) because they are 15
  timings of one frozen panel; they will not say whether the population wall ratio is above or below 1.

## What follows

- **If P0-P3 hold:** the size-dependent cap's wall effect per cell is its operation effect, per panel;
  the wall saving at 40-42 bits on the population is expected near #1340's operation saving (about 1.5%
  pooled; about 3% for j1728, none for j0), which these panels cannot resolve.
- **If P0 fails by more than 1%:** the instrument has a layout/noise floor that large, and every other
  cell's per-operation ratio is read against it.
- **If P3 fails:** the report names the cells; the operation saving would not be a wall saving there.

## Limits

- **Scope:** two families, 38-48 bits, single thread, one runner instance and CPU model, one run (Tier 1,
  instance-scoped; `host_exclusivity_proved` is false for Tier 1).
- **Each cell is one 20- or 30-target panel.** Its intervals describe timing noise on that panel, not
  variation across curves or walks, and the walks are seeded, so each panel's operation ratio is one
  realization (the predecessor saw 0.98 to 1.24 at 20 targets; here 0.775 to 1.200). A population wall
  claim needs more targets or repeated panels (seeds); this round does not make one. Only the
  ns-per-operation ratio is panel-independent, and only for this runner and these builds.
- **Not tested:** sizes above 48 bits (the cap stays 128 and nothing is measured), 34-39 bits (identical
  code to main; only 38 bits is run as the null), multi-thread, cache behavior directly, escape and cycle
  counts, other curve families.

## Data files

The report, chart and summaries are committed. Raw receipts live in the workflow artifact (30 days).
Data-suffixed files over the artifact-store thresholds (docs/artifacts.md) stay out of Git; the session
that made this experiment has no store credentials, so the raw artifact archive and PDF are pending a
store push. Summaries and hashes are committed instead.
