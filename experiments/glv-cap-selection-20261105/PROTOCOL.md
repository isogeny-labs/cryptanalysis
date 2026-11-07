# Protocol: selection round for a size-dependent GLV table cap, 38-42 bits

**Frozen before any data on the seed below was generated.** This is a
*selection* round: it applies one pre-stated rule to choose a candidate
size-dependent cap, and it is exploratory in the sense of the repository's
conventions (#1061). Nothing it measures is a confirmation. A candidate it
selects is tested on held-out curves in a second round, with its own frozen
protocol, written after this round's report is pushed. No parameter, rule or
margin below changes after the first row exists. Observation, interpretation
and hypothesis are kept apart in the report.

## Background

`glv_rho_solve` (`src/curve.c`) doubles its r-adding table while
`2r <= rbudget` and `2r <= 32`, with `rbudget = (isqrt(n/m) + 1) / (12 * bitlen(n))`
(`m` = `aut_order`, 4 for j = 1728 and 6 for j = 0, `n` the subgroup order).

- #1332 (seed 20261102, merged): a forced 128 table against main's 32 at 42, 44,
  46 bits: pooled 0.9802 [0.9627, 0.9978] (97.5%), confirmed; per size 0.989,
  0.984, 0.968; forced 64 not confirmed (0.9905).
- #1338 (seed 20261104): the rule with the cap raised to 128 at *every* size,
  at 34-40 bits: pooled 1.0220 [1.0149, 1.0291], worse; 34 and 36 bits worse by
  4-5%, 38 bits 1.003, 40 bits 0.992.
- #1337 (Tier 1): per-operation cost does not rise with the 128 table at
  42-46 bits.

The data bracket the crossover between 38 bits (neutral) and 42 bits (a saving
of about 1%). This round asks where inside 38-42 a bigger table starts to help,
so that a size-dependent cap (main's rule below a threshold T, a larger cap at
and above it) can be proposed. I read the three reports above before writing
this protocol; they are the priors for the effect sizes in the power
calculation and for nothing else.

At 38-42 bits the *uncapped* rule gives at least 128 for every n (checked in
`analyze.py`, at the smallest n of each size, both families), so a table forced to r = 128 (or 64) is exactly what the rule
produces with the cap raised to 128 (or 64). The measurement-only patch can
therefore force r without changing anything the candidate rule would do at
these sizes.

## Candidate rule family (what the round selects)

```
cap(lg) = 32      for lg <  T      (main's rule, byte for byte)
cap(lg) = C       for lg >= T      with C in {64, 128}, T in {38, ..., 42}
```

`lg` = `glv_ilog2(n) + 1`, the bit length of n, already in the function. The
rule selects T and C by the steps in "Selection rule" below. Above 46 bits
nothing has been measured; that is discussed in the report, not decided here.

## Builds

`aburan28/cryptanalysis` main **1ee4f47** (2026-10-31, tip when this was
frozen) plus `force-r.patch`: one measurement-only compile flag,
`CA_GLV_FORCE_R`, off by default (the #1332 patch with a new directory name in
its comment). `cmake -DCMAKE_BUILD_TYPE=Release -DCA_CUPQC=OFF
"-DCMAKE_C_FLAGS=<flags>"`, target `cryptanalysis`. The cycle escape stays on
in every arm.

| arm | flags | role |
|---|---|---|
| main | none (unpatched source; r = 32 here) | baseline |
| r64 | `-DCA_GLV_FORCE_R=64` | test arm |
| r128 | `-DCA_GLV_FORCE_R=128` | test arm |
| r32 | `-DCA_GLV_FORCE_R=32` | identity control |
| r8 | `-DCA_GLV_FORCE_R=8` | positive control |

## Design

- **Families:** j = 1728 (y^2 = x^3 + ax, p = 1 mod 4) and j = 0 (y^2 = x^3 + b,
  p = 1 mod 3). Curves from `run.py`'s `sample_curve` (the #1090 sampler: largest
  prime factor n of #E with exactly the stated bit length, cofactor <= 16).
- **Seed 20261105**, never used before. Curves come from
  `"20261105:<family>:<bits>"`, targets from `"20261105:<p>:<a>:<b>:0"`,
  `curve_solve` seed 1.
- **Grid:** 38, 39, 40, 41, 42 bits; **700 curves per family per bit length,
  one target per curve** (7000 targets per arm). Every arm runs the same
  curves and targets, with independent walks.
- **Controls:** identity control r32 on curves 0-39 of the 38- and 42-bit cells
  (both families), `group_ops` must equal main's exactly; positive control r8
  on curves 0-99 of the 42-bit cells (both families).
- **Commands** (this directory; build trees `$BUILDS/b-<arm>`; two processes
  under `nice -n 10`): `./run_all.sh p1 j1728` and `./run_all.sh p2 j0`, then
  `gzip rows_*.jsonl`.
- No wall time is measured or claimed anywhere in this round. No rho
  reference is run (it is part of the confirmation round).

## Power calculation (before the data)

Inputs: the per-target variance of log(arm / main) from #1090/#1332 was
0.42-0.49 (mean 0.45; sd 0.67 per target). With 700 curves in each of two
families the standard error of the pooled-family log ratio at one bit length
is 0.67 / sqrt(1400) = 0.018, so a 95% interval for one size is about +/-3.5%.
That is larger than the effects being located (about 1%), so **this round
cannot locate T to better than about +/-2 bits.** I state that in advance.
A Monte Carlo of the selection rule below (normal approximation with that SE,
20,000 draws per profile; `power.py`, committed for reproducibility, is not part of the analysis) gives, for true log-ratio profiles over 38..42 bits:

| true ratio at 38 / 39 / 40 / 41 / 42 | P(GO) | most likely T when GO |
|---|---|---|
| 1 / 1 / 1 / 1 / 1 (no effect anywhere) | 0.13 | 38 (false positive) |
| 1 / 1 / 1 / 1 / 0.989 (step at 42) | 0.26 | 38-40 |
| 1 / 1 / 0.995 / 0.99 / 0.985 | 0.45 | 38-40 |
| 1 / 1 / 0.985 / 0.985 / 0.985 | 0.59 | 38-40 |
| 0.98 at all sizes | 0.81 | 38 |

So a GO from this round is weak evidence by itself (13% false-positive rate
under no effect), and a STOP is weak evidence of no effect (power 0.26-0.59 for
the realistic profiles). That is why the rule is only a *selection* and why
the held-out round, with its own power calculation, decides. If this round
stops, the report says "no size selected at this power", not "no size helps".

Cost: the dry run (below) ran at 4.6 M group operations per second per process
including curve sampling. Per curve and family, summed over the five sizes and
three arms, the grid costs about 2.2 CPU-s per curve per family (about 0.9
CPU-hours in all with the controls, within the one-third share of the 3
CPU-hour allowance).

## Selection rule (fixed here; `analyze.py` implements it)

All quantities are on the **ratio of summed `curve_solve` group operations**
(arm over main, same curves and targets), per family and size, combined across
the two families by the **geometric mean with equal weight**. Write
`L_A(b)` for the log of that pooled ratio for arm A in {r64, r128} at size b
in {38, ..., 42}. Bootstrap: 10,000 draws; within each of the ten (family,
size) cells resample curves with replacement, the same resampled curves for
both arms; percentile intervals.

1. **Trend.** For each arm, fit an ordinary least-squares line to the five
   `L_A(b)` against b (unweighted; the five sizes have equal n and similar
   variance). `f_A(b)` is the fitted log ratio.
2. **Threshold.** `T_A` = the smallest b in {38, ..., 42} such that
   `f_A(b') <= log(0.995)` for every b' from b up to 42. (A fitted saving of at
   least 0.5% at every size from T up. If there is no such b, arm A has no
   candidate.) This resolves non-monotone data by the fit: a single noisy size
   cannot move T on its own, and a fitted line that is not below the margin
   at 42 gives no candidate.
