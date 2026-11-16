# Lead 3: constant-time audit (dudect-style) of the repo scalar multiplication

All numbers below are [pcc:unverified] (single host, single analyst, no replay certificate).

## Question
Does the repository's scalar multiplication leak the scalar through timing?

## What was measured (exactly)
The C routine `ca_group_mul` -> `ca_ec_group_mul` (src/group_ec.c, Jacobian double-and-add, branches on every scalar bit, `ec_jac_add_affine` has early returns), built unmodified from `/home/user/cryptanalysis/src/*.c` with `gcc -O2` (no cmake; objects in `build/`, ~15 s) and linked to `ct_harness.c`. Curve y^2=x^3+x+7 over p=2^61-1, 63-bit scalars (top bit 2^62 set), base point found by x-scan. **The Rust `scalar_mul` / `scalar_mul_ct` in suite/src/ecc/point.rs was NOT measured** (not built). Its own doc comment says `scalar_mul_ct` still has a data-dependent `if bit` and uses non-constant-time num-bigint.

## Preregistration (also in PREREG.txt, written before the N=4e5 data)
- Assigned prediction: if the production routine is constant-time, |t|<4.5; planted-leak control |t|>>4.5.
- My code-reading prior, stated before the run: the routine is NOT constant-time, so low-HW vs random should give |t|>>4.5.
- Kill criterion: planted control |t|<=4.5 on raw and all crops => instrument useless, do not interpret production.
- Controls must pass: A/A and the scalar-ignoring `const` routine give |t|<4.5.

## Method
dudect: per measurement a class is drawn at random (interleaved, ~50/50), inputs are pre-generated, one call is timed with `clock_gettime(CLOCK_MONOTONIC_RAW)`, first 2000 samples discarded, 4e5 retained samples per run (~2e5 per class), pinned with `taskset -c 3`, OMP_NUM_THREADS=1. Welch t on raw data and on data cropped at pooled percentiles 50/75/90/95/99; flag if any |t|>4.5. 3 independent repeats per configuration (`analyze.py`, `results.json`).
Tests: `lowhw` = fixed k=2^62 (HW 1) vs random 63-bit (same length, HW~32); `fixedrand` = fixed random k vs fresh random k (classic dudect); `aa_fixed` = same fixed k both arms; `aa_rand` = fresh random k both arms.

## Controls
- Positive (`planted`): fixed-cost mul on constant scalar plus one extra `ca_group_dbl` iff the input scalar is odd (class 0 even, class 1 random, ~half odd). Tiny leak, about 2% of one call on average.
- Negative (`const`): same mul on a constant scalar, ignoring the input; classes lowhw vs random, and random vs random.
- A/A on the production routine (`prod/aa_fixed`, `prod/aa_rand`).

## Results (max |t| over raw+crops; raw t in brackets; 3 repeats)
| config | max abs t | raw t |
|---|---|---|
| prod / lowhw | 4038.1, 4543.0, 2472.7 | -67.1, -173.0, -179.1 |
| prod / fixedrand | 2034.6, 2106.4, 2925.5 | -89.9, -38.2, -98.4 |
| prod / aa_fixed | 2.3, 2.8, 1.9 | -1.8, -1.0, 0.8 |
| prod / aa_rand | 1.5, 1.2, 2.1 | -0.7, -0.8, 1.1 |
| planted / lowhw (positive) | 161.1, 228.2, 129.2 | -0.1, -8.7, -3.6 |
| planted / fixedrand (positive) | 115.1, 202.6, 124.3 | 1.6, -14.1, -25.7 |
| const / lowhw (negative) | 1.2, 1.7, 1.4 | 0.4, -1.6, 0.3 |
| const / aa_rand (negative) | 2.0, 1.9, 0.9 | -2.0, 1.9, 0.6 |

Mean time per call: prod lowhw class 0 (k=2^62) about 1.3-1.6 us vs random about 4.0-4.5 us; prod fixedrand fixed-k about 2.1-2.4 us vs random about 4.2-4.7 us. Plot: `t_stats.png`.

## Verdict vs prediction
- Kill criterion not triggered: positive control reads |t| 115-228 on cropped statistics in all 6 runs (instrument sees a ~2% leak). Note the planted raw t was sometimes under 4.5 (-0.1, 1.6, -3.6), so the uncropped statistic alone would have missed it on a noisy VM; the percentile crops are what detect it.
- A/A and `const` controls all |t|<=2.8 (all 12 A/A and const runs): no false positives seen.
- Assigned prediction (production is constant-time, |t|<4.5): **refuted**. Production `ca_group_mul` gives |t| in the thousands for low-HW vs random, and in the thousands for fixed vs random. My code-reading prior (not constant-time) is **confirmed**.

## What it does and does not show
Shows: on this host, `ca_group_mul` run time depends strongly on the scalar (bit pattern/HW and likely branch-predictor learning of a repeated scalar), far beyond noise, with working controls. This is expected from a design that is a speed-oriented attack-tool primitive (the repo is a cryptanalysis library, not a signing library).
Does not show: how many bits of an unknown scalar an attacker could recover, since I did not run a key-recovery. The fixed-vs-random gap partly reflects branch-predictor/cache learning of a repeated input rather than a data-flow leak, so `fixedrand` magnitude should not be read as bits leaked; `lowhw` is the cleaner bit-pattern evidence. The Rust routines and `ec_leakage.py Curve.mul` were not timed. This says nothing about the math-level leakage question.

## Caveats
Shared 4-core cloud VM with other agents running, no isolated PMU, taskset pin but not isolcpus, no frequency lock; raw t is visibly unstable between repeats (planted raw t ranged -0.1 to -25.7). A borderline |t| would be inconclusive here; the observed values are not borderline. 64-bit scalars only (no big-int), one curve, one base point, one fixed scalar. Replications were three runs on the same host, not independent hosts.

## Next step
Time Rust `scalar_mul_ct` (cargo build of suite) with the same harness to test the documented residual leak; run on an isolated host (isolab-eks) for a replay certificate; add a key-recovery style test (bit-by-bit HW or length classifier) to convert |t| into bits leaked.

## Files
`ct_harness.c` (C harness), `analyze.py` (runs 8 configs x 3 reps, writes `results.json`), `plot.py`, `t_stats.png`, `PREREG.txt`, `build/` (deleted after build to save space; rebuild: `gcc -O2 -std=gnu11 -I<repo>/include -I<repo>/src -c <repo>/src/*.c` then link).

## Context (main-session note)

`ca_group_mul` belongs to a cryptanalysis library: it runs attacks such as rho
and BSGS on public instances and never handles a secret scalar. Variable time is
therefore expected and is not a vulnerability here. The finding matters only if
this routine is reused somewhere a secret scalar flows through it. The compiled
`ct_harness` binary was removed before commit; rebuild it with the command above.
