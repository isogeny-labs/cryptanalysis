# Protocol: GLV multiplier-table size and the j = 0 walk, 26–40 bits

**Frozen before any data on the seed below was generated.** This round
*selects*. Any rule it suggests is confirmed on separate held-out curves in a
later round, under a new protocol, before it becomes a speed claim.

## Background

`experiments/glv-table-size-20261022/` (#1059, exploratory) found:

- **Table size drives cycling.** In `glv_rho_solve`, the size of the r-adding
  table controls how often walks enter fruitless cycles. Main picks r = 8 up to
  about 30 bits, then 16, then 32 from about 36 bits up.
- **A larger table helped at 32 bits.** At 32 bits, a 32-entry table beat
  main's choice (j = 0 0.938, j = 1728 0.943). It tied at 28 bits and lost at
  24 bits.
- **j = 0's covariant walk is unreachable on main.** It is not dispatched on
  `main`. Main's walk beats it below 36 bits and loses at 36–40 bits.

## Questions

1. For each family (j = 1728, j = 0) and size, which table size (main's rule,
   16, 32 or 64) gives the fewest `curve_solve` group operations?
2. For j = 0, at which sizes does the covariant walk use fewer operations than
   main's walk?

## Builds (aburan28/cryptanalysis `main` 7cb3dce)

Every arm builds `7cb3dce` plus `measure-arms.patch`. The patch adds two
measurement-only compile flags, both off by default:

- `CA_GLV_FORCE_R` overrides the table size.
- `CA_J0_FORCE_COVARIANT` routes generic j = 0 `curve_solve` to
  `glv_covariant_rho_solve`.

Build: `cmake -DCMAKE_BUILD_TYPE=Release -DCA_CUPQC=OFF "-DCMAKE_C_FLAGS=<flags>"`,
target `cryptanalysis`.

| arm | flags | libcryptanalysis.so sha256 |
|---|---|---|
| main | none | `d08661e8514027aa449a2afc3b50fa455bd31aa6daea9bcb612f9bd967abd0bd` |
| r16 | `-DCA_GLV_FORCE_R=16` | `cf6a32d49de265e6810b89d793a5da7df0709d2698134e71512e696f19e89b61` |
| r32 | `-DCA_GLV_FORCE_R=32` | `e5b082bc85dab25bd45a14072d9966ce2bfa536986a0abced4abb59696a2862d` |
| r64 | `-DCA_GLV_FORCE_R=64` | `10084aae51547228b5210e467583f6ea2d5f0b9643335899a385a06b2b86e36c` |
| cov | `-DCA_J0_FORCE_COVARIANT` | `a72fb4a86802bce562a630f9a37b580e86e8e83bb8b986b62da3eba4c3ce16e0` |

Two pre-run checks pass, both using `fingerprint.py` (80 solves, seed 20261017):

- **`main` equals `7cb3dce`.** The `main` arm's fingerprint equals that of
  `7cb3dce` built with its own defaults (md5 `cf7021e5…`).
- **`cov` equals the old covariant walk.** The `cov` arm's j = 0 fingerprint
  equals the covariant walk's counts recorded in #1059
  (`raw/fingerprint_j0_dispatch.json`).

## Design

- **Families:** j = 1728 (y² = x³ + ax, p ≡ 1 mod 4) and j = 0 (y² = x³ + b,
  p ≡ 1 mod 3).
- **Curve sampling:** `run.py`'s `sample_curve`. The subgroup order r is the
  largest prime factor of #E, with exactly the stated number of bits and a
  cofactor of at most 16.
- **Sizes:** r of 26, 28, 30, 32, 34, 36, 38 and 40 bits.
- **Sample:** 120 curves × 25 targets per family and size.
- **Seed:** **20261022**. It is new: no earlier run used it. Curves come from
  `"20261022:<family>:<bits>"` and targets from
  `"20261022:<p>:<a>:<b>:<t>"`. `curve_solve` seed = t + 1.
- **Arms:** every arm solves every target, except `cov`, which runs on j = 0
  only. The `main` arm also runs the negation-map rho on each target
  (`--rho`, seed t + 1) as the reference.
- **Command:** `CRYPTANALYSIS_LIB=b-<arm>/libcryptanalysis.so python3 run.py --arm <arm> --out rows_<arm>.jsonl [--rho]`.
  The five arms run concurrently on one 4-core host, followed by `gzip`.

## Analysis (`analyze.py`, frozen with this file)

### Invariants

`analyze.py` stops, writing nothing, if any of these fail:

- **Correctness:** every answer is correct, in every arm and in the rho reference.
- **Grid:** every arm has exactly main's grid of curves and targets (j = 0 only
  for `cov`), with identical curves and targets, and no row is duplicated.
- **Identity control:** wherever main's own rule picks the same table size as
  a forced arm, the two arms give identical `group_ops` on every target.

### Metric

The metric is the ratio of an arm's `curve_solve` group operations to main's,
computed per family and size and paired on the same targets. Operations are
summed over a curve's targets; the ratio is the sum over curves of the arm
divided by the sum over curves of main.

- **Intervals:** bootstrap over curves, 10,000 draws. The 95% interval is
  descriptive. The decision interval is Bonferroni-adjusted over K = 56
  comparisons (3 forced tables × 2 families × 8 sizes, plus `cov` × 8 sizes),
  which makes it a 99.911% interval.
- **Verdicts:**
  - "fewer ops than main" if the adjusted upper bound is below 1.
  - "more ops than main" if the adjusted lower bound is above 1.
  - "not resolved" otherwise.
- **Selection (question 1):** per family and size, the table arm with the
  smallest point ratio, with main counting as 1. A size where no forced table
  is resolved as fewer is reported as "keep main".
- **Crossover (question 2):** the sizes where `cov` is resolved as fewer, and
  the sizes where it is resolved as more.
- **Descriptive only:** each arm's `curve_solve` / rho ratio.

## What the result can and cannot support

- **It can support:** a proposed size-dependent table rule, and a proposed
  j = 0 dispatch threshold, each to be tested on held-out curves (new seed,
  frozen in advance) before any change to `src/curve.c` is merged as a speed
  improvement.
- **It cannot support:** a wall-time claim, or claims above 40 bits.
- **Dry run (disclosed):** before freezing, the scripts were exercised on
  seed 1 with 3 curves × 3 targets at 26 and 40 bits. Its rows are not part of
  this experiment.
