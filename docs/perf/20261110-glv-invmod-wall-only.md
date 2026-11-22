# GLV j=0 walk and `ca_invmod`: WALL-only kernel fixes (C2, C1, C15, C3)

Date: 2026-11-10. Branch `claude/nice-babbage-bn0fn0`, base `188cd051`.
Source: `crypto:docs/assessment-speed-productionization-20261110.md` §3b,
items C1, C2, C3 and C15. Every number below is a local, unisolated
measurement on a 4-vCPU cloud VM (Intel Xeon @ 2.30 GHz, no PMU, gcc 13.3,
Release), labelled **[pcc:unverified]**. No pcc claim, benchmark record or
leaderboard row is made here. A speed claim still needs AGENTS.md §10:
a recorded isolated host, an A/A arm, ABAB ≥ 5 and a `benchrec` record.

## Commits

| Item | Commit | Change |
|---|---|---|
| C2 | `d971e30c` | `% c.r` → `& (c.r - 1)` at the three GLV walk index reductions. `c.r` has one assignment (`rr` starts at 8 and only doubles, up to 32 or 128), so it is always a power of two. An unreachable guard returns `CA_ERR_INTERNAL` otherwise. |
| C1 | `a2ef46bf` | The factored j=0 reducer is now the default (`CA_RHO_J0_FACTORED_HASH` ON; OFF selects the legacy loop through `CA_RHO_J0_LEGACY_HASH`). It uses one field multiplication: `x2 = -(x0 + x1) mod p`, from `1 + β + β² = 0`. `glv_class_reduce` returns the chosen hash, so the second `ca_group_hash` at the walk sites is gone. |
| C15 | `58b2791b` | The coefficient update `a·λ^k mod n` uses Shoup products, with `ca_shoup_pre(λ^k, n)` computed once per solve, when `n < 2^63`. Otherwise it keeps `ca_mulmod`. The helpers are `ca_shoup_ok/pre/mul` in `src/ca_internal.h`. `src/linalg.c` keeps its own identical copy for now (see the note there). |
| C3 | `3f7dbe07` | `ca_invmod`: odd moduli use a division-free binary xgcd (Kaliski almost-inverse, ctz-batched, branchless selection, 64-bit words, exact 2^-k correction). Even moduli keep the Euclid. `-DCA_GLV_FIELD_COUNT` builds keep the Euclid for every modulus, so `CA_FC_EUCLID` still counts Euclid division steps. |

## Identity gate (all must be identical to the `188cd051` baseline build)

| Check | C2 | C1 | C15 | C3 |
|---|---|---|---|---|
| `ctest -j4` (19 tests) | pass | pass | pass | pass |
| `ca_perfbench` fingerprints, 31 kernels, vs scratch `perfbench.jsonl` | identical | identical | identical | identical |
| `ca_bench generic --bits 24,28,32,36 --reps 3 --threads 1 --group both --json`: 120 instance rows (all fields except `seconds`) | identical | identical | identical | identical |
| `ca_bench glv` table (13 curves × 20 solves) | identical | identical | identical | identical |
| Scratch `glvfp`: 960 `ca_curve_solve` calls (all curves × 20, plus 300 on glv-j0-32, 100 on glv-j1728-32 and 300 on glv-j0-26); `rc`, `got`, `group_ops`, `iterations`, `table_entries`, `collisions`, `bytes_peak` | identical | identical | identical | identical |
| Two j0-56 solves (p = 2^61 − 1; 79,039,352 and 99,687,810 group ops) | — | identical | identical | identical |
| `ca_rho_orbit_bench` legacy (`-DCA_RHO_J0_FACTORED_HASH=OFF`) vs factored: 32-seed glv-j0-32 panel and j0-56 seed 1 (scalar 14684984045970115, 79,576,759 group ops, replay verified) | — | identical | — | — |

