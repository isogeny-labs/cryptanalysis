# Protocol: held-out confirmation of the plain-rho change selected in #1093 (frozen before data)

Frozen on 2026-10-30 in the first commit of this PR, before any row of this experiment exists and before the code
change is committed. The selection round (#1093, seed 20261025) selected, by its frozen rule, the arm
`F+B+D128+R1.5`. This PR makes that arm the default of `ca_rho_solve` and confirms it on curves and targets that
no earlier round used.

## The change (committed after this protocol)

For `ca_rho_solve` with the negation map and default parameters:

- **F** a walk escapes a 2- or 4-cycle as soon as its new point equals the point two or four committed steps back
  (the same deterministic escape from the cycle's minimum as the 64-step window);
- **B** on elliptic curves, the multiplier table, walk starts and restarts use tables of 2^b * base and 2^b * target
  (each set bit one operation, the table doublings charged to setup);
- **D128** the `dp_bits` rule targets 128 distinguished points per walk instead of 32;
- **R1.5** the table size is the power of two nearest to 1.5 * sqrt(sqrt(n) / (floor(log2 n) + 1)), within [8, 1024],
  instead of the budget rule sqrt(n) / (48 lg).

Without the negation map the old rules stay (not tested). User-supplied `r`, `dp_bits` and `walks_per_thread` are unchanged.

## Comparison

`main` at `3321bbfb129b` (library built from it unchanged) against the candidate (the same source with the change).
One solve per (curve, target) per library, same solver seed, one thread; metric `ca_stats.group_ops`, a deterministic count.
No wall time is measured or claimed.

## Workload (held out)

- Seed `20261026`; sizes 20, 24, 28, 32, 36, 40 bits (bits of the prime subgroup order r); 40 random generic curves per size x 50 targets = 2,000 paired solves per size.
- Curves y^2 = x^3 + a x + b, random a, b != 0 over a prime p of about size+3 bits, cofactor <= 16 (`run.py: sample_curve`); same generator as #1092 and #1093, new seed.

## Analysis (`analyze.py`)

- Per size: ratio of sums candidate / main; bootstrap over curves (10,000 resamples, numpy seed 20261026). Pooled: geometric mean of the six per-size ratios, 95% percentile interval (one primary comparison). Per-size intervals Bonferroni-adjusted over 6 sizes.
- **Confirmed** iff: every logarithm of both libraries is correct, the pooled upper bound is below 1, and no size has an interval whose lower bound is above 1.
- Reported with the result: the selection round's pooled ratio (0.7558, interval [0.7462, 0.7653]) next to this one. A held-out ratio above the selection interval is reported as selection optimism, not hidden.

## Predictions (written before the data)

The change reproduces the selected arm exactly (checked on the 8,000 selection solves at 20 to 32 bits before this run), so the expected pooled ratio is near 0.756 with per-size ratios near 0.666, 0.624, 0.599, 0.886, 0.905, 0.934 (20 to 40 bits).

## Limits (declared in advance)

- Operation counts, not time. A larger table, a smaller DP spacing and fixed-base tables change memory traffic; wall time needs a Tier 1 run.
- Generic curves with the negation map, one thread. Other groups and thread counts are untested.
- Native work outside `group_ops` (field inversions, cache effects) is not priced here.
