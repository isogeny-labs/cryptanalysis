# Protocol: held-out operation-count confirmation of the cap-128 GLV table rule at 34-40 bits

**Frozen before any data on the seed below was generated.** This round
*confirms or fails to confirm* one hypothesis about the rule as shipped in
PR #1335; it does not search. No parameter changes after the first row exists.
Observation, interpretation and hypothesis are kept apart in the report.

## Background

`glv_rho_solve` (`src/curve.c`) sets its r-adding table by doubling r from 8
while `2r <= rbudget` and `2r <= cap`, with `rbudget = (isqrt(n/m) + 1) /
(12 * bitlen(n))`, `m` = `aut_order` (4 for j = 1728, 6 for j = 0) and `n` the
subgroup order. Main caps r at 32. PR #1335 (branch `glv-table-cap-128`, commit
`a50f66e`) changes only the cap, 32 to 128. Its support is PR #1332 (seed
20261102): a *forced* 128 table saved 0.9802 [0.9627, 0.9978] of main's group
operations at 42-46 bits; PR #1337 (Tier 1) showed per-operation cost did not
rise there. Nothing has been measured where the **rule** itself changes the
table below 42 bits. This round measures the rule, not a forced r, where it
first acts.

### Table size r chosen by each rule (recomputed here from min and max n)

`n` ranges over `[2^(bits-1), 2^bits - 1]` (the largest prime factor with
exactly `bits` bits), `lg = bitlen(n)`. A range means r depends on n inside the
bit length; "32" under main and "128" under the cap-128 rule mean every curve.

| bits | j1728 main | j1728 cap 128 | j0 main | j0 cap 128 |
|---|---|---|---|---|
| 32 | 32 | 32-64 | 32 | 32-64 |
| 33 | 32 | 64 | 32 | 64 |
| 34 | 32 | 64-128 | 32 | 64-128 |
| 35 | 32 | 128 | 32 | 64-128 |
| 36 | 32 | 128 | 32 | 128 |
| 37-41 | 32 | 128 | 32 | 128 |

(The formula is `rule()` in `analyze.py`. Below 32 bits the cap is never
reached, so the two rules agree for every n.) Because the
rules differ for every curve from 33 bits up, there is no 33- or 34-bit cell
where the ratio is exactly 1; the only mixed bit length in the grid is 32,
where some curves run identical code under both rules. The grid therefore has
no padding cell where nothing changes.

## Hypothesis (one-sided, stated before the data)

> **H1.** The geometric mean over the eight cells {j = 1728, j = 0} x {34, 36,
> 38, 40 bits} of group_ops(cand) / group_ops(main), the ratio of
> `curve_solve` group operations under the #1335 rule to main's on the same
> targets, is below 1.

Null: the ratio is 1 or above. Raw `curve_solve` group operations only: no wall
time (that needs a Tier 1 run), no pricing of native work, no ranking of
methods (AGENTS.md section 5a would need the 0 / 0.1 / 1 GAE band; not invoked).

## Builds (all `cmake -DCMAKE_BUILD_TYPE=Release -DCA_CUPQC=OFF`, target `cryptanalysis`)

Main is pinned at `1ee4f47` (2026-10-31, the tip when this was frozen). The
only difference between main and cand in `src/` is the cap.

