# C kernel correctness-and-speed pass (2026-10-18)

Class: **engineering** (identical counted operations, wall time only). No speedup claim beyond that label.
All timing ratios here are **exploratory, unisolated (no tier)**: cloud VM, no isolation, `taskset -c 1` only.
No number in docs/BENCHMARKS.md is changed. Working tree only; nothing committed.

## Question
Do the C library kernels (rho, kangaroo, bsgs, grumpy, precomp, modarith, group_*, pohlig, indexcalc, linalg, util) contain correctness bugs, and can they run faster with identical counted ops and results?

## Setup
- Base: origin/main `3ce4c29ec497ff3149eb841c07e9dd9f6631de77` (branch claude/c-kernel-pass-20261018); after = same + working-tree diff (see `git diff`).
- gcc 13.3.0 (Ubuntu 13.3.0-6ubuntu2~24.04.1), 4 vCPU, Intel Xeon @ 2.10GHz (VM), Release build (`make lib`), `make test`, `make asan`, `make tsan`.
- Before binaries were built from the clean tree and kept (`ca_bench_before`); the after binary is `build/ca_bench` of the edited tree.

## Commands
- `make -j$(nproc) lib && make test` before edits: 17/17 pass. `make asan`, `make tsan` before and after: 17/17 pass each (raw/asan_*.txt, raw/tsan_*.txt).
- Bench = the `make bench` commands, run one by one (all fast, ~5 s total): `ca_bench ops`; `generic --bits 24,28,32,36 --reps 3`; `interval --bits 24,28,32 --reps 3`; `precomp --bits 24,28,32,36 --reps 5`; `complexity --bits 20,24,28,32,36 --reps 5`; `glv`; `ic --bits 32,40,48`; `cheon --bits 32,40`; `gpu --bits 24,28,32`.
  Alternating: before r1,r2, after r1, before r3, after r2, before r4, after r3. Raw: raw/before, raw/after (`*_rN.txt`, `wall_rN.txt`).
