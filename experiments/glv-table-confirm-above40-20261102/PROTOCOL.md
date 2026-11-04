# Protocol: held-out confirmation that a 64- or 128-entry GLV table beats main's 32 at 42-46 bits

**Frozen before any data on the seed below was generated.** This round
*confirms or fails to confirm* one hint; it does not search. No parameter is
changed after the first row exists. Observation, interpretation and hypothesis
are kept apart in the report.

## Background

`glv_rho_solve` (`src/curve.c`) doubles its r-adding table while
2r <= sqrt(n/m) / (12 log2 n), capped at 32 (rule c = 12, #1065). At 42-46
bits it picks r = 32 for every curve. The above-40-bit round (#1090, seed
20261031, 650/450/300 single-target curves per family at 42/44/46 bits) found
no per-cell effect (every Bonferroni interval contained 1), but its
descriptive pooled geometric mean over 42-50 bits was r64 0.968 [0.936, 0.999]
and r128 0.962 [0.937, 0.991] (95%, intervals touching 1). That is a hint
from a round that was not designed to confirm it. This round asks the one
question on new curves.

## Hypothesis (one-sided, stated before the data)

> **H1.** The geometric mean over the six cells {j = 1728, j = 0} x {42, 44,
> 46 bits} of group_ops(arm) / group_ops(main), the ratio of the arm's
> `curve_solve` group operations to main's on the same targets, is below 1,
> for arm = r64 (64-entry table) and for arm = r128 (128-entry table).

Null: the ratio is 1 or above. Raw `curve_solve` group operations only; no wall
time (a wall-time claim needs a Tier 1 run), no pricing of native work, and no
ranking of methods (AGENTS.md section 5a would need the 0 / 0.1 / 1 GAE band).

## Builds

`aburan28/cryptanalysis` main **ae86c73** (2026-10-31) plus `force-r.patch`,
which adds one measurement-only compile flag, `CA_GLV_FORCE_R`, off by
default. It is the #1090 patch with a new directory name in its comment; the
code is the same. `cmake -DCMAKE_BUILD_TYPE=Release -DCA_CUPQC=OFF
"-DCMAKE_C_FLAGS=<flags>"`, target `cryptanalysis`. The cycle escape (#953)
stays **on** in every arm (no `CA_GLV_CYCLE_ESCAPE=OFF` build exists here).

| arm | flags | role |
|---|---|---|
| main | none (r = 32 here) | baseline; also runs the rho reference |
| r64 | `-DCA_GLV_FORCE_R=64` | decision |
| r128 | `-DCA_GLV_FORCE_R=128` | decision |
| r32 | `-DCA_GLV_FORCE_R=32` | identity control |
| r8 | `-DCA_GLV_FORCE_R=8` | positive control |

## Design

- **Families:** j = 1728 (y^2 = x^3 + ax, p = 1 mod 4) and j = 0
  (y^2 = x^3 + b, p = 1 mod 3). Curves from `run.py`'s `sample_curve` (same as
  #1090: largest prime factor r of #E with exactly the stated bits, cofactor
  <= 16).
- **Seed 20261102**, never used before (not 20261017, 20261022-20261025,
  20261031). Curves come from `"20261102:<family>:<bits>"`, targets from
  `"20261102:<p>:<a>:<b>:0"`, `curve_solve` and rho seed 1.
- **Grid** (curves per family, **one target per curve**; every arm runs the
  same curves and targets): **42 bits 1600, 44 bits 1130, 46 bits 800**.
- **Controls** (same curves, the first ones of each 42-bit cell): identity
  control r32 on curves 0-99; positive control r8 on curves 0-199.
- **Matched rho** (descriptive): the negation-map rho on main's rows for curves
  0-149 of every cell.
- **Commands** (from the experiment directory, build trees `../b-<arm>`; two
  concurrent processes under `nice -n 10`, at most 2 heavy processes):
  `./run_all.sh p1 j1728:42:1600,j1728:44:1130,j0:46:800` and
  `./run_all.sh p2 j1728:46:800,j0:42:1600,j0:44:1130`, then `gzip rows_*.jsonl`.
  The split balances the two processes (the group-operation work differs by
  about 3%).
- **Pairing and independence:** the same curve and target in every arm, but
  independent walks, so the per-target ratio is noisy; the bootstrap resamples
  curves (rows), which carries both sources of variance.

## Power calculation (done before the data; inputs from #1090's rows)

I recomputed the per-target variance of log(arm/main) from #1090's rows
(delta method for a ratio of means: CV(arm)^2 + CV(main)^2, independent
walks). It is 0.42-0.49 in every one of the 16 (arm, family, bits) cells at
40-46 bits (CV of group_ops about 0.46-0.50 per arm), mean 0.45, so a
per-target standard deviation of 0.67 in log ratio. Mean `curve_solve` cost
per solve, from #1090: j = 1728 1.24 / 2.52 / 4.84 M group ops at 42 / 44 /
46 bits, j = 0 1.03 / 2.12 / 4.19 M.

The pooled statistic is the mean of six cell log-ratios, so
Var = (0.45 / 36) x sum over the six cells of 1/n. The half-width is quoted at
the primary interval's coverage (97.5% two-sided, the Bonferroni interval for
K = 2, z = 2.241). Allocating curves to minimise cost at fixed variance gives
n proportional to 1 / sqrt(cost per curve), i.e. fewer curves at larger sizes.

