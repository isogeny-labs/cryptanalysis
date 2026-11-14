# C library hot-path audit: profile first, then WALL-class fixes (2026-11-12)

Branch `claude/nice-babbage-bn0fn0`, base `0568f9b92` (origin/main).
Source of the candidate list: `crypto:docs/assessment-speed-productionization-20261110.md`
§3b (C4, C14, the "lower priority" items) plus what the profile below showed.
Earlier landed work this builds on: `docs/perf/20261110-glv-invmod-wall-only.md`,
`docs/perf/20261110-lanczos-spmv-threads.md`.

Every timing here is a **local, unisolated** measurement on a shared 4-vCPU
cloud VM (Sapphire-Rapids class, no PMU, gcc 13.3, Release `-O3`, no `-march`),
with other agents' builds and test suites running at the same time (1-minute
load average 10–22, recorded per row). All of them are **[pcc:unverified]**.
No pcc claim, benchmark record, `benchmarks/` row or leaderboard row is made.
A speed claim still needs AGENTS.md §10 (isolated host, A/A arm, ABAB ≥ 5,
`benchrec` record). Instruction counts (callgrind `Ir`) are deterministic and
are the primary evidence where they apply; where a change trades a branch or
a division for arithmetic, Ir rises and is **not** the measure — those rows
say so.

All changes are in the WALL class: identical values, group-operation counts,
RNG consumption and outputs. No COUNTER or METHOD change was made, so no new
option or method id was needed. Field-operation diagnostics of walk starts
change where noted (fewer inversions, more products); `-DCA_GLV_FIELD_COUNT`
builds keep the old GLV start and batch paths, so their `CA_FC_*` counts are
unchanged.

## 1. Profile (Phase A)