- Micro (alternating, 9 pairs, pinned): raw/micro.
- Fuzz harnesses written for the audit (ASan/UBSan/TSan builds): raw/fuzz/*.c (modarith vs 128-bit reference, ~200k cases incl. p near 2^64 and a >= p; solvers vs brute force on small Z_p/EC subgroups; parameter fuzz; tau multiplication vs generic mul; IC on tiny p; rho with small r).

## Correctness findings (fixed, each with a regression test that fails on the old code and passes now)
1. `src/rho.c`, look-ahead rule (negation map): when all r multipliers are rejected the scan wrapped and looped forever (probability r^-r per point; with user r = 4 about 70% of runs on a 65k group hit max_ops). Now the r-th candidate is accepted (function of the point alone; the 2-cycle is handled by the window test). Cannot change any run that terminated before. Test: tests/test_rho.c (r = 4, 5, 30 seeds each; 21 of 60 failed before).
2. `src/rho.c`: base = identity with target != identity ran to max_ops (forever without). Now CA_ERR_NOT_FOUND. Test: tests/test_rho.c.
3. `src/kangaroo.c`: same hang for identity base, and for a target outside the order-n subgroup (added `ca_check_members`, uncounted, as rho does). Tests: tests/test_kangaroo.c.
4. `src/kangaroo.c`: `abandon = 32 << dp_bits` wrapped to 0 for dp_bits 59..62 (documented clamp is 62), restarting every kangaroo each hop. Saturated. Test: collisions == 0 for dp 59..62 (was 1134).
5. `src/indexcalc.c`: factor-base bound B >= p for tiny moduli (p <= 61 with default B = 60) put primes >= p in the base; solve failed with "only k of n factor-base logarithms verified". B clamped to p-1. Test: tests/test_indexcalc.c (13 primes, both methods; 14 failed before).
Not fixed / noted: a rho target outside <base> when base has a proper-subgroup order (composite n) still never terminates without max_ops (documented behaviour); `ca_ic_log` mutates the context (not thread-safe; Rust binding already marks it not Sync); src/curve.c GLV rho and gpu_emulate.c not audited (outside scope); ec_tau.c checked only by differential fuzz (tau2/tau4/tripling vs generic mul, edge scalars) and the existing tests, not read line by line.
Audited with no defect found: modarith (Montgomery incl. p near 2^64, a >= p via mont_to, inversion of 0 returns 0), htab, bsgs, grumpy, precomp, pohlig, linalg, group_ec/zp, DP-store locking in rho (TSan clean).

## Speed changes (counts identical by construction)
1. `src/bsgs.c` + `ca_htab1_prefetch` in `src/ca_internal.h`: hash a 64-lane block, prefetch its slots, then insert/look up in the original order (baby steps and giant steps).
2. `src/group_ec.c` `ec_batch_op`: field constants held in locals (stores to `r`/scratch are uint64_t and forced reloads of g->p / g->mont); same Montgomery reduction, same residues.
Tried and reverted (no gain measured): faster `ca_invmod` (64-bit coefficients; quotient-by-subtraction made it slower, ~175 -> ~230 ns), prefetch in grumpy (ratio 0.97 min / 0.99 med, within noise).

## Measurements (exploratory, unisolated (no tier))
Micro, alternating pairs, min / median wall of the whole process:
| workload | before | after | ratio min / med | ops before = after |
|---|---|---|---|---|
| BSGS Z_p 61-bit, width 2^42 (table 2^21 entries, 64 MB), 3 solves | 0.4774 / 0.6618 s | 0.3316 / 0.4617 s | 0.695 / 0.698 | 2181971 = 2181971, same x |
| ec_batch_op 256 lanes (inner best) | 20.33 ns/op | 13.80 ns/op (last pair); process wall ratio 0.937 / 0.965 | see raw/micro/ec_batch256_summary.txt | same checksum |
Callgrind instructions in ec_batch_op, 300 batches: 11,717,212 -> 11,145,300 (-4.9%), deterministic.
`make bench` rows (4 before runs, 3 after runs; min and median wall; counts column below):
| bench | before min/med s | after min/med s | ratio min / med | counts identical |
|---|---|---|---|---|
| ops | 0.951/1.136 | 1.061/1.135 | 1.12 / 1.00 | n/a (throughput only) |
| generic | 0.450/0.481 | 0.428/0.476 | 0.95 / 0.99 | yes: S of bsgs, rho-1, kangaroo, grumpy identical in all 7 runs (rho-T excluded: 4 threads, differs run to run before too) |
| interval | 0.475/0.502 | 0.478/0.486 | 1.01 / 0.97 | yes (same rule) |
| precomp | 1.041/1.068 | 1.031/1.187 | 0.99 / 1.11 | not comparable: threaded, counts differ between before runs |
| complexity | 1.299/1.432 | 1.352/1.494 | 1.04 / 1.04 | yes (all rows identical) |
| glv | 0.133/0.145 | 0.122/0.141 | 0.91 / 0.98 | output has no counts column that is seed-stable; not asserted |
| ic | 0.186/0.251 | 0.234/0.238 | 1.26 / 0.95 | not comparable: threaded |
| cheon | 0.018/0.020 | 0.016/0.019 | 0.84 / 0.98 | yes |
| gpu | 0.056/0.063 | 0.053/0.054 | 0.95 / 0.85 | yes (emulated cpu-rho/gpu-rho rows identical) |
The bench sizes are milliseconds; VM noise (+-20-50%) exceeds any effect there. Only the large-table BSGS ratio is outside the noise.

## Interpretation (separate from the measurements)
The prefetch helps once the baby-step table no longer fits in cache; at the sizes `make bench` runs it has no resolvable effect. The `ec_batch_op` change saves ~5% instructions but its wall effect is not resolved here. Whether either moves an end-to-end index-calculus S is untested; these are stage-level engineering changes.

## Limits
Unisolated VM, noisy; no Tier 0/1 receipts; no A/A control run; threaded rows cannot be count-compared; the fuzzers are not committed as tests (kept under raw/fuzz); ec_tau.c and curve.c not read in full.
