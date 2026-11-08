---
title: "n = 83: field-ops-2 (R1) on the D4 base, stacking the two merged changes (Tier 1 design)"
date: 2026-11-08
---

# n = 83: field-ops-2 (R1) against field-ops, both on the D4 base

**Status (2026-11-08): design frozen, run pending.** The result section is added with the archived receipt.

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
