# Protocol: does the GLV table rule still hold above 40 bits? (42-50 bits)

**Frozen before any data on the seed below was generated.** Everything here is
decided before the first row exists. This round *measures*; any rule it
suggests goes to a held-out confirmation round under a new protocol first.

## Background

`glv_rho_solve` (`src/curve.c`, main `fb70171`) doubles its r-adding table
while 2r <= sqrt(n/m) / (12 log2 n), capped at 32 (#1065 confirmed c = 12).
Earlier rounds (#1059, #1061, #1065) measured 26-40 bits and found:

- a 64-entry table never helped at 26-40 bits;
- the 2/4-cycle escape (#953) gain vanished above about 36 bits, because with
  r = 32 fruitless cycles are already rare.

Nobody has measured above 40 bits. At 42-50 bits main's rule picks r = 32 for
every curve (checked by `analyze.py`).

## Questions

1. For j = 1728 and j = 0 at 42, 44, 46, 48 and 50 bits (40 as a bridge to the
   earlier rounds): does a 64- or a 128-entry table use fewer `curve_solve`
   group operations than main's r = 32?
2. Does the cycle escape (main's look-ahead kept, `-DCA_GLV_CYCLE_ESCAPE=OFF`)
   still change the operation count?
3. Descriptive: each cell's curve_solve / negation-map rho ratio, the distance
   remaining to matched rho (owner's success criterion). These are raw group
   operation counts, not priced; no ranking of methods is made from them
   (AGENTS.md section 5a would need the 0 / 0.1 / 1 GAE band).

## Builds (aburan28/cryptanalysis `main` fb70171, recorded in REPORT.md)

Every arm builds main plus `force-r.patch`, which adds one measurement-only
compile flag, `CA_GLV_FORCE_R`, off by default. Build:
`cmake -DCMAKE_BUILD_TYPE=Release -DCA_CUPQC=OFF "-DCMAKE_C_FLAGS=<flags>"`,
target `cryptanalysis`.

| arm | flags | role |
|---|---|---|
| main | none (r = 32 here) | baseline, also runs the rho reference |
| r64 | `-DCA_GLV_FORCE_R=64` | decision |
| r128 | `-DCA_GLV_FORCE_R=128` | decision |
| noesc | `-DCA_GLV_CYCLE_ESCAPE=OFF` | decision |
| r32 | `-DCA_GLV_FORCE_R=32` | identity control, 40 and 42 bits |
| r8 | `-DCA_GLV_FORCE_R=8` | positive control, 40 and 42 bits |

## Design

- **Families:** j = 1728 (y^2 = x^3 + ax, p = 1 mod 4) and j = 0
  (y^2 = x^3 + b, p = 1 mod 3). Curves from `run.py`'s `sample_curve`
  (largest prime factor r of #E with exactly the stated bits, cofactor <= 16).
- **Seed:** **20261031**, new (not 20261017, 20261022-20261025). Curves come
  from `"20261031:<family>:<bits>"`, targets from `"20261031:<p>:<a>:<b>:0"`,
  `curve_solve` and rho seed 1.
- **Grid** (curves per family, **one target per curve**; pairing is per
  target): 40 bits 800, 42 bits 650, 44 bits 450, 46 bits 300, 48 bits 170,
  50 bits 85. Sizes up the scale get fewer targets because a solve costs
  about 2^(bits/2); the budget is about 3 CPU-hours over 2 processes (measured
  at about 8 M group ops/s per process). **Power limit, stated in advance:**
  with independent walks per arm the per-target ratio has a standard deviation
  near 1, so a cell resolves only effects of roughly 3.3 / sqrt(targets) in
  ratio: about 13% at 42 bits, 20% at 46 bits, 36% at 50 bits for the walk-changing arms
  (r64, r128). The noesc arm shares the walk until the first escape and is far
  tighter. Smaller effects are not excluded; they are reported as "not
  resolved" with the interval.
- **Commands:** from this directory, with build trees `../b-<arm>`:
  `./run_all.sh p1 50:85,48:170,40:800` and
  `./run_all.sh p2 42:650,44:450,46:300` run concurrently (2 processes,
  `nice -n 10`), then `gzip rows_*.jsonl`. Controls r8 and r32 run on 40 and
  42 bits only, on the same curves.
- **No wall time.** Counts of `group_ops` only; wall time needs a Tier 1 run.

## Analysis (`analyze.py`, frozen with this file)

### Invariants (`analyze.py` stops, writing nothing, if any fails)

- every answer is correct in every arm and in the rho reference;
- every arm has exactly the frozen grid (controls: sizes 40 and 42), the same
  curves and targets as main, no duplicates;
- main's rule picks r = 32 for every curve;
- **identity control:** forced r = 32 gives `group_ops` identical to main on
  every row of its grid (shows the flag changes nothing else).

### Metric and verdicts

Per family and size, the ratio of an arm's `curve_solve` group operations to
main's on the same targets (ratio of sums per curve; each curve is one
target). Bootstrap over curves, 10,000 draws. The 95% interval is descriptive.
The decision interval is Bonferroni-adjusted over K = 36 comparisons
(3 arms x 2 families x 6 sizes), a 99.861% interval. "Fewer ops than main" if
the adjusted upper bound is below 1, "more ops" if the adjusted lower bound is
above 1, otherwise "not resolved". Question 1 is answered "a larger table
wins" only if r64 or r128 is resolved as fewer in some cell; otherwise "no
larger table is resolved as better", with the intervals as the bound.
Question 2: the cells where noesc is resolved as more ops (the escape still
earns) or fewer.

### Positive control

r8 against main, 40 and 42 bits, both families pooled (ratio of sums): the
detector passes if the 95% interval's lower bound is above 1 (a table of 8 is
known from #1059 and #1061 to cost operations at 36-40 bits). If it fails, the
power of the decision cells is in doubt and the report says so.

### Descriptive, not decision

Per arm and family (and both), the geometric mean of the 42-50 bit cell
ratios, 95% bootstrap interval (cells resampled independently). Each arm's
curve_solve / rho ratio per cell, and the mean S = group_ops / sqrt(r/m) for
curve_solve and S = group_ops / sqrt(r) for rho.

## What the result can and cannot support

- **Can support:** a proposal for a larger table or for the escape's removal
  above 40 bits, to be confirmed on held-out curves (new seed, frozen in
  advance) before any change to `src/curve.c`.
- **Cannot support:** a wall-time claim; effects below the stated power; any
  conclusion above 50 bits.
- **Dry run (disclosed):** before freezing, the scripts were exercised on seed
  1 with 4 and 6 curves at 40, 42 and 50 bits. Those rows are not part of this
  experiment; no parameter other than the grid sizes (set from the timings)
  was changed after it.