Build: Release from a `git archive` of `0568f9b92`, `-DCMAKE_EXPORT_COMPILE_COMMANDS=ON`,
plus `-g` for symbols (the `-g` build's `rho_thread_main` disassembly is
instruction-for-instruction the plain Release one). Kernels run under
`valgrind --tool=callgrind --instr-atstart=no` with `ca_perfbench run --filter K
--exact --instr --samples 1` (one warm run outside the measured region);
`ca_bench generic --bits 40,44 --threads 1` (default 5 reps) and the GLV solve
`ca_rho_orbit_bench j0-56 1` (the largest GLV case under 60 s: about 6 s
natively, 79,576,759 group ops) run whole. "self" sums a function's own
instructions over all source files (inlined header code included); "incl" is
callgrind's inclusive cost. Tables: `callgrind_annotate --auto=no
[--inclusive=yes]`, aggregated per function.

### 1.1 Top-15 by self instructions, base

#### `rho_ec36`

Base, total Ir 298,406,013
| # | function | self Ir | self % | incl % |
|---:|---|---:|---:|---:|
| 1 | `rho_thread_main` | 207,876,907 | 69.7 | 88.8 |
| 2 | `ca_invmod` | 51,330,576 | 17.2 | 17.2 |
| 3 | `__memset_avx2_unaligned_erms` | 12,926,380 | 4.3 | 4.3 |
| 4 | `ca_htab_insert` | 8,983,032 | 3.0 | 3.0 |
| 5 | `pthread_mutex_lock@@GLIBC_2.2.5` | 5,685,790 | 1.9 | 1.9 |
| 6 | `ec_op` | 5,099,339 | 1.7 | 18.2 |
| 7 | `pthread_mutex_unlock@@GLIBC_2.2.5` | 3,534,410 | 1.2 | 1.2 |
| 8 | `ca_mont_inv` | 1,054,914 | 0.4 | 17.6 |
| 9 | `walk_restart` | 668,521 | 0.2 | 11.8 |
| 10 | `rho_solve_impl` | 361,626 | 0.1 | 100.0 |
| 11 | (PLT stub) | 307,340 | 0.1 | 1.3 |
| 12 | (PLT stub) | 307,340 | 0.1 | 2.0 |
| 13 | `ec_jac_dbl` | 91,957 | 0.0 | 0.0 |
| 14 | `ca_ec_group_mul` | 62,923 | 0.0 | 0.1 |
| 15 | `ec_dbl` | 34,730 | 0.0 | 0.1 |

#### `glv_rho_j0_32`

Base, total Ir 105,018,578
| # | function | self Ir | self % | incl % |
|---:|---|---:|---:|---:|
| 1 | `ca_invmod` | 31,910,334 | 30.4 | 30.4 |
| 2 | `glv_class_reduce` | 22,096,998 | 21.0 | 21.0 |
| 3 | `ec_batch_op` | 20,252,300 | 19.3 | 49.2 |
| 4 | `glv_rho_solve` | 17,097,399 | 16.3 | 99.5 |
| 5 | `ec_jac_dbl` | 4,326,341 | 4.1 | 4.1 |
| 6 | `__memset_avx2_unaligned_erms` | 3,151,168 | 3.0 | 3.0 |
| 7 | `ec_hash` | 2,595,940 | 2.5 | 2.5 |
| 8 | `ca_ec_group_mul` | 2,320,487 | 2.2 | 7.0 |
| 9 | `ca_mont_inv` | 711,102 | 0.7 | 31.0 |
| 10 | `ca_htab_insert` | 289,764 | 0.3 | 0.3 |
| 11 | `ec_op` | 40,923 | 0.0 | 0.5 |
| 12 | `ca_group_mul` | 35,032 | 0.0 | 7.1 |
| 13 | `_int_malloc` | 32,000 | 0.0 | 0.0 |
| 14 | `glv_startup_combination` | 23,465 | 0.0 | 6.7 |
| 15 | `calloc` | 19,168 | 0.0 | 3.1 |

#### `rho_zp40`

Base, total Ir 146,340,363
| # | function | self Ir | self % | incl % |
|---:|---|---:|---:|---:|
| 1 | `rho_thread_main` | 145,372,131 | 99.3 | 99.7 |
| 2 | `__memset_avx2_unaligned_erms` | 309,360 | 0.2 | 0.2 |
| 3 | `ca_mont_pow` | 228,544 | 0.2 | 0.2 |
| 4 | `ca_htab_insert` | 119,752 | 0.1 | 0.1 |
| 5 | `rho_zp_dp` | 108,593 | 0.1 | 0.3 |
| 6 | `pthread_mutex_lock@@GLIBC_2.2.5` | 77,330 | 0.1 | 0.1 |
| 7 | `pthread_mutex_unlock@@GLIBC_2.2.5` | 48,070 | 0.0 | 0.0 |
| 8 | `ca_group_mul` | 14,760 | 0.0 | 0.2 |
| 9 | `rho_solve_impl` | 10,494 | 0.0 | 100.0 |
| 10 | `_int_malloc` | 7,387 | 0.0 | 0.0 |
| 11 | `walk_restart` | 6,096 | 0.0 | 0.1 |
| 12 | `__popcountdi2` | 6,048 | 0.0 | 0.0 |
| 13 | `ca_zp_group_mul` | 5,346 | 0.0 | 0.2 |
| 14 | (PLT stub) | 4,180 | 0.0 | 0.0 |
| 15 | (PLT stub) | 4,180 | 0.0 | 0.1 |

#### `ec_batch_add`

Base, total Ir 254,160,855
| # | function | self Ir | self % | incl % |
|---:|---|---:|---:|---:|
| 1 | `ec_batch_op` | 237,624,000 | 93.5 | 97.5 |
| 2 | `ca_invmod` | 10,140,034 | 4.0 | 4.0 |
| 3 | `run_ec_batch_add` | 6,230,884 | 2.5 | 100.0 |
| 4 | `ca_mont_inv` | 126,000 | 0.0 | 4.0 |
| 5 | `fp_elem` | 32,512 | 0.0 | 0.0 |
| 6 | `ec_decode` | 7,424 | 0.0 | 0.0 |
| 7 | `perfbench_measured_region` | 1 | 0.0 | 100.0 |

#### `precomp_build_ec32`

Base, total Ir 630,732,024
| # | function | self Ir | self % | incl % |
|---:|---|---:|---:|---:|
| 1 | `ec_batch_op` | 331,367,388 | 52.5 | 53.8 |
| 2 | `pc_build_worker` | 186,163,467 | 29.5 | 99.5 |
| 3 | `ec_hash` | 66,475,997 | 10.5 | 10.5 |
| 4 | `ca_invmod` | 39,780,874 | 6.3 | 6.3 |
| 5 | `ec_op` | 3,751,099 | 0.6 | 5.8 |
| 6 | `pc_base_mul` | 928,421 | 0.1 | 5.7 |
| 7 | `ca_mont_inv` | 912,681 | 0.1 | 6.5 |
| 8 | `msort_with_tmp'2` | 469,976 | 0.1 | 0.9 |
| 9 | `__mempcpy_avx_unaligned_erms` | 259,155 | 0.0 | 0.0 |
| 10 | `pc_entry_cmp` | 179,415 | 0.0 | 0.0 |
| 11 | `__memcpy_avx_unaligned_erms` | 123,562 | 0.0 | 0.0 |
| 12 | `pc_table_solve` | 66,504 | 0.0 | 0.3 |
| 13 | `__memcpy_chk_avx_unaligned_erms` | 49,150 | 0.0 | 0.0 |
| 14 | `0x000000000495d430` | 39,870 | 0.0 | 0.0 |
| 15 | `msort_with_tmp` | 38,918 | 0.0 | 0.2 |

#### `ic_precompute_zp44`

Base, total Ir 189,337,934
| # | function | self Ir | self % | incl % |
|---:|---|---:|---:|---:|
| 1 | `spmv64` | 128,419,618 | 67.8 | 67.8 |
| 2 | `ca_linsolve_mod_prime_mt` | 44,447,521 | 23.5 | 92.8 |
| 3 | `ca_invmod` | 5,471,203 | 2.9 | 2.9 |
| 4 | `sieve_thread` | 2,993,908 | 1.6 | 4.7 |
| 5 | `trial_factor` | 1,636,001 | 0.9 | 0.9 |
| 6 | `__memset_avx2_unaligned_erms` | 1,496,458 | 0.8 | 0.8 |
| 7 | `ca_spmat_add_row` | 1,315,016 | 0.7 | 0.7 |
| 8 | `__memcpy_chk_avx_unaligned_erms` | 803,679 | 0.4 | 0.4 |
| 9 | `rel_push` | 455,351 | 0.2 | 1.2 |
| 10 | `ca_mont_pow` | 446,129 | 0.2 | 0.2 |
| 11 | `__umodti3` | 357,924 | 0.2 | 0.2 |
| 12 | `zp_op` | 206,976 | 0.1 | 0.1 |
| 13 | `_int_malloc` | 167,419 | 0.1 | 0.1 |
| 14 | `ca_bsgs_table_new` | 153,860 | 0.1 | 0.7 |
| 15 | `ca_group_mul` | 101,920 | 0.1 | 0.1 |

