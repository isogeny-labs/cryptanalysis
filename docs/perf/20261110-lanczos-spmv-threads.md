# Lanczos SpMV on a thread pool (assessment item C9), 2026-11-10

Source: `crypto:docs/assessment-speed-productionization-20261110.md` §3b C9
(the Lanczos sparse products are 69–75 % of the `ic_precompute_zp44` /
`linsolve_sparse` instructions, single-threaded).

All timings below are **local, unisolated, [pcc:unverified]**: one shared
4-vCPU cloud VM, no PMU, other agents' builds running at the same time
(1-minute load average recorded per row). They are engineering sanity
checks, not benchmark rows, and do not go to `benchmarks/README.md` or the
IC leaderboard. No counted unit changed (see "Counted units").

## What changed

- `src/linalg.c`: `A v`, `A^T w`, the three Lanczos dot products and the
  vector update are split by **output rows** across a persistent,
  process-wide pthread pool (started on first use, detached workers asleep
  between solves). Each block writes only its own rows; the dot products
  are per-block residues added in block order. All sums are exact mod q,
  so every output element, and so the solution, `known` and every report
  field, is the same residue at every thread count.
- Blocks are claimed from a 64-bit ticket `(generation, block count, next
  block)`: a worker that wakes after its job is over cannot claim a block
  of the next job; the caller runs blocks too, so a worker the scheduler has
  not run costs nothing.
- Adaptive use: the Lanczos loop times 16 one-thread steps against 16 pool
  steps and runs up to 512 steps on the faster (early re-probe when a pool
  window falls a quarter behind). Both paths compute identical residues;
  the choice changes the time only.
- The scatter fallback (q ≥ 2^63, or rows of ≥ 2^31 terms) stays on one
  thread. Matrices with fewer than 512 nonzeros per thread, and thread
  counts above the online CPUs, are capped.
- Thread count: `ca_linsolve_mod_prime_mt(..., threads, ...)`;
  `ca_ic_params.threads` (CLI `--threads`) now also reaches the IC linear
  algebra; environment variable `CA_LA_THREADS=<n>` overrides it (the knob
  used for the measurements; `ca_perfbench` fixes `pr.threads = 1`).
  `ca_linsolve_mod_prime` stays one-thread unless `CA_LA_THREADS` is set.
  At one thread the original kernels run unchanged.
- Not done: the optional ±1 index-only coefficient lists (skipped: the
  kernels are already division-free; it would need a second CSR layout and
  was not needed for the parallel result).

## Evidence

| Check | Result |
|---|---|
| (a) `ctest -j4` (Release) | 19/19 pass |
| (a) TSan (`-DCA_SANITIZE=thread`): `test_linalg`, `test_indexcalc` (default and `CA_LA_THREADS=4`), `ca_perfbench` `linsolve_sparse`@4, `ic_precompute_zp44`@2, `ic_precompute_zp52`@3 ×3 | 0 reports (an earlier iteration had one: the stale block-count read the generation ticket now prevents) |
| (a) new test: x, `known`, rc, iterations, attempts, active size, dense flag at threads 1–5 | identical; 64-bit gather (q = 4294967311), 128-bit gather (q = 10^18+3), scatter fallback (q = 2^64−59), incl. a rank-deficient system |
| (b) `ca_perfbench` fingerprints, all 31 default kernels, `CA_LA_THREADS` = 1, 2, 4 | all identical to the unmodified-tree `perfbench.jsonl` |
| (b) `ic_precompute_zp44` / `linsolve_sparse` / `ic_precompute_zp52` (`--full`) at 1, 2, 4 | `f5eb415267f56692` / `3e54751cb68b8bc7` / `9c7326039d062242` at every count (fingerprints hash factor base, unknowns, relations, verified logs, rc, active size, Lanczos iterations, attempts, dense flag, solution vector, `known`) |
| (c) callgrind total Ir at threads = 1, `ic_precompute_zp44` | 372,677,594 → 371,687,781 (−0.27 %) |
| (c) callgrind total Ir at threads = 1, `linsolve_sparse` | 220,634,213 → 220,113,208 (−0.24 %); `spmv128` Ir identical (165,360,492) |
| (e) `ca ic`, 48-bit p = 281474976705359, `--seed 7`, `--threads 1`, `CA_LA_THREADS` = 1/2/4, and the unmodified tree | x = 987654321987, relations 2762, Lanczos iterations 1105, verified logs 303: identical in all four |
| (e) same, 56-bit p = 72057594037925687 | x = 987654321987, relations 6678, iterations 2538, verified logs 669: identical in all four |
| (e) `--threads 4` | same x; relation count differs from `--threads 1` (48-bit 2821, 56-bit 7044) and, in the unmodified tree, between runs (2873 / 2821 / 2821 observed): the parallel sieve's unit order is not deterministic. With the sieve held at `--threads 4`, `CA_LA_THREADS=1` and the default (4) give the same relations and iterations. Pre-existing, outside C9 |

### (d) Wall time, ABAB ×5 (A = unmodified tree, always one LA thread; B = this change at `CA_LA_THREADS` = T)

