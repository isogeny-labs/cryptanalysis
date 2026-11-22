---
title: "n = 83: field-ops-2 (R1) on the D4 base, stacking the two merged changes (Tier 1 design)"
date: 2026-11-08
---

# n = 83: field-ops-2 (R1) against field-ops, both on the D4 base

**Status (2026-11-08): result in. Verdict: improvement; every gate and control passes and the run is valid** `[pcc:unverified]`.
R = E2E(field-ops) / E2E(R1), both on D4, = **1.0504 [1.0467, 1.0541]** over 36 alternating pairs, run
[42450569196](https://github.com/isogeny-labs/cryptanalysis/actions/runs/42450569196), Tier 1, instance scope. The design
sections below are the frozen text (commit `bca22e9f9`, before any timing on the Tier 1 runner); the result section is added
with the archived receipt.

## Result

Run [42450569196](https://github.com/isogeny-labs/cryptanalysis/actions/runs/42450569196) (workflow `n83-fo2d4.yml`, push trigger,
head `bca22e9f9`, attempt 1, conclusion success) on one GitHub-hosted `ubuntu-24.04` runner (`GitHub Actions 1000203805`,
**Intel Xeon Platinum 8573C**, execution CPU 0; the k4c400 run was on a Xeon Platinum 8370C). All 278 scheduled rows ran and are
valid, none was skipped by the time guard. The receipt is in [`run_github_42450569196/`](run_github_42450569196/) (`panel/runs.jsonl`,
1.4 MB, in the artifact store).

**Verdict: improvement** `[pcc:unverified]`: R = sum E2E(A) / sum E2E(B) = **1.0504 [1.0467, 1.0541]** over 36 alternating pairs
(12 points x 3 pairs; two-stage paired bootstrap, 10,000 draws), A = field-ops producer `ic_online_fieldops_r770`, B = R1
`ic_online_fieldops2_r770`, both on D4. Every gate passes (`verify-stdout.json`): one scalar, relation, probe count and index and
layout digest set per point across both binaries, equal to D4's frozen identity; Q0 equal for both binaries; identical rank
relations, probe vectors, root calls and counters per seed across kD4FO, kD4R1 and kD4R1aa; rank tables equal to the frozen table;
pipelines and binaries as the arms name them; placement and host identity unchanged. `verify_receipt.py` and `band_model.py`
re-run on a full copy of the receipt directory reproduce `panel/result.json`, `panel/result_table.md` and `band/band_model.json`
byte for byte.

![Frozen ratios with 95% bootstrap intervals, from result.json (`figures/make_result_figure.py`, [SVG](figures/result.svg)).](figures/result.svg)

| stage (A = field-ops, B = R1, both D4) | side A mean (ms) | side B mean (ms) | A / B [95%] |
| --- | ---: | ---: | --- |
| index build (cold process) | 2,107 | 1,961 | 1.0745 [1.0721, 1.0772] |
| scan self-test | 209 | 208 | 1.0027 [0.9947, 1.0108] |
| rank stage (rank process) | 1,878 | 1,787 | 1.0505 [1.0461, 1.0550] |
| online, one target | 695 | 679 | 1.0232 [1.0091, 1.0314] |
| cold process | 3,404 | 3,241 | 1.0503 [1.0460, 1.0544] |
| **end to end (rank + cold)** | 5,281 | 5,028 | **1.0504 [1.0467, 1.0541]** |

The stage rows are stage secondaries and never decide. The index build carries most of the saving (7.5%), the rank stage 5.1%;
the self-test, which runs no field products, is unchanged, as in the field-ops-2 run. Process CPU time A / B 1.0430
[1.0403, 1.0463]; peak RSS equal (0.99997).

- **A/A** (B against Baa, 24 pairs): end to end 0.9995 [0.9969, 1.0019], cold 0.9987 [0.9958, 1.0015] (both inside [0.97, 1.03]).
- **Planted:** cD4R1X / cD4R1 index build 3.0054 [2.9892, 3.0195] (lower bound above 1), layout digests unchanged.
- **Probe law** (estimate, band [0.80, 1.20], 144 attempts each): kD4FO 0.9916 [0.7738, 1.2394], kD4R1 0.9916 (the same
  work on both binaries, as gated).
- **Order and spread:** A first 1.0527, B first 1.0492; pair positions 1.0504, 1.0486, 1.0521; per-point ratios 1.037 to 1.060
  (12 of 12 above 1). Geometric mean of the per-pair ratios 1.0506 [1.0469, 1.0541].
- **Against the power check:** the design had power 0.998 at a true 1.010 and the estimate is 1.050, far above the minimum
  effect. Observed per-side E2E CV 0.209 (A) and 0.210 (B): large, but the two sides do identical work per pair, so the ratio's
  noise is small (A/A pair noise in `analysis/power.json`).

Expected effect was about 2-3% `[pcc:unverified]`; the measured 5.0% is larger than that expectation and than R1's 2.56% on the M38
base: on D4 the index build (7.5% faster here against 5.0% on M38) is a larger share and the rank stage gains 5.1% against 0.6%
there. Ratios from different runs do not compose, so this is its own measurement, on another runner CPU class.

### Distance to rho

In this run's matched rT770 rho (12 processes, mean cold 2,461.5 ms, step 254.81 ns) the end-to-end cold gap is **2.1455 for side A
(field-ops on D4) and 2.0426 for side B (R1 on D4)** (point estimates, no interval computed for the gaps); S end to end cold is 0.2239
for A and **0.2132 for B** in rT770 steps `[pcc:unverified]`. The k4c400 run read 2.0485 for the field-ops producer on D4 on another
runner (rT770 step 275.68 ns); gaps do not compose across runs (the matched rho's cold mean is a mean of random-length processes and
moves with panel and host). Wall time, one host class, factor-base construction charged to neither side, so cold S is a lower bound.

### Section 5a (priced native work; a model band, not a counted band)

`band_model.py` (frozen) models the IC units from the archived counted run 39882571652; neither producer here emits operation
counts, so this run has no counted band and none was run, in CI or locally. Both sides do identical group-operation work (gated), so
the model gives A and B the same units and cannot see a field-arithmetic change: at 0, 0.1 and 1 GAE per unpriced native operation
the gap to rT is 9.844e-05, 0.7217 [0.4782, 1.177], 2.875 [1.905, 4.69] for both sides; the order against rho is unresolved (it changes
by w = 1). Per the coordinator's note on PR #1448 (opcounts2, merged; not re-checked here) `[pcc:unverified]`, this model under-states
the unpriced IC operations by about 1.4x, so the in-band gaps above are probably low. A counted band needs the counted producer of
#1448 run on this design; not done.

### Limits of this result

- Wall time on one GitHub-hosted runner (Intel Xeon Platinum 8573C), one pinned CPU, Tier 1 instance scope, no host-wide exclusivity;
  not replayed on another host class (the k4c400 run was on an 8370C, field-ops and field-ops-2 on an AMD EPYC 9V74).
- 36 pairs on 12 points; the narrowed panel scan is disclosed above.
- Factor-base construction is charged to neither side, as in every n = 83 row.

## Files (result)

`run_github_42450569196/` (receipt, `band/`), `figures/make_result_figure.py`, `figures/result.svg`, `figures/result.png`,
`figures/make_report_pdf.py`, this report as `README.pdf`.


## Question

The headline row is the field-ops producer (`ic_online_fieldops_r770`) on the D4 closure base (K' = 4, 400 orbits;
`koblitz-n83-k4c400-20261107`). The field-ops-2 producer R1 (`ic_online_fieldops2_r770`, a constant reduce shift at
n = 83; `koblitz-n83-fieldops2-20261107`) was measured only on the M38 base (1.0256 [1.0236, 1.0278]) `[pcc:unverified]`.
**Is the end-to-end cold cost of R1 on D4 lower than that of the field-ops producer on D4?** Both sides run the same
header, table, points and rank seeds; only the binary differs. Ratios from different runs do not compose, and D4 shifts
the stage mix, so the stacked effect is measured. Expected effect: about 2-3% `[pcc:unverified]` (an expectation).

## Design (frozen before any timing)

- **Sides:** A = `kD4FO` + `cD4FO` (field-ops binary, built from the field-ops-2 experiment's `online/` crate); B = `kD4R1` +
  `cD4R1` (R1, its `online-b/` crate); A/A = B against `kD4R1aa` + `cD4R1aa`; planted = `cD4R1` against `cD4R1X`
  (`lift_plant`, index build); matched rho `rT`. `+pclmulqdq` on both, one toolchain (1.99.0 in CI).
- **Panel:** 12 new held-out points (`inputs/cold_targets.json`, role `fo2d4-cold-v1`), disjoint from every earlier n = 83
  panel including k4c400's (`inputs/panel_disjointness.json`, 0 hits; narrowed scan: origin/main in full and the 92 origin
  branches whose name contains `n83`, as in k4c400, disclosed).
- **Rank seeds:** 2601-2636, new on n = 83 (`inputs/seed_disjointness.json`), outside 2201-2236, 2301-2360 and 2501-2560.
- **Pairs per point:** 3 alternating primary pairs (same point and rank seed, seeded ABAB/BABA), 2 A/A pairs, 1 planted
  pair, 1 rho process; 278 runs, about 24 minutes modelled.
- **Primary:** R = sum E2E(A) / sum E2E(B) over 36 pairs, E2E = rank stage + cold process; improvement iff the 95% two-stage
  paired bootstrap lower bound exceeds 1 (10,000 draws).
- **Primary choice (frozen before data): end to end, not cold only.** The noise of one A/B pair comes from the k4c400 A/A
  pairs (identical work): sd 0.0103 in log for E2E, 0.0121 for cold, so E2E is no noisier. At 12 x 3 pairs E2E resolves a 1.010
  effect with power 0.998 and 1.005 with 0.67 (cold only 0.997 and 0.56; `analysis/power.json`). A cold-only schedule would
  save about 12 minutes and would measure another quantity (R1 also touches the rank stage). Cold is a secondary.
- **Gates and controls** are the k4c400 verifier's, with both sides on one base: one relation, probe count, scalar and
  index/layout digest set across BOTH binaries; rank work identical per seed across `kD4FO`, `kD4R1`, `kD4R1aa`; probe law in
  [0.80, 1.20] over at least 64 attempts for each binary; A/A end-to-end and cold point estimates inside [0.97, 1.03]; planted
  index-build lower bound above 1. An unknown gate fails.

## Local checks (diagnostics, not timing evidence)

Both binaries reproduce D4's frozen identity (counts, index and layout digests, Q0 relation/probes/scalar, table digest) in 8
processes, with identical rank work across the binaries (`inputs/local_identity.json`, all checks pass). A smoke run of segments
O1 and P1 through `run_schedule.py` and `arm.py` (10 rows, one per arm) was valid; it is not kept.

## Files

`restore.py`, `make_log_table.py`, `check_log_table.py`, `local_identity.py`, `make_targets.py`, `check_panel_disjoint.py`,
`check_seed_disjoint.py`, `make_power_prior.py`, `power_check.py`, `make_protocol.py`, `make_schedule.py`, `run_schedule.py`,
`arm.py`, `verify_receipt.py`, `test_verify_receipt.py`, `band_model.py`; `protocol.json`, `schedule.json`; `inputs/`,
`analysis/power.json`. Trigger: `.github/workflows/n83-fo2d4.yml`, on a push to `claude/n83-fo2d4`.