#### `linsolve_sparse`

Base, total Ir 109,809,179
| # | function | self Ir | self % | incl % |
|---:|---|---:|---:|---:|
| 1 | `spmv128` | 82,680,246 | 75.3 | 75.3 |
| 2 | `ca_linsolve_mod_prime_mt` | 24,698,999 | 22.5 | 100.0 |
| 3 | `ca_invmod` | 1,800,117 | 1.6 | 1.6 |
| 4 | `ca_spmat_add_row` | 404,849 | 0.4 | 0.4 |
| 5 | `__umodti3` | 49,539 | 0.0 | 0.0 |
| 6 | `__memset_avx2_unaligned_erms` | 42,260 | 0.0 | 0.0 |
| 7 | `__udivti3` | 40,885 | 0.0 | 0.0 |
| 8 | `run_linsolve` | 32,409 | 0.0 | 100.0 |
| 9 | `lz_av` | 22,134 | 0.0 | 40.4 |
| 10 | `lz_atw` | 16,864 | 0.0 | 34.9 |
| 11 | `__memset_chk_avx2_unaligned_erms` | 4,359 | 0.0 | 0.0 |
| 12 | `_int_malloc` | 3,332 | 0.0 | 0.0 |
| 13 | `__strncmp_avx2` | 2,214 | 0.0 | 0.0 |
| 14 | `_int_free_merge_chunk` | 1,845 | 0.0 | 0.0 |
| 15 | `getenv` | 1,639 | 0.0 | 0.0 |

#### `generic4044`

Base, total Ir 56,752,708,942
| # | function | self Ir | self % | incl % |
|---:|---|---:|---:|---:|
| 1 | `ec_batch_op` | 14,661,006,511 | 25.8 | 43.5 |
| 2 | `rho_thread_main` | 14,549,922,610 | 25.6 | 26.7 |
| 3 | `ca_invmod` | 10,936,887,048 | 19.3 | 19.3 |
| 4 | `k_solve_impl` | 3,751,263,342 | 6.6 | 19.8 |
| 5 | `ec_hash` | 2,658,513,755 | 4.7 | 4.7 |
| 6 | `ca_htab_insert` | 2,419,878,764 | 4.3 | 4.3 |
| 7 | `ca_htab1_insert` | 1,426,467,116 | 2.5 | 2.5 |
| 8 | `zp_hash` | 1,170,133,732 | 2.1 | 2.1 |
| 9 | `zp_batch_op` | 1,163,351,482 | 2.0 | 2.0 |
| 10 | `grumpy_solve_impl` | 1,138,169,037 | 2.0 | 32.7 |
| 11 | `ca_bsgs_table_new` | 1,033,879,345 | 1.8 | 11.8 |
| 12 | `bsgs_table_solve_impl` | 735,787,410 | 1.3 | 7.6 |
| 13 | `ca_htab1_find` | 584,193,080 | 1.0 | 1.0 |
| 14 | `ca_mont_inv` | 188,798,568 | 0.3 | 19.6 |
| 15 | `__memset_avx2_unaligned_erms` | 93,319,638 | 0.2 | 0.2 |

#### `j056`

Base, total Ir 46,751,995,014
| # | function | self Ir | self % | incl % |
|---:|---|---:|---:|---:|
| 1 | `glv_class_reduce` | 17,758,924,152 | 38.0 | 38.0 |
| 2 | `glv_rho_solve` | 14,142,291,759 | 30.2 | 99.9 |
| 3 | `ec_batch_op` | 12,176,084,784 | 26.0 | 26.1 |
| 4 | `ec_hash` | 2,426,158,022 | 5.2 | 5.2 |
| 5 | `ec_jac_dbl` | 105,855,804 | 0.2 | 0.2 |
| 6 | `ca_invmod` | 62,289,488 | 0.1 | 0.1 |
| 7 | `ca_ec_group_mul` | 56,009,370 | 0.1 | 0.4 |
| 8 | `ca_htab_insert` | 8,812,946 | 0.0 | 0.0 |
| 9 | `ec_interval_all` | 6,649,297 | 0.0 | 0.1 |
| 10 | `ca_htab1_insert` | 3,441,802 | 0.0 | 0.0 |
| 11 | `ca_htab1_find` | 2,117,668 | 0.0 | 0.0 |
| 12 | `ca_mont_inv` | 750,666 | 0.0 | 0.1 |
| 13 | `ec_op` | 579,846 | 0.0 | 0.0 |
| 14 | `glv_restart` | 510,408 | 0.0 | 0.4 |
| 15 | `ca_group_mul` | 372,106 | 0.0 | 0.4 |


### 1.2 What the compiler emits (objdump of the Release `ca_perfbench`)

Counts per function body (baseline build):

