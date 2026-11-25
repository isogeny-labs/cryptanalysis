# Protocol: held-out confirmation of the size-dependent GLV table cap (cap 128 from 40 bits)

**Frozen before any data on the seed below was generated.** This round
*confirms or fails to confirm* one hypothesis about one code change; it does
not search. No parameter changes after the first row exists. Observation,
interpretation and hypothesis are kept apart in the report.

## Background and the candidate

`glv_rho_solve` (`src/curve.c`) doubles its r-adding table while
`2r <= rbudget` and `2r <= 32` (`rbudget = (isqrt(n/m) + 1) / (12 * bitlen(n))`).
The selection round (#1339, seed 20261105, report commit `07601ee`, 700 curves
per family and size at 38-42 bits) applied a rule frozen before its data and
chose **cap = 32 for bitlen(n) < 40 and cap = 128 for bitlen(n) >= 40**
(r128 pooled 0.982 / 0.970 / 0.969 at 40 / 41 / 42 bits; r64 0.974 / 0.972 /
0.954; the choice of 128 over 64 was a margin of 0.03 percentage points over the
tie width). That selection used the same data it summarised, so its numbers are
optimistic. Earlier rounds: #1332 (forced 128 at 42-46 bits, pooled 0.9802
[0.9627, 0.9978], confirmed), #1338 (cap 128 at every size: worse at 34-36 bits,
neutral at 38-40 bits).

**The candidate is the code change itself:** branch `glv-table-cap-by-size`,
commit **e71ebec** (main 1ee4f47 plus a change to `src/curve.c` only:
`uint32_t rcap = lg >= 40 ? 128 : 32;`). It is the build tested here, not a
patched flag, so the confirmation also covers the code path that will ship.

## Hypothesis (one-sided, stated before the data)

> **H1.** The geometric mean over the eight cells {j = 1728, j = 0} x {40, 41,
> 42, 43 bits} of group_ops(candidate) / group_ops(main), the ratio of the
> candidate's `curve_solve` group operations to main's on the same targets (ratio of
> sums per cell, equal weight per cell), is below 1.

Null: the ratio is 1 or above. Raw `curve_solve` group operations only: no
wall time (needs a Tier 1 run), no pricing of native work (so no ranking of
methods; AGENTS.md section 5a would need the 0 / 0.1 / 1 GAE band), nothing
about sizes outside 38-43 bits.

## Design

- **Builds** (`cmake -DCMAKE_BUILD_TYPE=Release -DCA_CUPQC=OFF`, target
  `cryptanalysis`, no other flags): `main` = commit 1ee4f47 unpatched;
  `cand` = commit e71ebec. The cycle escape is on in both.
- **Families:** j = 1728 and j = 0, curves from `run.py`'s `sample_curve` (the
  same sampler as the selection round and #1090).
- **Seed 20261106**, never used before. Curves from `"20261106:<family>:<bits>"`,
  targets from `"20261106:<p>:<a>:<b>:0"`, solver seed 1, one target per curve.
  Independent walks, same curve and target in both arms.
- **Primary cells** (candidate differs from main: cap 128 against 32): 40, 41,
  42 and 43 bits, **1600 curves per family and size** (12,800 targets per arm).
  43 bits is a size nobody has measured (the earlier rounds are 42/44/46); it is
  in the primary set so the claim covers the range just above the selection grid.