Release `-DCA_SANITIZE=ON` (address, undefined) at the C3 state: ctest 19/19.
The perfbench `glv_rho_j0_32`, `invmod` and `ec_add_chain` fingerprints are
unchanged under the sanitizers. Compile-only with `-DCA_WERROR=ON` passed for
`CA_GLV_BATCH_ESCAPE`, `CA_GLV_FIELD_COUNT`, `CA_RHO_J0_COORDINATE_ORBIT`,
`CA_J0_RHO_COORD_CANON`, `CA_GLV_CYCLE_ESCAPE=OFF` and
`CA_GLV_LOOKAHEAD_LEGACY`. Walk equality was not run in those non-default
configurations.

C3 value equality: a scratch program compared the library `ca_invmod` with a
copy of the old routine on **150,200,012 (a, m) pairs**, with **0
mismatches**. The pairs were:

- 34 edge values, paired every way including ±1: 0, 1, 2, 3, 2^32 ± 1,
  2^61 − 1, 2^63 ± 1, 2^64 − 59, 2^64 − 2 and 2^64 − 1.
- Every `a ≤ 2m + 1` for `m < 2048`.
- 2M random pairs per bit length 2–64, with odd and even `m` and reduced,
  unreduced, multiple-of-small-factor and near-`m` values of `a`.
- 2M pairs for each of 10 moduli the library uses.

Another 5.66M pairs ran under ASan and UBSan. `tests/test_modarith.c` now
keeps the old routine as `invmod_reference` and checks about 330k pairs
against it.

## Instruction counts (callgrind, `ca_perfbench run --filter K --exact --instr`)

| Kernel | base | C2 | C1 | C15 | C3 |
|---|---:|---:|---:|---:|---:|
| `dlp/c_glv_rho_j0_32` | 120.26M | 119.98M | 89.27M | 86.38M | 105.02M |
| `dlp/c_rho_ec36` | 268.42M | 268.42M | 268.42M | 268.42M | 298.41M |
| `field_ec/c_invmod` | 110.95M | 110.95M | 110.95M | 110.95M | 267.22M |
| `field_ec/c_ec_add_chain` | 74.95M | 74.95M | 74.95M | 74.95M | 164.75M |

Top 5 self-cost symbols in `glv_rho_j0_32`:

- **base:** `ec_hash` 19.9 %, `ec_batch_op` 16.7 %, `ca_ec_endo` 14.7 %,
  `glv_rho_solve` 14.4 %, `glv_class_reduce` 11.6 %.
- **After C1:** `glv_class_reduce` 24.8 %, `ec_batch_op` 22.5 %,
  `glv_rho_solve` 19.1 %, `ca_invmod` 14.9 %, `ec_jac_dbl` 4.9 %. `ec_hash`
  and `ca_ec_endo` leave the hot path.
- **After C3:** `ca_invmod` 30.4 %, `glv_class_reduce` 21.0 %, `ec_batch_op`
  19.2 %, `glv_rho_solve` 16.3 %, `ec_jac_dbl` 4.1 %.

For `rho_ec36`, `rho_thread_main` is 77 % before C3 and 70 % after, and
`ca_invmod` goes from 8.0 % to 17.2 %. For `c_invmod` and `ec_add_chain`,
`ca_invmod` is 98 % / 83 % before C3 and 99 % / 92 % after.

**C3 raises Ir while lowering wall time.** Callgrind counts a 64-bit `div` as
one instruction, and the binary xgcd runs about 2.4× as many instructions,
each of them cheap. Ir is not the measure for C3. Use the wall table.

## Wall time: local ABAB × 5, min and median of per-round medians (5 samples each)

All rows are **local, unisolated, [pcc:unverified]**. Each row compares a
commit with its predecessor, except "all", which compares base with C3.