| function | insns | `div` | `__umodti3` / `__udivti3` calls | `mulx`/`adcx` | indirect calls | notes |
|---|---:|---:|---:|---:|---:|---|
| `rho_thread_main` | 1821 | 2 | 0 / 0 | 0 | 14 | both `div`s are the look-ahead's `(idx + 1) % sh->r` on retried steps; 28 conditional jumps come from `ca_addmod` (`if (s < a \|\| s >= m)`), 2 from `ca_ec_canon_words`' `flip ? ny : yy` |
| `glv_rho_solve` | 2824 | 10 | 10 / 7 | 0 | 12 | all `div`/u128 calls are off the step path (setup `ca_mulmod`, `glv_recover`, n ≥ 2^63 fallback); per step: one vtable `ca_group_hash`, one vtable `batch_op` per round, staging copies of 64 B per walk, a 4-slot history shifted per commit |
| `glv_class_reduce` | 322 | 0 | 0 | 0 | 3 | an out-of-line call per step; the j=0 minimum `if (h < best_hash)` compiled to 10 conditional jumps (five coin flips per step) |
| `ec_batch_op` | 509 | 0 | 0 | 0 | 0 | branch-light; one `ca_mont_inv` call per batch |
| `ca_invmod` | 180 | 2 | 0 | 0 | 0 | the `div`s are the Euclid path for even moduli only |
| `walk_restart` | 300 | 2 | 0 | 0 | 7 | one affine `ec_op` (one inversion) per set scalar bit |
| `sieve_thread` | 622 | 6 (+2 `idiv`) | 1 / 0 | 0 | 0 | per (row, prime): four `%`, one `ca_invmod`, one `ca_mulmod` |
| `spmv64` / `spmv128` | 84 / 138 | 0 | 0 | 0 | 0 | division-free (Shoup / REDC) |

- No `mulx`/`adcx`/`adox` anywhere: the default build has no ISA level, so
  Montgomery products use `mul`. That is the companion change's subject
  (`CA_ARCH`, `docs/perf/20261112-build-flags-and-cuda.md`), not this one.
- No `memcpy` calls of walk structs on the step path; the per-step copies are
  inline vector moves (history shift, GLV staging).
- `memset` (4.3 % of `rho_ec36`, 3.0 % of `glv_rho_j0_32`) is `calloc`
  zeroing the DP table once per solve. Its size feeds the reported
  `bytes_peak`, so presizing or shrinking it would change an output; kept.
- `__popcountdi2` is a libgcc call at the baseline ISA (no `popcnt`); it is
  called once per walk start, not per step.


### 1.3 What the profile says, in instructions × confidence

1. **`rho_ec36` walk starts (C4).** `walk_restart` is 11.8 % inclusive and the
   multiplier-table build in `rho_solve_impl` another ~7 %: each set scalar
   bit is one affine `ec_op`, one `ca_mont_inv`. 47k of the kernel's 50k
   inversions come from starts; the batched rounds need only 2.8k.
2. **Data-dependent branches in the walk steps.** Not visible in Ir; read in
   the disassembly: `ca_addmod` on the random exponent coefficients (two per
   step, every walk), `ca_ec_canon_words` (one per EC step), the j=0 orbit
   minimum (five per GLV step), the GLV `if (k)` (one per step).
3. **GLV per-step overheads at 56 bits** (`j0-56`): `glv_class_reduce` as a
   call (prologue/epilogue/dispatch ~5.7 %), the re-hash of `wk->Y` through
   the vtable (`ec_hash` 5.2 %), the staging copies plus vtable `batch_op`,
   and the history shift (~7 % of Ir, all moves).
4. **`rho_ec36` per-step overheads:** history shift (~5.4 %), DP-table mutex
   with one walker (3.1 % lock/unlock with `dp_bits` ≈ 2), the retry `div`.
5. **GLV starts at 32 bits:** `glv_startup_combination` ~6.7 % inclusive:
   two Jacobian ladders and an affine add, three inversions per start.
6. **Not worth it here:** the IC sieve (1.6 % self, 4.7 % inclusive at 44
   bits; 2–7 % of the precompute at 48–60 bits, `ca_bench ic`), Lanczos
   (`spmv64`/`spmv128`, division-free already, `linalg.c` not in this scope),
   `ec_batch_op` itself (branch-light; its inversions in `ca_bench generic`
   come from grumpy's batches of 3 and kangaroo/BSGS, which are inherent to
   those algorithms), `ca_invmod` (see §4).

## 2. Changes (Phase B), one commit each

