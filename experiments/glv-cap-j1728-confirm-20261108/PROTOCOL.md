# Protocol: held-out test of a j = 1728-only 128-entry GLV table cap (from 40 bits)

**Frozen before any data on the seed below exists.** This round tests one hypothesis about one code change; it does
not search. No parameter changes after the first row exists. Observation, interpretation and hypothesis are kept apart in
the report. Operation counts only: no wall time (needs a Tier 1 run).

## What changed since the task was set, and what that does to the question

The task was written while PR #1341 (cap 128 from 40 bits for both families) was held. **#1341 has since been merged**
(2026-11-01, merge `6ad8b68d`), so current main (`318b27bf`) already has `rcap = lg >= 40 ? 128 : 32` for both families.
The candidate (`rcap = (c.m == 4 && lg >= 40) ? 128 : 32`, below) therefore differs from **current main** only on j = 0 at 40
bits and above (back to cap 32), and its j = 1728 path is exactly current main's. Three consequences, all fixed here:

1. The reference for the j = 1728 question is the **pre-#1341 rule** (cap 32 at every size), built unpatched from
   commit `1ee4f47` (#1340's "main"). The registered primary asks whether cap 128 helps j = 1728 against that rule, on fresh data.
   Because the candidate's j = 1728 path equals current main's, this is also a fresh-seed replication of #1340's j = 1728 half.
2. **Against current main the candidate changes only j = 0.** Whether that is an improvement is the secondary S2 below
   (j = 0, candidate over current main). Stated now so it is not discovered later: if S2 is neutral, the candidate is not an
   operation-count improvement over what is merged, and relabelling it as one would not be honest.
3. Identity checks are exact and cheap, and they also prove that nothing else between `1ee4f47` and `318b27bf` changed
   `curve_solve` operation counts.

## Candidate and builds (all `cmake -DCMAKE_BUILD_TYPE=Release -DCA_CUPQC=OFF`, target `cryptanalysis`)

| arm | source | cap used by `glv_rho_solve` |
|---|---|---|
| `ref` | commit `1ee4f47` unpatched (main before #1341) | 32 everywhere |
| `main` | commit `318b27bf` unpatched (current main) | 128 from 40 bits, both families |
| `cand` | branch `glv-table-cap-j1728`, commit `461f34d0` (main `318b27bf` plus the selector line and its comment in `src/curve.c`) | 128 from 40 bits when `c.m == 4` (j = 1728, `aut_order` 4); 32 otherwise (j = 0 has `aut_order` 6) |
| `r8` | `1ee4f47` plus `force-r.patch`, `-DCA_GLV_FORCE_R=8` | positive control only |

T = 40 bits. Reason, from the pre-freeze look below: on j = 1728 a 128 table was not better at 38 and 39 bits (#1339 r128 over
main 1.009 and 1.022) and was better at 40-43 bits (0.964, 0.987, 0.967 in #1339; 0.967, 0.988, 0.970, 0.948 in #1340),
which is where #1341 already put it. No other T was considered or is tested.

## Looks at data before the freeze (disclosed; exploratory, not the confirmation)

1. The #1339 (seed 20261105) and #1340 (seed 20261106) per-row data were re-read by `explore_prefreeze.py`, output
   `explore_prefreeze.txt`: j = 1728 r64 / r128 / candidate over main per size, and the per-target variance of log(arm/main)
   (0.48-0.56). They fixed T, the size range and the power calculation. None of those curves are reused (seed differs; the
   sampler seeds on the seed string).
2. Dry run: seed 7, 3 curves per cell, all four builds, `run_all.sh` and `analyze.py` end to end (noise only; one build
   check shows the invariants pass and the identity cells are exact). No rows kept in this experiment.
3. Nothing of seed 20261108 has been generated.

## Hypotheses (one-sided, stated before the data)

> **H1 (primary, confirmation).** On j = 1728 at 40, 41, 42 and 43 bits, the geometric mean over the four sizes of
> group_ops(`cand`) / group_ops(`ref`), each size's ratio being the ratio of sums over its curves, is below 1.

Null: the ratio is 1 or above. **Confirmation rule:** the upper bound of the 97.5% two-sided percentile bootstrap interval
(10,000 draws over curves, within each size independently) is below 1. (K = 2: the owner's brief splits alpha = 0.05 over two
comparisons, this one and the pooled test of #1340 on the same code line; 97.5% two-sided.) A point estimate below 1 whose
interval contains 1 is not a confirmation.

**No-worse check:** per size, a Bonferroni interval over the 4 sizes (98.75% two-sided) of cand/ref; **fails if any size's
interval is wholly above 1** (lower bound > 1). It does not require every size to be below 1.

## Secondary (registered, labelled secondary; no decision rests on them)

- **S1.** j = 1728 per size, cand/ref, 98.75% Bonferroni intervals (the no-worse intervals), and which sizes are wholly below 1.
- **S2.** j = 0 at 40-43 bits: `cand` (cap 32) over current `main` (cap 128), 800 curves per size, pooled geometric mean at
  97.5% and per size at 98.75%. Read as an estimate of what going back to cap 32 on j = 0 does to current main. It is called
  an improvement over main only if the pooled upper bound is below 1; if the interval contains 1 it is neutral; if the lower
  bound is above 1 it is a regression.
- **Descriptive** (no decision): per-cell mean S = group_ops / sqrt(n / m) (GLV) and group_ops / sqrt(n) (rho); the negation-map
  rho on the first 60 j = 1728 curves of every primary cell on `ref`'s targets and the first 40 j = 0 curves of every S2 cell on
  `main`'s targets; cand/rho and ref/rho on those curves (distance remaining to matched rho, raw group operations, **not
  priced**; AGENTS.md section 5a pricing of native work at 0, 0.1 and 1 GAE is not applied, so no ranking of methods is made).

## Design

- Families: j = 1728 `y^2 = x^3 + a x` (p = 1 mod 4), j = 0 `y^2 = x^3 + b` (p = 1 mod 3); `sample_curve` of `run.py` (same as
  #1340): largest prime factor r of #E with exactly `bits` bits, cofactor <= 16.
- **Seed 20261108**, never used. Curves from `"20261108:<family>:<bits>"`, targets from `"20261108:<p>:<a>:<b>:0"`, solver
  seed 1, one target per curve; independent walks; every arm solves the same curve and target.
- **Primary cells:** j = 1728 at 40, 41, 42, 43 bits, **3000 curves per size** (12,000 targets per arm), arms `ref`, `cand`.
- **S2 cells:** j = 0 at 40-43 bits, 800 curves per size, arms `cand`, `main`.
- **Identity cells (exact checks, not padding):** (a) `cand` vs `ref` on j = 0 at 40, 41, 42, 43 bits and j = 1728 at 38 and 39 bits,
  100 curves per size: the candidate's j = 0 path is the old rule and its j = 1728 path below T is the old rule, so every row
  must match exactly (ratio 1); (b) `cand` vs `main` on the first 100 curves of every j = 1728 primary cell: same code path, every
  row must match exactly.
- **Positive control:** forced r = 8 (`r8`) against `ref` on j = 1728 at 42 bits, curves 0-199 of the primary cell; the
  detector passes if the lower bound of its 95% interval is above 1 (#1339 saw 1.20 [1.01, 1.41] on 100 curves).
- All answers must verify in every arm; `analyze.py` stops, writing nothing, if any invariant fails: correctness, the frozen
  grids and identical curves across arms, the recomputed table size (ref 32 everywhere; cand 128 for j = 1728 at 40-43 and
  32 for j = 0; main 128 for j = 0 at 40-43), both identity checks, the rho coverage.
- Commands: `run_all.sh p1` and `run_all.sh p2` concurrently under `nice -n 10` (two heavy processes), `gzip rows_*.jsonl`,
  `analyze.py`, `chart.py`. `GRID_N=3000 J0_N=800 IDENT_N=100 RHO_N=60 CTRL_N=200` are the defaults.

## Power calculation (`power.py`, normal approximation, before the data)

Per-target variance of log(arm/ref) 0.53 (0.48-0.56 across #1339 and #1340 j = 1728 cells; the brief's 0.42 is lower than
what these cells show). With n curves in each of the four sizes the pooled standard error is sqrt(0.53 / 4n) and the 97.5%
half-width 2.24 SE:

| curves per size | pooled SE | half-width | P(confirmed) at true pooled ratio 0.968 / 0.975 / 0.98 / 0.985 / 0.99 / 1.00 |
|---|---|---|---|
| 1600 | 0.0091 | 2.04% | 0.91 / 0.71 / 0.49 / 0.28 / 0.13 / 0.01 |
| 3000 (chosen) | 0.0066 | 1.49% | 1.00 / 0.94 / 0.79 / 0.51 / 0.23 / 0.01 |
| 3600 | 0.0061 | 1.36% | 1.00 / 0.97 / 0.86 / 0.60 / 0.28 / 0.01 |

3000 per size gives the requested half-width of about 1.5%. #1340's j = 1728 pooled point was 0.968 but it was selected by
the earlier rounds, whose realized effects shrank on re-test, so the plan assumes 0.98 (P about 0.8). **An effect below about
1.5% cannot be confirmed here.** Per size the Bonferroni half-width is 3.3%, so the per-size intervals only rule out a size
being worse by more than about 3%. S2 (800 curves per size) has a pooled half-width of 2.9%: it cannot see a j = 0 difference
smaller than that. Cost: about 1.6 CPU-hours for the primary, about 0.5 for S2 and the checks (total under 3).

## What each outcome means

- **H1 confirmed and no-worse passes:** a 128 table is a measured group-operation improvement for j = 1728 from 40 bits,
  over the pre-#1341 rule, on held-out curves. It says nothing about wall time (Tier 1) or about sizes outside 40-43.
- **Confirmed but some size wholly worse:** the size is named and the threshold is not recommended as it stands.
- **Not confirmed:** said plainly with the interval; the code PR is not recommended; no other threshold is searched here.
- **S2** decides what the candidate is against current main: improvement, neutral (only a smaller j = 0 table), or regression.
