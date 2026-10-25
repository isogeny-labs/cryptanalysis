# Protocol: the GLV walk's cycle escape inside the batched inversion

Frozen before the confirmatory data exists. The commit that adds this file and
`PROTOCOL.sha256` is pushed, and its pull request opened, before `run.py` is run
for the arms below. Everything dated before that commit is labelled exploratory.

## Question

`glv_rho_solve` (src/curve.c) leaves a fruitless 2- or 4-cycle by one affine
doubling (#953, `CA_GLV_CYCLE_ESCAPE`). The doubling is `ca_group_op`, outside the
walk's batched (Montgomery trick) inversion, so it pays a full field inversion,
while it is counted as one group operation. #1083 measured the c = 12 table
change at 1.8% / 3.3% fewer group operations but 4.0% / 6.6% less Tier 1 wall
time; the hypothesis was that escapes explain part of that gap.

## Exploratory findings (seed 20261024, 100 solves per cell, main's default walk; not evidence for a claim)

* One escape = exactly 1 field inversion + 6 (j = 1728) or 8 (j = 0) multiplications + 2 squarings.
  One batched step = (1/W) inversions + about 9 multiplications + 2 squarings; W is
  about 4 (26 bits) to 125 (36 bits).
* The inversion is `ca_invmod`: a 64-bit extended Euclid with a hardware division
  per step, 17 to 23 steps at 26 to 36 bits. The library has no measured
  inversion-to-multiplication ratio, so the price is an assumption (below).
* Priced so, an escape costs 2x to 12.6x one batched step. It happens 0.3 to
  14 times per 10^4 steps on main's rule, so escapes are 0.01% to 0.46% of
  the walk's field cost, and the part above their share of group operations is
  0.004% to 0.34%. The escape cannot explain a 2.2 point wall/operation gap on
  main's table; at the old table 8 (18 escapes per 10^4 steps) it could explain
  at most about 0.7 points.
* Counters do not change anything: operation counts of the counted build equal
  main's on 1200 solves.

## Candidate

`-DCA_GLV_BATCH_ESCAPE=ON` (default OFF, needs `CA_GLV_CYCLE_ESCAPE`). When a walk
detects the cycle it records the cycle member P (chosen exactly as now: smallest
hash) and its exponents, and its slot in the next batched operation computes
P + P (the batch already handles a == b as a doubling). The next iteration
finishes the escape (exponents doubled, class reduction, hash, data-point and
abandon tests) with exactly the state the inline doubling produced. So every
walk entering the same cycle still leaves to the same point, the sequence of
points each walk visits is unchanged, and the doubling is still one group
operation (one of the W the iteration counts). The only change is the iteration
in which that walk's data-point test happens, which can reorder which walk
reports a collision first.

## Arms

* `main`: current walk, `-DCA_GLV_FIELD_COUNT=ON` (counters only).
* `batch`: the same plus `-DCA_GLV_BATCH_ESCAPE=ON`.

Same source tree, `-DCMAKE_BUILD_TYPE=Release -DCA_CUPQC=OFF`. Counters are
single-threaded; `Group.curve_solve` runs one thread.

## Data

`run.py` with defaults: seed 20261025 (fresh curves; the exploratory seed was
20261024), families j1728 and j0, sizes 26, 28, ..., 36, 200 curves per cell,
10 targets per curve, solver seed target + 1; 24000 solves per arm. Curves and
targets come from the sampler of `experiments/glv-table-rule-20261022/run.py`.

## Field-operation price (assumptions)

Per solve, summed over setup, batched steps, post-step, escape and restart
phases: cost = M + 0.8 S + d E, where M, S are field multiplications and
squarings (a Montgomery REDC each, counted), E is the number of division steps
inside the inversions (counted exactly), and d is the price of one division
step in multiplications: d = 1, 2.5, 5 (an inversion at 20 steps then costs 20,
50, 100 multiplications). Additions, subtractions and the scalar arithmetic mod
n (identical in both arms) are not priced. No wall time is measured.

## Analysis

Per (family, size) cell and per price d: ratio of sums batch / main over all the
cell's solves, percentile bootstrap over curves (10000 resamples), Bonferroni
level 0.05 / 36 (12 cells x 3 prices) per interval. A cell **wins** when the
upper bound is below 1 at all three prices and **regresses** when the lower
bound is above 1 at any price. Also reported (same intervals): group
operations, field inversions, multiplications plus squarings.

## Checks and decision rule

1. Every solve in both arms returns the right answer, or the result is void.
2. Group operations: the arms' walks are the same except for the timing above, so
   the ratio of sums of `ops` is expected within 1 +/- 0.001 in every cell; a
   cell outside that is reported and explained, or the change is not proposed.
3. The default build (no flags) must reproduce main's operation counts exactly
   (fingerprint on the exploratory 1200 solves: sha256 47c7ce34cc8e2bf40b7309b211a6516e3b2b258609571b7a0012a57903674162).
4. **Verdict**: the change is proposed if there is no regressing cell and at
   least 9 of the 12 cells win; it is reported as marginal if there is no
   regression and fewer wins; it is not proposed if any cell regresses.
5. Prediction, from the exploratory run: field cost ratios between 0.997 and
   1.000 (largest effect at small sizes and j = 1728); group operations
   unchanged. Whatever the outcome, the gap to the matched rho is not changed
   by this work and is not re-stated.

## Not claimed

Wall time. This protocol makes no wall-time statement; whether a Tier 1 run is
warranted is a decision for the report's reader.