| # | commit | item | change | class |
|---|---|---|---|---|
| 1 | `b8c24cb3a` | C4 | rho walk starts and multipliers: fixed-base points summed in Jacobian coordinates, one inversion (`ca_ec_fb_sum`, `rho_start_point`) | WALL (start field-op diagnostics change) |
| 2 | `8a2baed6a` | C14 | rho 2/4-cycle history as a ring (`hist_pos`); look-ahead `(i + 1) % r` → mask (`rho_next_index`) | WALL |
| 3 | `bca13d049` | DP lock | no DP-table mutex when one walker runs inline with no monitor (`sh.single`, `rho_dp_insert`) | WALL |
| 4 | `ab03cbd1c` | GLV | keep each walk's point hash (`Yh[w]`) instead of re-hashing `wk->Y` through the vtable every step | WALL (glv_walk, checkpoint unchanged) |
| 5 | `be4fe04e4` | GLV | `glv_class_reduce` always_inline | WALL |
| 6 | `7ddda2bcc` | GLV batch via vtable | fused native batch step (Montgomery trick over 4 chains, `ca_ec_add_with_di`), no staging copies; FIELD_COUNT builds keep the vtable | WALL |
| 7 | `304901934` | GLV history | 2/4-cycle history as a ring in the former padding byte; normalised to the old newest-first layout before every checkpoint write | WALL (checkpoint bytes unchanged) |
| 8 | `1f3a02cf3` | branches | `ca_addmod_sel` (mask) for the per-step coefficient adds in rho EC, rho (Z/pZ)^* and GLV; `ca_addmod` untouched (pqc-assay pins and proves it) | WALL |
| 9 | `d955fed0c` | branches | j=0 orbit minimum as a mask select; GLV `lam^k` products unconditional (lam^0 = 1) | WALL |
| 10 | `451d4ee5c` | branches | `ca_ec_canon_words` select written as a mask (gcc had made it a branch) | WALL |
| 11 | `bed518be1` | GLV starts | Shamir joint Jacobian ladder with base + target precomputed (`ca_ec_group_mul2`), one inversion per start; FIELD_COUNT builds keep the old path | WALL (start field-op diagnostics change) |

Files: `src/rho.c`, `src/curve.c`, `src/curve_internal.h`, `src/ca_internal.h`,
`src/group_ec.c` (new static `ec_jac_to_affine`, `ec_jac_add_bits`,
exported-internal `ca_ec_fb_sum`, `ca_ec_group_mul2`), `tests/test_modarith.c`.
`include/` is not touched (so `verification/pqc-assay/sources.sha256` needs no
re-pin). `src/group_ec.c` is not in the listed scope globs but is not
in the co-tenant agent's either (it owns `CMakeLists.txt`, `cmake/`, `cuda/`,
`gpu/`, `deploy/`); it holds the Jacobian routines the start-point items reuse.

## 3. Evidence per item

### 3.1 Identity gate (every commit)

Each commit's `src/`, `include/` and `tests/` were built in scratch on the
base snapshot's CMake files (Release) and compared with the base build:

- `ctest -j4`: 19/19 pass.
- `ca_perfbench run --samples 3 --min-samples 3 --max-seconds 5 --warmup-seconds 0.2`:
  all 31 fingerprints identical to the scratch `perfbench.jsonl` reference.
- `ca_bench generic --bits 24,28,32,36 --reps 3 --threads 1 --group both --json`:
  120 instance rows identical in every field but `seconds` (and the
  text table minus time columns).
- `ca_bench glv`: identical (13 curves × 20 instances).
- `ca_rho_orbit_bench j0-56 1`: scalar 14684984045970115, 79,576,759 group
  ops, replay verified, identical.
- `ca ic` 48-bit (p = 281474976705359, g = 13) and 56-bit (p =
  72057594037925687, g = 5), `--seed 7 --threads 1`: x = 987654321987,
  relations 2762 / 6678, Lanczos iterations 1105 / 2538, verified logs
  303 / 669, identical.

Additionally, at the final state:

- The full branch HEAD (`git archive`, with the co-tenant's CMake changes:
  `-ffp-contract=off`, 20 ctest entries including `isa-no-mmx`): ctest
  20/20 and every gate item above identical.

- `ca_bench generic --bits 40,44 --reps 3 --threads 1 --group both`: 60
  instance rows identical (minus `seconds`).
- GLV checkpoint (items 4, 7, 11; `ca solve --alg glv` on the j0-56 curve,
  seed 5): the checkpoint written at `--max-ops 20000000` differs from the
  base binary's only in the elapsed-seconds and checksum bytes (as two base
  runs do); resuming it, and resuming the base binary's checkpoint, give the
  base result (x, ops 154,562,295, iterations); a full run that checkpoints
  every second equals the uninterrupted base run (ops 154,541,594).
- Non-default configurations, base vs final, each built both ways:
  `-DCA_GLV_BATCH_ESCAPE=ON`, `-DCA_GLV_FIELD_COUNT=ON`,
  `-DCA_GLV_CYCLE_ESCAPE=OFF`, `-DCA_GLV_LOOKAHEAD_LEGACY=ON`,
  `-DCA_RHO_J0_FACTORED_HASH=OFF`: `ca_bench glv`, the `glv_rho_j0_32`,
  `rho_ec36`, `rho_zp40` fingerprints and the j0-56 solve identical in
  each (79,576,626 / 79,576,759 / 79,586,180 / 54,431,375 / 79,576,759
  group ops). Compile-only with `-DCA_WERROR=ON`: those plus
  `CA_RHO_J0_COORDINATE_ORBIT`, `CA_J0_RHO_COORD_CANON` and `-DCA_RHO_TRACE`
  pass; `-DCA_GLV_TRACE` fails with `-Werror` on `trace_prior_ops` set but
  unused under `NDEBUG`, identically in the base tree (pre-existing).
- `-DCA_SANITIZE=ON` (address, undefined): ctest 19/19; `rho_ec36`,
  `rho_zp40`, `glv_rho_j0_32`, `ec_batch_add` fingerprints and j0-56
  identical; GLV checkpoint stop/resume as above.