3. **Go gate** (per arm with a candidate). Let `S_A` be the mean of `L_A(b)`
   over b = T_A, ..., 42 (raw, not fitted). The arm is **robust** if (i) the
   one-sided 90% bootstrap upper bound of `S_A` is below 0 (ratio below 1),
   with T_A held at its point-estimate value, and (ii) no size b in
   T_A..42 has its pooled 95% interval wholly above 1 (no size where the
   bigger table is shown to be worse). The bootstrap holds T fixed, so the
   gate is optimistic about selection; the held-out round is the correction.
4. **Choice.** If no arm is robust: **STOP**. Otherwise take the robust arm
   with the lower `S_A`; if both are robust and their `S_A` differ by less than
   0.5% (log difference below 0.005), take the **smaller table (r64)**, the
   conservative choice (less memory per walk and per batch; nothing in this
   round separates them). The rule is `cap = 32` for `lg < T_A` and
   `cap = C` for `lg >= T_A`, C = the arm's table size.
5. **Above 46 bits** (nothing measured): the report states it. The default
   written here is the conservative one in the sense that it introduces no
   table size that has not been measured at 46 bits: the cap stays at C for
   all larger `lg` (the rule's own `rbudget` still limits r), rather than
   reverting to 32, which would make the table shrink with n although the
   saving in #1332 grows from 42 to 46 bits. That extends the claim beyond
   the measured range and the report and the code PR say so; an unmeasured
   range is a Tier 1 question.
6. Report T_A, the fitted ratios, the bootstrap distribution of T_A (stability,
   descriptive), per-size and per-family intervals (descriptive), and the
   verdict.

### Outcomes

- **GO:** write the second protocol (seed 20261106, held-out, candidate
  code built from a pinned commit), after this round's report is pushed.
- **STOP:** no Phase 2; this PR is the result. Two readings are kept apart:
  "the data show no benefit" (all estimates >= 1) versus "not enough power".

### Invariants (`analyze.py` stops, writing nothing, if any fails)

- every answer is correct in every arm;
- every arm has exactly the frozen grid, with the same curves and targets as
  main, no duplicates;
- main's rule picks r = 32 for every curve; the uncapped rule picks >= 128 at
  every size and family (so forced r = what a raised cap would produce);
- **identity control:** forced r = 32 gives `group_ops` identical to main on
  every row of its grid;
- the escape stays on in every arm (by construction).

### Positive control

r8 against main on the 42-bit curves 0-99, both families pooled (ratio of sums
per family, geometric mean): passes if the 95% interval's lower bound is above
1 (an 8-entry table cost about 20% at 40-42 bits in #1090). If it fails, the
round's power is in doubt and the report says so.

### Descriptive, not decision

Per (family, size) cell: ratios and 95% intervals, and main's mean
S = group_ops / sqrt(n / m). The matched rho reference is not run here.

## What this round can and cannot support

- **Can support:** the choice of a candidate (T, C) for a held-out test.
- **Cannot support:** a confirmation, a wall-time claim, a ranking between
  table sizes 64 and 128 (unless the intervals separate them, which is
  reported descriptively), any statement about sizes outside 38-42 bits.

## Dry runs and looks at data before the freeze (disclosed)

1. Seed 1, 30 curves each of j1728 at 38/40/42 bits and j0 at 42 bits, arm
   main only, to time the solver (rate used above; it also gave mean group
   operations per solve: 0.33 M, 0.58 M, 1.16 M, and 1.04 M for j0 at 42).
2. Seed 7, 6 curves per cell, all five arms, to run `run_all.sh` and
   `analyze.py` end to end. Its output was noise (intervals of +/-40%) and
   influenced nothing but fixing two bugs in the scripts (paths, grid
   override). None of its rows is part of this experiment.
3. The Monte Carlo above, which uses no measured rows of this experiment.
4. The reports of #1332, #1338 and #1337, read before freezing (priors).