| Step | Kernel | min A → B (ms) | ratio | median A → B (ms) | ratio |
|---|---|---|---:|---|---:|
| C2 | glv_rho_j0_32 | 15.93 → 15.99 | 1.004 | 16.45 → 16.48 | 1.001 |
| C1 | glv_rho_j0_32 | 16.44 → 10.84 | 0.659 | 16.66 → 11.17 | 0.670 |
| C15 | glv_rho_j0_32 | 10.89 → 10.44 | 0.958 | 11.22 → 11.00 | 0.980 |
| C3 | glv_rho_j0_32 | 10.69 → 9.43 | 0.882 | 11.07 → 9.98 | 0.901 |
| C3 | invmod | 27.52 → 17.18 | 0.624 | 28.55 → 18.02 | 0.631 |
| C3 | ec_add_chain | 17.31 → 11.56 | 0.668 | 17.88 → 12.28 | 0.687 |
| C3 | rho_ec36 | 27.03 → 26.19 | 0.969 | 28.52 → 28.12 | 0.986 |
| all | glv_rho_j0_32 | 16.16 → 9.38 | 0.581 | 16.62 → 9.88 | 0.594 |
| all | rho_ec36 | 27.76 → 25.21 | 0.908 | 28.76 → 26.55 | 0.923 |
| all | invmod | 26.93 → 17.36 | 0.645 | 28.34 → 17.71 | 0.625 |
| all | ec_add_chain | 17.49 → 11.93 | 0.682 | 17.67 → 12.18 | 0.690 |

Two runs measure the noise floor on this host. Neither changed the `rho_ec36`
code, and Ir is identical in both:

- C15 step: `rho_ec36` median 29.01 → 31.55 ms (1.088).
- C1 step: `rho_ec36` median 31.45 → 28.56 ms (0.908).

So differences under about 10 % in medians are not resolved here. The C2
result (no measurable change) and the C15 result (−2 % median) are within that
noise.

The j0-56 single solves agree in direction with these results but are too
noisy to quote on their own:

- C1: online time from 10.07 s to 5.24 s (`ca_rho_orbit_bench`).
- C3: inconclusive at 56 bits. Alternating runs gave 4.89/4.62/4.93/4.88 s and
  6.10/6.06/6.18/6.58 s. Batched inversion makes the inversion share small.

## Rejected attempts

C3 microbenchmark (latency-bound chain of 2^20 inversions; B and C at -O2, D, E and legacy at -O3, legacy differs by under 3 % between the two; ns per call
on moduli of 61, 62, 41, 64 and 33 bits). The legacy routine measured
208/191/130/197/106.

| Candidate | ns | Verdict |
|---|---|---|
| B: branchy Kaliski with ctz batching | 210/202/138/212/113 | Rejected: no faster than legacy, because of branch mispredictions. |
| C: branchless, swap first, then subtract | 175/180/124/193/101 | Rejected: 1.0–1.2×. The swap mask sits on the critical path. |
| D: abs via xor-mask, coefficients off the critical path | 128/130/91/134/75 | Superseded by E. |
| E (landed): `|u − v|` and `min` via cmov, ctz of `u − v` | 113/116/80/119/67 | 1.6–1.8×. |

Not attempted:

- Lehmer, or Bernstein–Yang safegcd with 62-divstep matrices. Larger code and
  risk for a ~100 ns routine whose remaining callers mostly batch their
  inversions.
- Moving `linalg.c`'s `shoup_*` onto the shared helpers, because another agent
  is editing that file.

## Decisions

- **`CA_FC_EUCLID`.** The legacy path stays behind the existing
  `CA_GLV_FIELD_COUNT` flag, so the counter is not redefined.
  `experiments/glv-batch-escape-20261024/run.py` prices "one Euclid division
  step = d multiplications", and its counts stay reproducible. Diagnostic
  builds therefore run the Euclid; the values are identical.
- **Field counts after C1.** `CA_FC_MUL` in GLV diagnostic builds drops by
  design: one multiplication per j=0 reduction instead of five. This is a
  change to the diagnostic field-operation counts, not to the group-operation
  counts.
- **Reducer precedence.** `CA_RHO_J0_COORDINATE_ORBIT` and
  `CA_J0_RHO_COORD_CANON` now take precedence over the default factored
  reducer. Previously, setting both `FACTORED` and `COORD_CANON` picked
  factored. The configure-time "at most one" error is removed.
- **Existing build trees.** A build tree keeps a cached
  `CA_RHO_J0_FACTORED_HASH=OFF`, and therefore the legacy reducer, until it is
  reconfigured.
- **`make_rho_orbit_manifest.py`.** It still works if the reference build
  passes `-DCA_RHO_J0_FACTORED_HASH=OFF` explicitly, which it already checks
  for.
