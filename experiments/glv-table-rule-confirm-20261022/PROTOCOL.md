# Protocol: held-out confirmation of the GLV table rule c = 12

**Frozen before any data on the seed below was generated.**

## Change under test

`src/curve.c`, `glv_rho_solve`: the table budget becomes
`rbudget = sqrt(n/m) / (12 · log2 n)`, down from `48 · log2 n`. The table
still doubles from 8 while 2r ≤ rbudget, capped at 32. Nothing else changes:
the walk count W, the distinguished points, the escape and the covariant walk
are untouched.

The constant came from a post-hoc rule search on the selection round
(`experiments/glv-table-rule-20261022`, #1061, seed 20261022). There, c = 12
gave a geometric mean of 0.978 over 16 cells. In-sample it gave the following,
which is optimistic because c was chosen on those rows:

| bits | j = 1728 | j = 0 |
|---|---|---|
| 28 | 0.932 | 0.983 |
| 30 | 0.934 | 0.939 |
| 32 | 0.979 | 0.927 |
| 34 | 0.991 | 0.969 |

## Hypothesis

On held-out curves, for each family, the geometric mean of the c = 12 / main
ratios over the 28, 30, 32 and 34-bit cells is below 1.

In-sample geometric means were 0.959 for j = 1728 and 0.954 for j = 0. Expect
less on held-out curves.

## Builds (aburan28/cryptanalysis `main` 7cb3dce)

Build: `cmake -DCMAKE_BUILD_TYPE=Release -DCA_CUPQC=OFF`, target `cryptanalysis`.

| arm | source | libcryptanalysis.so sha256 |
|---|---|---|
| main | `7cb3dce` unmodified | `d08661e8514027aa449a2afc3b50fa455bd31aa6daea9bcb612f9bd967abd0bd` |
| c12 | `7cb3dce` + this PR's `src/curve.c` change | `b5d6d9ec8ff1a2500853888e84760a68bda5f74cbcb048cc2061ff15c55ad6c1` |

Pre-run checks:

- **`main` equals `7cb3dce`.** `main`'s 80-solve fingerprint
  (`experiments/glv-table-rule-20261022/fingerprint.py`) equals that of
  `7cb3dce` (md5 `cf7021e5…`).
- **Tests pass with the change.** The c12 tree passes the full Release
  `ctest` (18 of 18).

## Design

- **Families:** j = 1728 and j = 0, sampled exactly as in the selection round
  (`run.py`).
- **Sizes:** r of 26, 28, 30, 32, 34, 36, 38 and 40 bits.
- **Sample:** 200 curves × 25 targets per family and size.
- **Seed:** **20261023**, held out. It is new: neither the selection round nor
  any earlier run used it.
- **Arms:** both arms solve every target. `main` also runs the negation-map
  rho reference (`--rho`).
- **Execution:** four processes on one 4-core host (arm × family), then `gzip`.

## Analysis (`analyze.py`, frozen with this file)

### Invariants

`analyze.py` stops, writing nothing, if any of these fail:

- **Correctness:** every answer is correct, in both arms and in the rho
  reference.
- **Grid:** both arms have identical grids, curves and targets, with no
  duplicate rows.
- **Identity control:** wherever c = 12 and c = 48 pick the same table, the two
  arms give identical `group_ops`. That covers all of 26 and 36–40 bits, and
  part of the other sizes.

### Primary test

- **Statistic:** per family, the geometric mean of the four cell ratios at
  28, 30, 32 and 34 bits. Each cell ratio is the sum over curves of c12
  operations divided by the sum over curves of main operations, paired on the
  same targets.
- **Interval:** bootstrap over curves within each cell, 10,000 draws, at the
  97.5% level (Bonferroni over the 2 families).
- **Verdict:** **confirmed** if the upper bound is below 1, otherwise not
  confirmed.

### Descriptive

- **Per cell:** the c12 / main ratio with 99.69% intervals (Bonferroni over 16).
- **Rho reference:** main / rho and c12 / rho for every cell.

## Decision rule

- **If both families are confirmed:** this PR proposes the change for merge as
  an operation-count improvement at 28–34 bits, with the held-out numbers as
  its evidence.
- **If either family is not confirmed:** the PR reports that, and the change
  is not proposed as an improvement.

## Limits

- **Measure:** operation counts, not wall time.
- **Sizes:** 26–40 bits only.
- **Dry run (disclosed):** before freezing, the scripts were exercised on
  seed 2, at 28–34 bits, with 3 curves × 2 targets. Those rows are not part of
  this experiment.