| arm | source | flags | role |
|---|---|---|---|
| main | `1ee4f47` `src/curve.c` | none | baseline (cap 32); also runs the rho reference |
| cand | `a50f66e` `src/curve.c` (#1335, unchanged) | none | decision: cap 128 |
| capid | cand + `cap-force.patch` | `-DCA_GLV_CAP=32` | identity control (code equals main's) |
| r8 | cand + `cap-force.patch` | `-DCA_GLV_FORCE_R=8` | positive control |

`cap-force.patch` adds two measurement-only macros to `a50f66e`'s line: `CA_GLV_CAP` (default 128, so
unflagged it is the same code) and `CA_GLV_FORCE_R`. The cycle escape (#953) is
on in every arm.

## Design

- **Families:** j = 1728 (y^2 = x^3 + ax, p = 1 mod 4) and j = 0 (y^2 = x^3 + b,
  p = 1 mod 3). Curves from `run.py`'s `sample_curve`, **unchanged from the
  #1332 run** (largest prime factor of #E with exactly the stated bits,
  cofactor <= 16), so the two rounds are comparable.
- **Seed 20261104**, never used before (not 20261017, 20261022-20261025,
  20261031, 20261102, nor the dry-run seeds 1 and 7). Curves from
  `"20261104:<family>:<bits>"`, targets from `"20261104:<p>:<a>:<b>:0"`,
  `curve_solve` and rho seed 1. One target per curve.
- **Grid (curves per family):** 34, 36, 38, 40 bits: **4000 each** (primary);
  32 bits: 1000 (descriptive only, outside the primary pool). Eight primary
  cells with equal weight in the pooled statistic. Bit length 41 is not run;
  the secondary split is 34-36 against 38-40.
- **Controls:** identity control `capid` on curves 0-99 of every cell (all ten);
  positive control `r8` on curves 0-299 of the 40-bit cells (decision) and of
  the 34-bit cells (descriptive).
- **Matched rho (descriptive):** the negation-map rho on main's rows for curves
  0-149 of every cell.
- **Commands** (experiment directory, build trees `$BUILDS/b-<arm>`, two
  concurrent processes under `nice -n 10`, never more than two heavy processes):
  `./run_all.sh p1 j1728:40:4000,j0:38:4000,j1728:34:4000,j0:36:4000,j1728:32:1000`
  and `./run_all.sh p2 j0:40:4000,j1728:38:4000,j1728:36:4000,j0:34:4000,j0:32:1000`,
  then `gzip rows_*.jsonl`. The split balances the work to about 1%.
- **Pairing:** the same curve and target in every arm, but independent walks
  (different table sizes change the walk), so the per-target ratio is noisy;
  the bootstrap resamples curves, which carries both sources of variance.

## Power calculation (done before the data)

Per-target variance of log(arm/main) from #1090 and #1332 rows: about 0.45
(CV of group_ops about 0.46-0.50 per arm; a seed-1 dry run at 34-40 bits gave
CV 0.30-0.61 per cell with 20 curves each, consistent). Pooled variance of the
mean of K_c cell log-ratios is `0.45 * sum(1/n_c) / K_c^2`.

Measured speed on this shared VM (dry run, planning only, not a performance
claim): about 0.55 s per curve per arm summed over the eight primary cells
(curve sampling included), i.e. about 3.5 M group ops per second per process.
Estimated cost of the frozen design: core arms about 1.2 CPU-hours, rho
reference about 0.05, controls about 0.1; **about 1.4 CPU-hours in all**,
under the 3 CPU-hour allowance. The request's target half-width was about
1.5% (reachable with about 1300 curves per cell); with the budget available I
chose 4000 per cell, which is below the allowance and gives:

| quantity | expected half-width | note |
|---|---|---|
| **pooled, 8 cells (primary, 95%, K = 1)** | **0.74%** | confirms a true 1.5% saving with probability about 0.98, a 2% saving about 0.9997, a 1% saving about 0.76 |
| one family or one size half (4 cells, 98.75%, K = 4) | 1.3% | secondary |
| one size, both families (2 cells, 95%) | 1.5% | descriptive |
| one cell (95%) | 2.1% | descriptive |
| 32-bit cell (1000 curves, 95%) | 4.2% | descriptive |

Effects below about 0.7% cannot be told from zero. The positive control (r8
over main at 40 bits, 300 curves per family) expects a half-width near 5%; the
#1332 value at 42 bits was 1.221 [1.145, 1.305].

## Analysis (`analyze.py`, frozen with this file)

### Invariants (`analyze.py` stops, writing nothing, if any fails)

- every answer is correct in every arm and in the rho reference;
- every arm has exactly its frozen grid, the same curves, targets and subgroup
  order as main, no duplicates; rho on main is on exactly curves 0-149 of every cell;
- **identity control:** `capid` gives `group_ops` identical to main on every row;
- **equal-r rows:** every row where `rule(n, cap 32) == rule(n, cap 128)` (the
  32-bit curves with a small n) has identical `group_ops` in cand and main
  (same code path and seeds).

### Primary test (the confirmation)

Statistic: exp(mean over the eight primary cells of log(sum cand ops / sum
main ops)) (ratio of sums per cell, geometric mean across cells with equal
weight). Bootstrap over curves within each cell independently, 10,000 draws.

- **K = 1** comparison; two-sided percentile interval at **95%**.
- **H1 is confirmed only if the upper bound of the pooled interval is below 1.**
- If the lower bound is above 1 the report says the rule **increases** group
  operations at 34-40 bits ("worse"), with the interval. Otherwise "not
  confirmed". A point estimate below 1 with an interval containing 1 is not a confirmation.

### Secondary (labelled secondary)

Four comparisons, so **K = 4 and a 98.75% interval** each, with the same rule
(upper bound below 1 = confirmed for that subset, lower bound above 1 = worse):
j = 1728 alone and j = 0 alone (four cells each); and the **size split**, sizes
34-36 against 38-40 (four cells each, both families), because the saving may
differ with size. The difference between the two halves (ratio of the two
pooled ratios, 95% interval) is reported descriptively. A subset "not confirmed"
does not weaken a confirmed pooled result.

### Positive control

r8 against main at 40 bits on curves 0-299, both families (geometric mean of the
two family ratios of sums): passes if the 95% interval's lower bound is above 1.
If it fails the power of the round is in doubt and the report says so. The 34-bit r8
cell is descriptive.

### Descriptive, not decision

Per cell: ratio and 95% interval, the number of curves at each table size under
each rule, mean S = group_ops / sqrt(n / m) for main and cand, S = group_ops /
sqrt(n) for rho; main's and cand's operations as a fraction of rho's on the same
targets (the distance remaining to matched rho, the owner's success criterion,
not a pass/fail gate; raw group operations, not priced). Per size with both
families pooled, including the 32-bit cells. Post hoc, the per-cell delta-method
variance of log(cand/main) is reported to check the 0.45 power input.

## What the result can and cannot support

- **Can support:** whether the #1335 rule saves group operations (operation
  counts only) in the 34-40 bit range where it changes the table, and how that
  saving compares with the 2% found at 42-46 bits.