- `-DCA_SANITIZE=thread` (item 3 touches the threaded DP insert): ctest
  19/19 with 0 ThreadSanitizer reports; `ca_bench generic --bits 32,36
  --threads 4 --group ec` and `ca rho --threads 1|2 --state-dir ...
  --checkpoint-every 1` (the monitored path, which keeps the lock): 0
  reports.
- `tests/test_modarith.c` (item 8): `ca_addmod_sel == ca_addmod` on all
  13³ edge triples and 300,000 random reduced and unreduced inputs.

### 3.2 Instruction counts per commit (callgrind Ir, measured region)

`ca_perfbench run --filter K --exact --instr`; j0-56 is the whole
`ca_rho_orbit_bench j0-56 1` process. "—" = the commit does not touch that
path (not re-measured; the count carries over).

| step | `rho_ec36` | `rho_zp40` | `glv_rho_j0_32` | `j0-56` (whole run) |
|---|---:|---:|---:|---:|
| base `0568f9b92` | 298,406,013 | 146,340,363 | 105,018,578 | 46,751,995,014 |
| 1 C4 starts | 257,083,693 | 146,343,186 | 105,170,093 ¹ | — |
| 2 C14 ring + mask | 248,315,362 | 144,174,884 | — | — |
| 3 DP lock | 238,324,285 | 144,041,337 | — | — |
| 4 GLV hash kept | — | — | 103,111,434 | 44,395,918,298 |
| 5 reducer inline | — | — | 101,492,854 | 43,351,526,309 |
| 6 fused batch | — | — | 99,026,361 | 42,444,124,769 |
| 7 GLV ring | — | — | 97,945,925 | 41,350,957,527 |
| 8 `ca_addmod_sel` ² | 246,008,553 | 156,682,439 | 98,274,155 | — |
| 9 j0 min / lam^k ² | — | — | 102,075,658 | — |
| 10 canon mask ² | 251,273,916 | — | — | — |
| 11 Shamir starts | 251,249,188 | 156,682,439 | 99,096,127 | 44,482,273,604 |
| final vs base | −15.8 % | +7.1 % ² | −5.6 % | −4.9 % |

Unchanged-code controls at the final state: `ec_batch_add` 254,160,855 (base
254,160,855), `precomp_build_ec32` 630,732,851 (630,732,024),
`ic_precompute_zp44` 189,337,934 (189,337,934), `linsolve_sparse`
109,809,182 (109,809,179). `ca_bench generic --bits 40,44 --threads 1`
whole run: 56,752,708,942 → 56,532,663,005 (rho is 27 % of it; grumpy,
BSGS and kangaroo are untouched).

¹ +0.14 %: `ec_jac_add_affine` gained callers in item 1 and stopped being
inlined into `ca_ec_group_mul`, which GLV starts use (item 11 replaces that
path).
² Items 8–10 replace conditional jumps on walk data by arithmetic: Ir rises
by design and is not the measure; see the wall table. Items 8–10 together
take j0-56 from 41.35 G to about 44.5 G Ir while its wall time falls (§3.3).

### 3.3 Wall time, local and unisolated, [pcc:unverified]