- **Identity cells** (candidate is main's rule, so the ratio must be exactly 1):
  38 and 39 bits, 80 curves per family and size, both builds. Not padding:
  they check that the cap rule changes nothing below the threshold.
- **Matched rho** (descriptive): the negation-map rho on main's rows for
  curves 0-59 of every primary cell.
- **Commands:** `./run_all.sh p1 j1728` and `./run_all.sh p2 j0` under
  `nice -n 10` (two heavy processes), then `gzip rows_*.jsonl`, `analyze.py`,
  `chart.py`.

## Power calculation (before the data)

Per-target variance of log(arm / main) 0.42-0.49 (mean 0.45; sd 0.67), from
#1090, #1332 and #1339 alike. With 1600 curves in each of 8 cells the pooled
statistic has standard error sqrt(0.45 / (1600 x 8)) = 0.0059, and the 97.5%
two-sided interval has half-width about 1.3% (z = 2.24). The probability that
the upper bound falls below 1, for a true pooled ratio of:

| true pooled ratio | 0.975 | 0.980 | 0.985 | 0.990 | 1.000 |
|---|---|---|---|---|---|
| P(confirmed) | 0.97 | 0.87 | 0.61 | 0.29 | 0.01 |

The selection round estimated 0.974 at 40-42 bits, but selecting on those
data biases that figure downward, and #1332 saw 0.989 / 0.984 at 42 / 44 bits.
A true pooled effect near 1.5% is therefore confirmed with probability about
0.6, near 2% about 0.9. **Effects below about 1.3% cannot be confirmed here.**
Per size (both families), the standard error is 0.012; per-size intervals only
rule out a size being worse by more than about 3% (see below).

Cost: about 1.65 CPU-hours at 4.6 M group operations per second per process
(selection used about 0.95 CPU-hours; total for the task stays under 3).

## Analysis (`analyze.py`, frozen with this file)

### Invariants (`analyze.py` stops, writing nothing, if any fails)

- every answer is correct in every arm; every arm has exactly the frozen grid
  with the same curves and targets as main;
- main's rule picks 32 for every curve in every cell; the candidate's rule
  picks 128 for every curve at 40-43 bits and 32 at 38-39 bits (recomputed in
  `analyze.py` from each curve's n);
- **identity:** on every 38- and 39-bit row the candidate's `group_ops` equals main's
  exactly (ratio 1);
- rho on main covers exactly curves 0-59 of every primary cell, all correct.

### Primary test (the confirmation)

Statistic: exp(mean over the 8 cells of log(sum cand ops / sum main ops)).
Bootstrap over curves within each cell independently, 10,000 draws, percentile
interval. **One comparison (K = 1); H1 is confirmed if the upper bound of the
97.5% two-sided interval is below 1.** A point estimate below 1 with an
interval containing 1 is not a confirmation.

### No-worse check (per size)

For each of the four sizes (both families pooled, geometric mean of the two
cell ratios) a Bonferroni interval over the 4 sizes (98.75% two-sided).
**The check fails if any size's interval is wholly above 1** (lower bound > 1).
It does not require every size to be below 1.

### What each outcome means

- **Confirmed and no-worse passes:** the data support the candidate at 40-43
  bits in group operations. The code PR may be merged after a Tier 1
  wall-time run and a user decision; the sizes above 43 rest on #1332 (42-46
  bits, forced 128) and on extrapolation above 46.
- **Confirmed but some size wholly worse:** the report names the size; the
  rule is not recommended as it stands (the threshold would be raised).
- **Not confirmed:** said plainly, with the interval. The code PR stays open
  with that stated and is not recommended for merge. This round does not search
  for a different threshold; a new threshold needs a new frozen round.

### Descriptive, not decision

Per cell: ratio and 95% interval; per family (sizes pooled); main's and the
candidate's mean S = group_ops / sqrt(n / m); rho S = group_ops / sqrt(n); the
candidate's and main's operations as a fraction of rho's on the same targets
(the distance remaining to matched rho, raw group operations, not priced).

## Dry runs and looks at data before the freeze (disclosed)

1. The selection round's full data (#1339) were seen before this freeze; that
   is the purpose of the two-stage design. None of its curves are reused (seed
   differs; `sample_curve` seeds on the seed string).
2. Seed 7, 5 curves per cell, both builds, to run `run_all.sh` and
   `analyze.py` end to end; noise only, no rows kept in this experiment.
