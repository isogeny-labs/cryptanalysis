# tet: index-calculus linear algebra (`src/linalg.c`), WALL-only (2026-11-12)

Branch `perf/ca-indexcalc-linalg`, base `cea0f68f`
(`claude/performance-optimization-parallel-vgenii`). Scope: `src/indexcalc.c`,
`src/linalg.c`, `src/linalg.h`; only `src/linalg.c` changed. Builds on
`docs/perf/20261110-lanczos-spmv-threads.md` and the C hot-path audit
(`docs/perf/20261112-c-hotpath-audit.md`: sieve 2-7 % of the precompute,
Lanczos 69-75 %).

Everything here is WALL class: every residue, Lanczos iteration count,
attempt, solution vector, `known`, fingerprint and CLI output is identical to
the base; no counted unit exists in this code (`ca_invmod` is untouched).
Primary evidence is deterministic callgrind `Ir`. Wall times are **local,
unisolated, [pcc:unverified]** (shared 4-vCPU VM, load average 1.4-2.5 during
the ABAB runs, no PMU). No benchmark row, leaderboard row or pcc claim.

## Profile first

Base, `ic_precompute_zp44` (189,338,005 Ir): `spmv64` 68 %, the Lanczos
vector update (inside `ca_linsolve_mod_prime_mt`) ~20 %, sieve 4.7 %.
56-bit `ca ic` (p = 72057594037925687, seed 7, 2,885,342,179 Ir): `spmv128`
78 %, update ~14 %, sieve+trial ~1.2 %. The 44-bit IC matrix is 1290 x 716,
8766 nonzeros: 92 % are +-1, rows average 6.8 terms. So the product loops are
dominated by per-term loads (column, value, vector) and per-row overhead.
`ic_log_zp44` is 81 % `trial_factor` (already inverse-multiplication tests,
four primes a step); not touched.

## Commits

| # | commit | change |
|---|---|---|
| 1 | `6f0dc479` | level-1 (64-bit) Lanczos gather: A and A^T re-laid with the +-1 terms first as bare indices; vectors carry their negation `q - v` behind them (2n, 2m entries), so a -1 term is a load from the second half and every term is nonnegative (no bias, no sign, no coefficient load, no multiply). Producers (A v rows, vector update, start vector, verify copy) write the negation half; the update has neg / no-neg copies so the scatter-fallback path pays nothing. Level-1 bound K(2q-1) < 2^64 loosened to K q < 2^64. |
| 2 | `1fe7d008` | per-row width: a row (or A^T row) whose own sum of \|c\| times q stays below 2^64 is summed in 64 bits from the new layout; only heavy rows (dense columns of A^T; nearly every row for q near 2^63) take the signed 128-bit sum over the plain CSR with the same K q bias. At 56 bits (K = 3101, q = 2^55) only a few dozen rows are heavy, so the whole product left the 128-bit kernel. `spmv64`/`spmv128` replaced by one `lz_spmv` (always-inline body, two specialised call shapes). |
| 3 | `92044728` | `dense_dot`: one running 128-bit sum (mul, add, adc) over a pointer loop unrolled by four instead of summing two products first (gcc spilled the temporary). |
| 4 | (this note) | evidence |

## Callgrind `Ir` (base -> final), `ca_perfbench`, fingerprints identical

| kernel | base Ir | final Ir | change | fingerprint (base = final) |
|---|---:|---:|---:|---|
| `relation/c_ic_precompute_zp44` | 189,338,005 | 171,676,910 | -9.3 % | `f5eb415267f56692` |
| `relation/c_ic_precompute_zp52` (--full) | 1,058,411,749 | 939,481,620 | -11.2 % | `9c7326039d062242` |
| `relation/c_linsolve_sparse` (q = 2^60, 57 % non-unit) | 109,809,232 | 110,052,559 | +0.2 % | `3e54751cb68b8bc7` |
| `relation/c_dense_solve` | 13,630,869 | 10,848,408 | -20.4 % | `c31c4ce65893a5be` |
| `relation/c_ic_log_zp44` | 21,721,818 | 21,721,818 | 0 | `705095b7f97010ff` |
| `relation/c_ic_randexp_zp36` | 26,687,677 | 26,645,385 | -0.2 % | `0c634a2270d2e07a` |
| `ca ic` 56-bit, seed 7, `--threads 1` | 2,885,342,179 | 2,146,260,443 | -25.6 % | output identical |

(`c_linsolve_sparse` is a synthetic, heavy-row system; its Ir is flat, its
wall is not slower.)

## Wall (local, unisolated, [pcc:unverified]; ABAB x5 interleaved, median of per-run medians; load 1.8-2.0)