ABAB ×5, base build (A) vs final build (B), same host, alternating. Each run
is one `ca_perfbench run --exact --samples 21 --min-samples 21
--warmup-seconds 0.1`; the table gives the minimum and the median over the
five rounds of each run's minimum sample, and the minimum process CPU time
(user + sys, including the kernel's setup). Load average 9–11 during the
run. `ec_batch_add` and `kangaroo_ec56_w34` run code no item changed: they
are the noise controls.

| kernel | min A → B (ms) | B/A | median A → B (ms) | B/A | CPU min A → B (s) | B/A |
|---|---|---:|---|---:|---|---:|
| `rho_ec36` | 31.92 → 24.55 | 0.769 | 32.76 → 27.45 | 0.838 | 0.75 → 0.61 | 0.817 |
| `rho_zp40` | 29.12 → 8.95 | 0.307 | 30.09 → 9.41 | 0.313 | 0.64 → 0.27 | 0.425 |
| `glv_rho_j0_32` | 11.11 → 8.16 | 0.734 | 11.76 → 8.84 | 0.752 | 0.32 → 0.22 | 0.698 |
| `ec_batch_add` (control) | 17.53 → 17.56 | 1.002 | 18.79 → 22.57 | 1.201 | 0.47 → 0.48 | 1.013 |
| `kangaroo_ec56_w34` (control) | 12.51 → 12.52 | 1.001 | 13.24 → 13.23 | 1.000 | 0.37 → 0.36 | 0.973 |

`ca_rho_orbit_bench j0-56 1` (one GLV solve, 79,576,759 group ops), ABAB ×5,
process wall seconds: A 7.059, 6.341, 6.786, 6.396, 6.377 (min 6.34,
median 6.40); B 4.189, 4.302, 4.362, 4.336, 4.201 (min 4.19, median 4.30):
B/A 0.66 (min) and 0.67 (median), load 9.

The `ec_batch_add` median (1.20 with min 1.00 and code unchanged) shows the
size of the noise on this host; only effects well beyond it are read here.
The `rho_zp40` result is the largest: the native (Z/pZ)^* round is little
more than one Montgomery product, a hash and two coefficient adds per step,
and the two adds were each a conditional jump on a coin flip of walk data.
Branch mispredictions are the likely cause, but this host has no PMU, so
they were not counted (`perf stat` unavailable); the inference rests on the
disassembly, the Ir rise and the wall drop together.

Per-step wall measurements taken while landing each item (same caveats,
smaller ABAB, load 10–22) are in the commit messages; the ones that showed
a direction: item 1 `rho_ec36` min 32.07 → 28.91 ms; item 8 `rho_zp40`
29.16 → 9.48 ms, `rho_ec36` 28.11 → 24.43 ms, `glv_rho_j0_32` 11.05 →
10.20 ms; item 9 j0-56 8.15 / 7.85 → 6.92 s; item 10 `rho_ec36` 23.78 →
22.05 ms; item 11 `glv_rho_j0_32` 8.88 → 8.16 ms. Items 2–7 were judged
on Ir (pure instruction removals with no new branches).

## 4. Rejected, skipped and not attempted

| candidate | verdict | why |
|---|---|---|
| IC sieve: `bitlen()` while-loop → `clz`, `ca_mulmod(b, inv, q)` → 64-bit `%` (q is a 32-bit factor-base prime), at `indexcalc.c` ~:80, :568 | **tried, reverted** | identity gate passed, but `ic_precompute_zp44` Ir moved 189,337,961 → 189,118,211 (−0.12 %) and 7 alternating 56-bit `ca ic` runs gave sieve_seconds 0.011–0.035 both ways (noise). The sieve is 1.6 % self at 44 bits and 2–7 % of the precompute at 48–60 bits; the linear algebra dominates. Not worth a diff. |
| IC sieve per-(row, prime) `ca_invmod` + four `%` | skipped | same profile share as above; the division count per unit is small next to the Lanczos phase |
| DP table presize / per-thread DP buffers (`rho.c` ~:926, `util.c` ~:110) | skipped | presizing changes the reported `bytes_peak`; buffering DPs per thread delays collision detection and so changes multi-thread `group_ops` (already nondeterministic, but a different distribution). The single-thread lock elision (item 3) took the deterministic part. Rehash under lock: 0 grows were seen in the profiled kernels (the table is presized from the expected DP count) |
| `memset` of the DP table (`calloc`, 3–5 % of the small kernels) | kept | its size is an output (`bytes_peak`) |
| `ca_mont_inv` → `ca_invmod` call chain, 2^-k folding into the R^3 product | skipped | ~20–30 Ir of ~1000 per inversion; a table of 2^(192-k) mod p would need a field in the public `ca_mont`, which pqc-assay pins |
| another `ca_invmod` (safegcd / Lehmer) | not attempted | the previous note's local microbenchmarks [pcc:unverified] put the current binary xgcd at 0.55–0.63 of the Euclid's time per call; for 64-bit moduli a 62-divstep safegcd needs about as many dependent steps. Its 30 % share of `glv_rho_j0_32` comes from the batch width (W ≈ 33 walks per inversion at 32 bits), which is a METHOD parameter |
| GLV batch width / walks per thread | not done | changes the walk (METHOD); would need a new option id and an experiment |
| C14 hot/cold split of `rho_walk` (~280 B) | not done | after the ring change every field is touched per step except `saved`/`win` (one compare); 256 walks stream sequentially and the prefetcher keeps up; no profile signal |
| `precomp_build_ec32` (`pc_build_worker` + `ec_batch_op` + vtable `ec_hash`, 630 M Ir) | not done | `src/precomp.c` is outside this task's file scope; same fusion as item 6 would apply |
| j=1728 legacy reducer loop (`ca_ec_endo` + branchy minimum) | not done | j=0 is the production curve family here; j=1728 is exercised only by `ca_bench glv` rows |
| `-march` / `mulx` / LTO | not here | companion change (`docs/perf/20261112-build-flags-and-cuda.md`) |

## 5. Profile after (final state, same method)

#### `rho_ec36` (after)

After, total Ir 251,249,188
| # | function | self Ir | self % | incl % |
|---:|---|---:|---:|---:|
| 1 | `rho_thread_main` | 211,898,090 | 84.3 | 92.8 |
| 2 | `__memset_avx2_unaligned_erms` | 12,926,380 | 5.1 | 5.1 |
| 3 | `ec_jac_add_affine` | 11,013,222 | 4.4 | 4.4 |
| 4 | `ca_htab_insert` | 8,983,032 | 3.6 | 3.6 |
| 5 | `ca_invmod` | 4,612,892 | 1.8 | 1.8 |
| 6 | `ca_ec_fb_sum` | 1,176,584 | 0.5 | 5.4 |
| 7 | `walk_restart` | 101,088 | 0.0 | 3.5 |
| 8 | `ca_mont_inv` | 94,773 | 0.0 | 1.9 |

#### `glv_rho_j0_32` (after)

After, total Ir 99,096,127
| # | function | self Ir | self % | incl % |
|---:|---|---:|---:|---:|
| 1 | `glv_rho_solve` | 58,929,039 | 59.5 | 99.4 |
| 2 | `ca_invmod` | 31,260,882 | 31.5 | 31.5 |
| 3 | `__memset_avx2_unaligned_erms` | 3,151,168 | 3.2 | 3.2 |
| 4 | `ec_jac_dbl` | 2,484,408 | 2.5 | 2.5 |
| 5 | `ec_jac_add_affine` | 1,713,512 | 1.7 | 1.7 |
| 6 | `ca_mont_inv` | 696,612 | 0.7 | 32.2 |
| 7 | `ca_htab_insert` | 289,764 | 0.3 | 0.3 |
| 8 | `ca_ec_group_mul2` | 283,036 | 0.3 | 4.1 |

#### `rho_zp40` (after)

After, total Ir 156,682,439
| # | function | self Ir | self % | incl % |
|---:|---|---:|---:|---:|
| 1 | `rho_thread_main` | 155,844,931 | 99.5 | 99.7 |
| 2 | `__memset_avx2_unaligned_erms` | 309,360 | 0.2 | 0.2 |
| 3 | `ca_mont_pow` | 228,544 | 0.1 | 0.1 |
| 4 | `ca_htab_insert` | 119,752 | 0.1 | 0.1 |
| 5 | `rho_zp_dp` | 108,596 | 0.1 | 0.2 |
| 6 | `ca_group_mul` | 14,760 | 0.0 | 0.2 |
| 7 | `rho_start_point` | 7,632 | 0.0 | 0.2 |
| 8 | `_int_malloc` | 7,387 | 0.0 | 0.0 |

#### `j056` (after)

After, total Ir 44,482,273,604
| # | function | self Ir | self % | incl % |
|---:|---|---:|---:|---:|
| 1 | `glv_rho_solve` | 44,284,503,617 | 99.6 | 99.9 |
| 2 | `ec_jac_dbl` | 53,738,549 | 0.1 | 0.1 |
| 3 | `ca_invmod` | 47,546,273 | 0.1 | 0.1 |
| 4 | `ec_jac_add_affine` | 40,021,314 | 0.1 | 0.1 |
| 5 | `ec_batch_op` | 24,349,108 | 0.1 | 0.1 |
| 6 | `ca_htab_insert` | 8,812,946 | 0.0 | 0.0 |
| 7 | `ca_ec_group_mul2` | 7,286,299 | 0.0 | 0.2 |
| 8 | `ec_interval_all` | 6,649,297 | 0.0 | 0.1 |

#### `generic4044` (after)

After, total Ir 56,532,663,005
| # | function | self Ir | self % | incl % |
|---:|---|---:|---:|---:|
| 1 | `rho_thread_main` | 14,947,751,478 | 26.4 | 27.0 |
| 2 | `ec_batch_op` | 14,661,006,511 | 25.9 | 43.7 |
| 3 | `ca_invmod` | 10,334,237,158 | 18.3 | 18.3 |
| 4 | `k_solve_impl` | 3,751,263,342 | 6.6 | 19.9 |
| 5 | `ec_hash` | 2,658,513,755 | 4.7 | 4.7 |
| 6 | `ca_htab_insert` | 2,419,878,764 | 4.3 | 4.3 |
| 7 | `ca_htab1_insert` | 1,426,467,116 | 2.5 | 2.5 |
| 8 | `zp_hash` | 1,170,133,732 | 2.1 | 2.1 |


What moved: in `rho_ec36`, `ca_invmod` 17.2 % → 1.8 % and `walk_restart`
11.8 % → 3.5 % inclusive (starts now cost Jacobian additions,
`ec_jac_add_affine` 4.4 %); the mutex calls are gone. In `glv_rho_j0_32`
and `j0-56` the walk is one function (`glv_class_reduce`, the batch and the
hash are inlined or fused); at 32 bits the batch's one inversion per ~33
walks (31.5 %) is now the largest single item, which only a wider batch
(METHOD) would reduce.

## 6. Decisions

- `ca_addmod` is not changed: `verification/pqc-assay` proves that exact C
  (SAW + Lean) and pins the header by hash. The walks use a separate
  `ca_addmod_sel` with the same value for every input (tested).
- GLV history ring: `glv_walk` is written raw into checkpoints, so `hpos`
  lives in existing padding and every checkpoint write normalises the ring
  first; the on-disk format and bytes stay those of the old code.
- GLV `Yh[]` is a side array, not a `glv_walk` field, for the same reason.
- `-DCA_GLV_FIELD_COUNT` builds keep the vtable batch and the separate start
  products so `CA_FC_*` stays comparable with earlier diagnostic runs; the
  default build's start field-operation counts change (fewer inversions).
- `src/curve.c` changed, so the last commit moves the `--live` Lean source
  binding (`experiments/glv-table-rule-confirm-20261022/`) to the commit that
  holds the final `curve.c` (the table selector text is unchanged).

## 7. Reproduce

Scratch scripts (not committed): build a `git archive` snapshot per commit,
then `c2-gate.sh` (ctest, perfbench fingerprints, `ca_bench generic`/`glv`,
j0-56, `ca ic` 48/56) and compare with the base outputs; callgrind with
`valgrind --tool=callgrind --instr-atstart=no ./ca_perfbench run --filter K
--exact --instr --samples 1 --min-samples 1`; wall with alternating
`ca_perfbench run --filter K --exact --samples 21 --min-samples 21`
(base, final, base, final, …).