Each run is one `ca_perfbench run --exact --samples 5 --warmup-seconds 0.1`
process (`--samples 3`, `--full` for zp52); "median" is the median of the
five per-run medians. `ic56 linalg` is `linalg_seconds` from one `ca ic`
run each (56-bit, matrix 4695 × 2538 active).

Quieter host (2026-11-10T18:56Z, load ≈0.95: one other process; final code):

| kernel | T | A median (ms) | B median (ms) | B/A median | A min | B min |
|---|---|---|---|---|---|---|
| ic_precompute_zp44 | 1 | 17.03 | 17.25 | 1.013 | 16.73 | 17.08 |
| ic_precompute_zp44 | 2 | 16.97 | 17.46 | 1.029 | 16.82 | 16.55 |
| ic_precompute_zp44 | 4 | 16.97 | 15.23 | 0.897 | 16.52 | 13.85 |
| linsolve_sparse | 1 | 9.65 | 9.69 | 1.004 | 9.05 | 9.65 |
| linsolve_sparse | 2 | 9.57 | 7.60 | 0.794 | 9.25 | 7.47 |
| linsolve_sparse | 4 | 9.44 | 6.06 | 0.642 | 9.17 | 5.80 |
| ic_precompute_zp52 | 1 | 92.46 | 94.87 | 1.026 | 89.34 | 94.02 |
| ic_precompute_zp52 | 2 | 93.54 | 95.70 | 1.023 | 91.43 | 90.08 |
| ic_precompute_zp52 | 4 | 95.07 | 82.57 | 0.869 | 90.57 | 75.55 |
| ic56 linalg | 1 | 283 | 249 | 0.880 | 246 | 242 |
| ic56 linalg | 2 | 251 | 256 | 1.020 | 245 | 230 |
| ic56 linalg | 4 | 251 | 183 | 0.729 | 250 | 152 |

(T = 1 rows are A/A-like: the same kernels run in both arms, so their
spread, ±3 % here and 12 % on one ic56 median, is the noise floor of this
host.) Whole-kernel times include the sieve and verification, which are
unchanged; the LA share of zp44 is ≈69 % of instructions.

Contended host (another agent's `rustc` at ≈360 % CPU, load ≈4.8 on 4 vCPUs):

| kernel | T | A median (ms) | B median (ms) | B/A median | A min | B min |
|---|---|---|---|---|---|---|
| ic_precompute_zp44 | 1 | 17.27 | 17.59 | 1.019 | 17.10 | 17.03 |
| ic_precompute_zp44 | 2 | 17.32 | 19.41 | 1.121 | 16.82 | 17.72 |
| ic_precompute_zp44 | 4 | 16.59 | 23.60 | 1.423 | 16.32 | 21.23 |
| linsolve_sparse | 1 | 9.76 | 9.96 | 1.020 | 9.64 | 9.78 |
| linsolve_sparse | 2 | 9.71 | 11.08 | 1.141 | 9.58 | 10.57 |
| linsolve_sparse | 4 | 9.57 | 15.17 | 1.585 | 9.30 | 11.21 |
| ic_precompute_zp52 | 1 | 93.75 | 96.35 | 1.028 | 93.58 | 95.93 |
| ic_precompute_zp52 | 2 | 94.85 | 101.40 | 1.069 | 92.55 | 99.74 |
| ic_precompute_zp52 | 4 | 96.81 | 103.68 | 1.071 | 93.61 | 99.36 |
| ic56 linalg | 1 | 267 | 253 | 0.948 | 248 | 252 |
| ic56 linalg | 2 | 250 | 260 | 1.040 | 250 | 257 |
| ic56 linalg | 4 | 252 | 278 | 1.103 | 250 | 265 |

## Reading

- Bit-identity holds at every thread count tested; that is the
  load-bearing result.
- The 784 × 700 (`linsolve_sparse`) and 1267 × 714 (zp44) systems are a few
  microseconds per product: three pool barriers per Lanczos step cost a
  large share of that, so the gains the assessment estimated (2–3.5× on LA
  with 4 cores) are not reached: on the quieter host 4 threads give
  B/A ≈0.64 on `linsolve_sparse` (all LA), ≈0.73 on the 56-bit LA phase,
  0.87–0.90 on the whole zp44/zp52 kernels; 2 threads help only
  `linsolve_sparse` (0.79).
- On a saturated host a spinning pool loses (a preempted worker holds up
  each step). The adaptive switch and the persistent pool bound the loss
  (the first version, per-solve pool without the switch, measured up to
  2.0× slower on ic56 at 4 threads and ≈60× on `linsolve_sparse` before
  block claiming); it is not eliminated. A dedicated host (isolab) is where
  a speed claim would have to be measured.

## Counted units

The LA phase reports `lanczos_iters`, `attempts`, `active_rows/cols`,
`used_dense` (and IC: relations, verified logs, Lanczos iterations): all
identical at 1, 2, 4 threads (fingerprints and `ca ic` JSON above). No
ecbench counter, op count or method id is touched.

## Reproduce

Scratch builds (Release) of 188cd051 (`git archive`) and of this branch;
scripts and raw JSONL in the session scratchpad (`c9/abab_k.sh`,
`c9/abab_ic.sh`, `c9/abab_sum.py`). `CA_LA_THREADS=T ca_perfbench run
--filter relation/c_linsolve_sparse --exact`.
