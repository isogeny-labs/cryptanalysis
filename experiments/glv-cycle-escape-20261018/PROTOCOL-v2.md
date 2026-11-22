# Protocol v2: does fixing the GLV walk's fruitless cycles recover the automorphism gain?

Frozen 2026-10-18, before the main run of version 2. Version 1 (`PROTOCOL.md`)
and its result (`REPORT.md`) are unchanged. `DIAGNOSIS.md` traced the
shortfall to fruitless cycles and setup cost.

## 1. Question and what each outcome licenses

On current aburan28/cryptanalysis `main` (`3ce4c29ec497`), do two
changes to `glv_rho_solve` reduce `curve_solve`'s group operations on
j = 1728 and j = 0 curves, against the unchanged walk, on the same curves,
targets and seeds?

- **look-ahead:** the look-ahead also rejects a candidate whose next point would select Y's own natural multiplier. That is the default in `v2-curve.patch`.
- **escape:** the look-ahead change, plus a deterministic escape from 2- and 4-cycles (`-DCA_GLV_CYCLE_ESCAPE`). When the new point equals the one 2 or 4 committed steps back, the walk doubles the cycle member with the smallest hash.

For each (variant, family):
- CI entirely below 1: "fewer operations than the legacy walk", by the stated factor.
- CI containing 1: "no measured difference".
- CI entirely above 1: "more operations".

Ratios against the library's negation-map rho, and against theory, are reported descriptively.

Claim class: comparative, about this implementation's operation counts. It
is not a time measurement and not an ECDLP-hardness statement.

## 2. Arms and instrument

- **Library:** `main` `3ce4c29ec497` with `v2-curve.patch` (sha256 `a4193d2891ba2103a73dc46ca6a885283ef07a2d45410d752599a5eec140e10e`), built Release with `CA_CUPQC=OFF`, in three variants:
  - legacy: `-DCA_GLV_LOOKAHEAD_LEGACY`. This is identical to `main` on 80 checked solves.
  - look-ahead: default flags.
  - escape: `-DCA_GLV_CYCLE_ESCAPE`.
- **Instrument:** `run.py` unchanged from v1. It runs the negation-map `rho` and `curve_solve` on the same target and seed, against each library in its own process, with the binding from the same source tree.
- **Families:** j = 1728 (target), j = 0 (second target; on `main` it uses the same generic walk), and random curves.
  - Random curves are the negative control: `curve_solve` does not reach `glv_rho_solve` there, so every variant must give exactly the legacy counts.
  - The rho arm must be identical across the three runs, because rho code is not touched.
- **Positive control:** the dry run showed the escape variant changing counts on GLV curves. v1 established that the paired measurement detects GLV-sized effects.
- **Sizes and sample:** r = 24, 28 and 32 bits; 40 curves per family and size; 200 targets per curve; seed 20261017. These are the same curves and targets as v1's design.

## 3. Metric and decision rule

- **Per curve:** log( mean S of the variant's `curve_solve` / mean S of the legacy `curve_solve` ), over the same 200 targets. Family statistic: the mean over its 120 curves.
- **Intervals:** two-stage bootstrap (curves, then targets), 10,000 replicates, seed 20261017.
- **Multiple comparisons:** two variants × two GLV families = 4 tests. Bonferroni gives alpha = 0.05 / 4, so 98.75% intervals.
- **Descriptive only:** per-size rows, ratios against rho and theory, and trace shares.
- **Correctness:** every answer is checked against the planted logarithm. A wrong answer or a solver failure in any arm invalidates that arm.

## 4. Runtime estimate

v1's 72,000 paired solves took 309 s on the older revision. Three variants
of the same design, three processes in parallel on 4 shared cores, should
take about 15 to 25 minutes.

## 5. What does not count

Changing sizes, N, arms, the metric or the interval after seeing the v2
results. Further walk changes are a version 3.

## Dry-run disclosure

The dry run used 6 curves per GLV family at 28 bits, 30 targets each, with tracing.

| walk | j = 1728 vs rho | j = 0 vs rho | steps in cycles (j = 1728) | 2-cycles (j = 1728) |
|---|---|---|---|---|
| legacy | 0.800 | 0.504 | 22.0% | 546 |
| look-ahead | 0.777 | 0.544 | 20.3% | 249 |
| escape | 0.505 | 0.420 | 2.8% | 0 at abandonment (558 escaped) |

- **Design change from the dry run.** It showed the look-ahead change alone removes only about half the 2-cycles, which is why the escape arm was added before freezing.
- **The escape arm sits below theory.** Both families come in below the theory ratio against rho. The rho baseline has fruitless cycles of its own, so "against theory" stays descriptive.