**Speed on this VM (planning only, not a performance claim):** a disclosed dry
run (below) ran at 5.2 M group ops per second per process including curve
sampling and the rho reference. #1090 assumed 8 M.

| design | curves 42 / 44 / 46 (per family) | CPU-hours | pooled half-width (97.5%) |
|---|---|---|---|
| target of the request | 2460 / 1740 / 1230 | about 4.4 | 1.5% |
| **frozen (best affordable)** | **1600 / 1130 / 800** | **about 2.9 in all** | **about 1.9%** |

**The budget cannot reach a 1.5% half-width.** Reaching it needs about 1.55
times the data, about 4.5 CPU-hours on this VM (about 3 at #1090's 8 M ops/s,
which this VM did not give). The frozen design instead spends the whole 3
CPU-hour allowance on the pooled test. What it resolves, stated in advance:

- **Pooled, both families, per arm** (the primary test): expected half-width
  1.9%, so a true 3% effect (ratio 0.97) is confirmed with probability about
  0.92, a true 3.5% effect (the #1090 point estimate) about 0.98, and a true 2%
  effect about 0.58. Effects below about 1.5% cannot be confirmed here.
- **One family alone** (secondary, K = 6, 99.17% interval): expected
  half-width about 3.1%, so a 3% effect in one family is confirmed with
  probability only about 0.5. Family-alone results are reported with their
  intervals and will often read "not confirmed" even if the effect is real.
- Cells alone (about 3-5% half-width at 95%) resolve nothing; they are
  descriptive.

The CPU budget breakdown (core arms about 2.6 h, rho reference about 0.2 h,
controls about 0.05 h, curve sampling inside these) is a plan; the grid above
is the commitment. If the run takes longer than 3.3 CPU-hours the report says so.

## Analysis (`analyze.py`, frozen with this file)

### Invariants (`analyze.py` stops, writing nothing, if any fails)

- every answer is correct in every arm and in the rho reference;
- every arm has exactly the frozen grid (r32: 42-bit curves 0-99; r8: 42-bit
  curves 0-199; rho on main: curves 0-149 of every cell), with the same curves
  and targets as main, no duplicates;
- main's rule picks r = 32 for every curve (the baseline is the r = 32 table);
- **identity control:** forced r = 32 gives `group_ops` identical to main on
  every row of its grid (shows the flag changes nothing else);
- the escape stays on in every arm (by construction: no escape-off build).

### Primary test (the confirmation)

For each arm in {r64, r128}, the statistic is
exp(mean over the six cells of log(sum arm ops / sum main ops)) (ratio of sums
per cell, geometric mean across the six cells with equal weight). Bootstrap
over curves within each cell independently, 10,000 draws.

- **Number of comparisons: K = 2** (r64 and r128, families pooled).
- Each gets the Bonferroni-adjusted two-sided percentile interval at coverage
  1 - 0.05 / 2 = **97.5%**.
- **H1 is confirmed for an arm only if the upper bound of its 97.5% interval is
  below 1.** The two arms are not compared with each other. If both are
  confirmed, no choice between 64 and 128 is made from this data; the one with
  the lower point estimate is named and the difference is reported as
  unresolved if the intervals overlap.
- If neither is confirmed the report says so plainly: "not confirmed", with the
  intervals. A point estimate below 1 with an interval containing 1 is not
  a confirmation.

### Secondary (family-alone)

The same statistic for j = 1728 and for j = 0 alone (three cells each), per arm:
4 more comparisons, so **K = 6 over the whole family** and a 99.167% interval;
confirmed per family only if its upper bound is below 1. These are reported
with their half-widths; a family-alone "not confirmed" does not weaken a
confirmed pooled result, because the pooled result is the registered primary
test.

### Positive control

r8 against main on 42-bit curves 0-199, both families pooled (ratio of sums per
family, geometric mean): passes if the 95% interval's lower bound is above 1 (a
table of 8 cost about 20% at 40-42 bits in #1090). If it fails, the power of
the whole round is in doubt and the report says so.

### Descriptive, not decision

Per cell: ratio and 95% interval for each arm; mean S = group_ops / sqrt(r / m)
for main and S = group_ops / sqrt(r) for rho; main's and each arm's operations
as a fraction of rho's on the same targets (the distance remaining to matched
rho, the owner's success criterion, not a pass/fail gate; raw group
operations, not priced). Per size, both families pooled.

## What the result can and cannot support

- **Can support:** a follow-up proposal to raise the table cap above 32 at
  42-46 bits (a separate change to `src/curve.c`, not made in this PR), if H1
  is confirmed for an arm, in group operations.
- **Cannot support:** a wall-time claim (larger tables cost cache and
  inversion-batch work; wall time needs a Tier 1 run and is the user's decision),
  an effect below the stated power, any conclusion outside 42-46 bits, or a
  ranking between table sizes 64 and 128.
- **If not confirmed:** the larger-table hint from #1090 is not supported at the
  power above, and the report states that.

## Dry runs (disclosed)

Before freezing: (1) seed 1, 20-30 curves per family at 42/44/46 bits, arms
main and r64, to time the solves and measure the rate used above; (2) seed 7,
3-6 curves per cell on all five arms, to exercise `run_all.sh` and
`analyze.py` end to end (no invariant failed). None of those rows is part of
this experiment, and none was used for the hypothesis, the grid-shape
reasoning (power inputs come from #1090's published rows), or the verdict rules.