| kernel | base ms | final ms | ratio |
|---|---:|---:|---:|
| `ic_precompute_zp44` | 23.62 | 19.60 | 0.83 |
| `ic_precompute_zp52` | 156.87 | 130.55 | 0.83 |
| `linsolve_sparse` | 13.00 | 12.51 | 0.96 |
| `dense_solve` | 1.59 | 1.30 | 0.82 |
| `ca ic` 56-bit `linalg_seconds` | 0.402 | 0.287 | 0.71 (min 0.341 -> 0.285) |

Earlier quieter ABAB for commit 1 alone: zp44 22.99 -> 18.66, zp52 144.89 ->
106.99 (0.81 / 0.74). A 60-bit prime (`ca ic`, heavy rows nearly everywhere)
is a wash: linalg 0.79-0.89 s both ways.

## Identity checks

- `ca_perfbench` fingerprints of all 34 kernels (`--full`) base vs final:
  identical (diff of id/fingerprint lists empty).
- `CA_LA_THREADS` = 1, 2, 4: zp44 / linsolve_sparse / zp52 fingerprints equal
  the base at every count.
- `ca ic --seed 7 --threads 1` at p = 281474976705359, 72057594037925687,
  1152921504606846883 (g = 2, h = 12345), `CA_LA_THREADS` 1 and 4, base vs
  final: output (x, relations, factor base, verified logs, Lanczos
  iterations) md5-identical per prime.

## Tests

- `ctest -j2` (Release, final tree): 20/20 pass; `test_linalg` 34,207 checks
  (x, `known`, rc, iterations, attempts, active size, dense flag at threads
  1-5; 64-bit, 128-bit and scatter moduli, rank-deficient systems) also with
  `CA_LA_THREADS=3,4`; `test_indexcalc` 195 checks.
- TSan (`-DCA_SANITIZE=thread`): `test_linalg`, `test_indexcalc` with
  `CA_LA_THREADS=4`, `ca_perfbench` `linsolve_sparse`@4 and
  `ic_precompute_zp44`@3: 0 reports.

## Reverted ideas

| idea | outcome |
|---|---|
| separate +1 / -1 / other runs per row (no negation vector) | Ir **up** (189.3 -> 191.8 M): three short loops per row, per-row overhead above the saved loads; dropped |
| negation vector for the 128-bit (level-2) kernel as well | Ir -7 % at 56 bits but local wall **+25 %** (two more data-dependent loops, doubled gather footprint); replaced by the per-row split of commit 2, which keeps the original 128-bit code for heavy rows |
| unit-sum helper by `n & 2` / `n & 1` tail bits | Ir 189.2 M vs 176.2 M for the pointer-difference form; reverted |
| unroll the others loop of the 128-bit row by two / unit loop by four | Ir 111.8 -> 116.9 M; reverted |
| update loop with Montgomery reduction of `wj c1R + wp c2R` (one reduction for two products) | Ir -3.2 % on zp44 but wall **+8 %** at zp52 and +8 % at 56 bits (128-bit mul port pressure); reverted |
| reuse the previous step's `ca_invmod` for `c2` | 0.5 % Ir, below the noise floor; dropped |
| `trial_factor`, sieve | not touched: already inverse-multiplication tests (ic_log) and 1.2-4.7 % of the run |

## Deferred method changes (not done: would change a count, a draw or a method)

- Block Lanczos / Wiedemann or a different solver would change iteration
  counts and the reported `lanczos_iterations`.
- Dropping the redundant second Lanczos pass (A^T D A applied as one fused
  sweep of A) needs a different traversal and a CSC copy; same sums but
  different cache behaviour is untested here.
- Column reordering by degree: Lanczos is permutation-equivariant (so the
  result is identical) but the gain for the L1/L2 footprint was not measured.
- Smaller factor-base / relation-count changes belong to the IC collector, not
  to this scope.

## Disk / artefacts

Build dirs `/home/user/wt/b-linalg` and `b-linalg-tsan` removed after the run.
sha256 prefixes of the measured binaries (Release `-g -O3`, gcc 13.3, no
`-march`): base `ca_perfbench` 6313d30c3ebbbfdf, final `ca_perfbench`
ffdb3b9cf5a77db3, base `ca` 52da2d40167843fe, final `ca` 94cdfff2da27d7b2.

## Review follow-up

An independent review rebuilt base and candidate, reran test_linalg (34,207
checks, also at CA_LA_THREADS=3), test_indexcalc (195 checks, also at 4
threads), compared all 34 ca_perfbench fingerprints (identical) and `ca ic
--seed 7` output at three primes and CA_LA_THREADS 1 and 4 (identical apart
from the timing fields), and saw `relation/c_dense_solve` Callgrind Ir fall
about 19 % (including setup). One small hardening: `lz_free` and
`lz_gat_free` now null the pointers they free, so the error path of `lz_init`
(which calls `lz_free`, after which `lanczos` calls it again) no longer frees
twice. No change to results or to the measured kernels.