- **Cannot support:** any wall-time claim (cache and batch costs: Tier 1 run,
  the user's decision), an effect below the stated power, anything outside
  32-40 bits (bit lengths 41-46 are covered by #1332; above 46 is untested), or
  a ranking between table sizes.
- **If not confirmed or worse:** the report states it plainly with the intervals and
  the recommendation reflects it (for example a cap that depends on size).

## Dry runs (disclosed)

Before freezing: (1) seed 1, 20 curves per cell at 34/36/38/40 bits, both
families, arms main and cand (5 rho curves), then arms capid and r8 on j1728 34, j0 34 and j1728 36 (20
curves each), to time the solves and exercise the builds; (2) seed 7, 12 curves per
primary cell and 6 at 32 bits, all four arms, with `A6_DRY=1` shrinking the
grids, to exercise `run_all.sh`, `analyze.py` and `chart.py` end to end (no
invariant failed). **I saw the dry-run ratios**: at seed 1, cand over main was
between 0.92 and 1.47 per cell with 20 curves per cell (pooled above 1 in most
cells, i.e. no saving visible), and at seed 7 the pooled ratio was 1.13 [0.99,
1.28] with 12 curves per cell. Those samples are too small to read; they did not
change the design, the hypothesis or any decision rule, and the possibility that
the rule *costs* operations in this range is exactly why "worse" is a registered
outcome. None of those rows is part of this experiment.
