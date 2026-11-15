# C library memory pass: correctness audit, footprint, structure, WALL-class fixes (2026-11-12)

Branch `claude/nice-babbage-bn0fn0`, base `dc4885a61` (origin/main, which holds
rounds 1–2: `docs/perf/20261112-c-hotpath-audit.md`,
`docs/perf/20261112-build-flags-and-cuda.md`). Earlier notes whose skip lists
this pass keeps: `docs/perf/20261110-glv-invmod-wall-only.md`,
`docs/perf/20261110-lanczos-spmv-threads.md`.

Every timing here is a **local, unisolated** measurement on a shared 4-vCPU
cloud VM (no PMU, gcc 13.3, Release `-O3 -g`, no `-march`), with other agents
running at the same time (1-minute load average 3–8, given per row). All of
them are **[pcc:unverified]**. No pcc claim, benchmark record, `benchmarks/`
row or leaderboard row is made; a wall-clock claim still needs AGENTS.md "CPU
performance isolation gate" / "evidence tiers" (isolated host, A/A arm, ABAB ≥ 5,
`benchrec` record). Valgrind byte and block counts and callgrind `Ir` are
deterministic for one-thread runs and are the primary evidence here.

All changes are WALL class: identical walk outputs, group-operation counts,
fingerprints, checkpoint payloads and replay. No reported memory field
(`bytes_peak` and the like) changed: see §3.1.

## 1. Correctness audit (Phase A.1)

### 1.1 What ran

| tool | coverage | build |
|---|---|---|
| `valgrind --tool=memcheck --leak-check=full --show-leak-kinds=definite,indirect,possible --errors-for-leak-kinds=definite,indirect --track-origins=yes --error-exitcode=99` | all 18 ctest executables (`test_bsgs` … `test_sixclass`) | Release `-g` |
| same | 30 `ca` CLI runs: `rho` EC 1 and 2 threads, `solve --alg glv` (glv-j0-32), `kangaroo`, `bsgs`, `grumpy`, `solve --alg precomp` (1 and 2 threads), `solve --alg dlog`, `ic` lsieve 48-bit (1 and 2 threads), `ic --method rexp` (1 and 2 threads), `solve --alg gpu-rho --backend emulate`; checkpoint write + `--resume` for rho (1 and 2 threads), GLV, kangaroo, gpu-rho, IC lsieve, IC rexp, precomp, plus bsgs/grumpy/dlog with `--state-dir` | Release `-g` |
| ASan + LSan + UBSan (`-DCA_SANITIZE=ON`, `detect_leaks=1`, `detect_stack_use_after_return=1`) | ctest; the 30 CLI runs; all 31 `ca_perfbench` kernels; `ca_rho_orbit_bench j0-56 1`; `ca ic` 56-bit at 4 threads; `ca_bench generic --bits 32,36 --threads 4 --group both`; `ca_bench glv` | RelWithDebInfo at the base, Release at the final state |
| `clang-tidy` 18, `clang-analyzer-unix.Malloc`, `unix.MallocSizeof`, `core.*`, `unix.cstring.*` | every `src/*.c` (path-sensitive leak and null checks on error paths, which memcheck only sees when they run) | compile_commands of the base build |
| TSan (`-DCA_SANITIZE=thread`) at the final state | ctest (18 C tests); `ca ic` lsieve 56-bit at 4 threads, rexp at 4 threads, lsieve 48-bit at 3 threads with a state dir; `solve --alg precomp` at 4 threads | Release `-g` |

### 1.2 Defects found

**None.** Every memcheck run reported `ERROR SUMMARY: 0 errors` (no invalid
read or write, no use of uninitialised values, no uninitialised bytes passed
to `write(2)` by any checkpoint writer, no definite or indirect leak). ASan,
LSan and UBSan printed no report on any run; TSan printed none. So Phase B
had no correctness fix to make.

What the tools printed that is not a defect:

| report | where | why it is not a defect |
|---|---|---|
| memcheck "possibly lost" 288 B (one block; 864 B in `test_indexcalc`) | `allocate_dtv` under `pthread_create`, `src/indexcalc.c:1198` / `:1277` | the DTV of a thread stack that glibc caches after `pthread_join` and hands to the detached Lanczos pool worker started later; the pointer into the live stack is interior, hence "possibly". Seen only in runs that start both. |
| memcheck "still reachable" 6,464 B | `lz_pool_acquire`, `src/linalg.c:838` | the process-lifetime Lanczos thread pool, kept on purpose (comment at `src/linalg.c:816–821`); only in runs with ≥ 2 linear-algebra threads |
| clang-analyzer `core.DivideZero` | `src/curve.c:851` (`n / c.m`) | false positive: `glv_rho_solve` is called only when `g->endo_kind != 0` (`src/curve.c:1486`), and every assignment that leaves `endo_kind` nonzero sets `aut_order` to 4 or 6 (`src/curve.c:78–96`) |
| ctest `isa-no-mmx` fails in sanitizer builds | `.cold` parts of `linalg.c` (`lanczos`, `ca_linsolve_mod_prime_mt`, `dense_solve_rowops`), `ec_tau.c`, `sixclass.c`, `indexcalc.c` (`individual_log_zeta`) | pre-existing, present at the base: gcc 13 uses `%mm` registers to move 128-bit values in the UBSan report paths only. Not in any file this pass touched; the default and `CA_ARCH` builds pass the test (20/20). |

## 2. Footprint (Phase A.2)

Workloads: the six `ca_perfbench` kernels (`run --filter ID --exact --samples
1 --min-samples 1 --warmup-seconds 0`, which runs the kernel twice: one warm
run and the sample), `ca ic` at 48 and 56 bits (`--seed 7 --threads 1`) and
the 56-bit j0 GLV solve (`ca_rho_orbit_bench j0-56 1`, 79,576,759 group
operations). Tools: `valgrind --tool=massif` (peak heap) and
`valgrind --tool=dhat` (totals, lifetimes, per-site breakdown). Whole
process, so the kernels' setup is included. Before → after where the final
state differs; one number where it does not.

### 2.1 Totals, base `dc4885a61` → final

| workload | peak heap, massif (B) | peak live, dhat (B) | bytes allocated | allocations | heap bytes read / written (base) | instructions (whole process) |
|---|---:|---:|---:|---:|---:|---:|
| `rho_ec36` | 3,237,129 | 3,237,137 | 25,874,656 | 100 | 395,720,556 / 227,529,380 | 477,137,155 |
| `glv_rho_j0_32` | 103,656 | 103,656 | 6,497,496 | 583 | 61,339,465 / 38,536,925 | 192,861,839 |
| `rho_zp40` | 109,425 | 109,425 | 641,694 | 70 | 264,649,894 / 190,937,916 | 313,785,245 |
| `ic_precompute_zp44` | 3,223,025 → 2,282,278 | 3,223,025 → 2,282,278 | 8,576,002 → 5,653,250 | 890 → 888 | 526,899,318 / 48,897,876 | 381,859,108 → 375,430,570 |
| `linsolve_sparse` | 301,288 | 301,288 | 512,872 | 71 | 258,095,973 / 20,802,561 | 222,776,594 |
| `precomp_build_ec32` | 104,153 | 104,153 | 311,530 | 42 | 1,271,605,803 / 588,922,905 | 1,265,732,956 → 1,235,715,576 |
| `ca ic` 48-bit | 5,636,075 → 3,403,953 | 5,636,075 → 3,403,953 | 8,098,619 → 4,320,523 | 659 → 658 | 641,883,672 / 55,605,735 | 458,303,260 → 448,870,078 |
| `ca ic` 56-bit | 10,473,207 → 8,051,821 | 10,473,207 → 8,061,977 | 16,828,945 → 10,122,609 | 1,395 → 1,394 | 3,549,377,802 / 270,978,002 | 2,904,544,353 → 2,882,657,202 |
| j0-56 GLV solve | 14,194,688 | 14,194,688 | 18,458,624 | 13 | 21,648,759,559 / 16,805,045,832 | 44,481,999,990 |

(The whole-process instruction counts of unchanged workloads move by a few
tens between runs: environment and path lengths.)

Reading: every workload allocates fewer than 1,400 blocks; no hot loop
allocates. The heap peak is one structure in each case: the DP hash table
(rho, GLV), the relation list (index calculus), or the matrix copies
(`linsolve_sparse`).

### 2.2 Top allocation sites (dhat, base)

Sites are the allocator wrapper and its first caller (line numbers of the
base tree). "Mean lifetime" is the blocks' average life as a share of the run.

#### `rho_ec36`

| allocation site | bytes allocated | blocks | bytes live at global peak | mean lifetime (% of run) |
|---|---:|---:|---:|---:|
| `ca_htab_init (util.c:71) < rho_solve_impl (rho.c:1215)` | 25,165,824 | 8 | 3,145,728 | 12.20 |
| `rho_thread_main (rho.c:737)` (walks, 280 B each) | 492,800 | 8 | 61,600 | 12.20 |
| `rho_thread_main (rho.c:738)` (`Yn`) | 56,320 | 8 | 7,040 | 12.20 |
| `rho_thread_main (rho.c:739)` (`B`) | 56,320 | 8 | 7,040 | 12.20 |
| `rho_solve_impl (rho.c:1173)` (multipliers) | 32,768 | 8 | 4,096 | 12.48 |
| `rho_thread_main (rho.c:740)` (scratch) | 28,160 | 8 | 3,520 | 12.20 |

#### `glv_rho_j0_32`

| allocation site | bytes allocated | blocks | bytes live at global peak | mean lifetime (% of run) |
|---|---:|---:|---:|---:|
| `ca_htab_init (util.c:71) < glv_rho_solve (curve.c:967)` | 6,291,456 | 64 | 98,304 | 1.50 |
| `glv_rho_solve (curve.c:908)` (walks, 304 B each) | 58,368 | 64 | 912 | 1.54 |
| `ec_count_once (group_ec.c:611)` | 32,768 | 1 | 0 | 0.17 |
| `ec_count_once (group_ec.c:612)` | 32,768 | 1 | 0 | 0.17 |
| `ca_htab1_init (util.c:163) < ec_interval_all (group_ec.c:491)` | 32,768 | 1 | 0 | 0.16 |
| `glv_rho_solve (curve.c:904)` (multipliers) | 16,384 | 64 | 256 | 1.54 |

#### `rho_zp40`

| allocation site | bytes allocated | blocks | bytes live at global peak | mean lifetime (% of run) |
|---|---:|---:|---:|---:|
| `ca_htab_init (util.c:71) < rho_solve_impl (rho.c:1215)` | 589,824 | 6 | 98,304 | 16.59 |
| `rho_thread_main (rho.c:737)` | 26,880 | 6 | 4,480 | 16.59 |
| `rho_solve_impl (rho.c:1173)` | 6,144 | 6 | 1,024 | 16.61 |
| `_IO_file_doallocate` (stdio buffer) | 4,096 | 1 | 0 | 0.00 |
| `dlp_new (ca_perfbench.c:216)` | 3,784 | 1 | 3,784 | 99.87 |
| `rho_thread_main (rho.c:738)` | 3,072 | 6 | 512 | 16.59 |

#### `ic_precompute_zp44`

| allocation site | bytes allocated | blocks | bytes live at global peak | mean lifetime (% of run) |
|---|---:|---:|---:|---:|
| `rel_push (indexcalc.c:104) < sieve_thread (indexcalc.c:616)` (precompute list) | 3,211,264 | 2 | 1,605,632 | 48.65 |
| `rel_push (indexcalc.c:104) < ic_precompute_impl (indexcalc.c:1120)` (first 1024 slots) | 1,605,632 | 2 | 802,816 | 2.06 |
| `rel_push (indexcalc.c:104) < sieve_thread (indexcalc.c:607)` (worker's local list) | 1,605,632 | 2 | 802,816 | 2.86 |
| `ca_bsgs_table_new (bsgs.c:192)` (individual logs) | 859,264 | 392 | 0 | 0.00 |
| `ca_spmat_init (linalg.c:21) < build_matrix (indexcalc.c:916)` | 227,712 | 2 | 0 | 46.48 |
| `ca_spmat_init (linalg.c:22) < build_matrix (indexcalc.c:916)` | 227,712 | 2 | 0 | 46.48 |

#### `linsolve_sparse`

| allocation site | bytes allocated | blocks | bytes live at global peak | mean lifetime (% of run) |
|---|---:|---:|---:|---:|
| `ca_spmat_init (linalg.c:21) < setup_linsolve (ca_perfbench.c:1184)` | 50,176 | 1 | 50,176 | 99.28 |
| `ca_spmat_init (linalg.c:22) < setup_linsolve (ca_perfbench.c:1184)` | 50,176 | 1 | 50,176 | 99.28 |
| `ca_spmat_init (linalg.c:21) < ca_linsolve_mod_prime_mt (linalg.c:1202)` | 47,568 | 2 | 23,784 | 49.33 |
| `ca_spmat_init (linalg.c:22) < ca_linsolve_mod_prime_mt (linalg.c:1202)` | 47,568 | 2 | 23,784 | 49.33 |
| `lz_init (linalg.c:521) < lanczos (linalg.c:956)` | 47,568 | 2 | 23,784 | 49.02 |
| `lz_init (linalg.c:522) < lanczos (linalg.c:956)` | 47,568 | 2 | 23,784 | 49.02 |

#### `precomp_build_ec32`

| allocation site | bytes allocated | blocks | bytes live at global peak | mean lifetime (% of run) |
|---|---:|---:|---:|---:|
| `pc_worker_push (precomp.c:221) < pc_build_worker (precomp.c:317)` | 98,304 | 4 | 32,768 | 24.74 |
| `pc_collect (precomp.c:407)` | 65,536 | 2 | 32,768 | 0.37 |
| `qsort_r < pc_collect (precomp.c:414)` | 65,536 | 2 | 32,768 | 0.23 |
| `pc_build_worker (precomp.c:275)` (`Y`) | 16,384 | 2 | 0 | 49.58 |
| `pc_build_worker (precomp.c:276)` (`Yn`) | 16,384 | 2 | 0 | 49.58 |
| `pc_build_worker (precomp.c:277)` (`B`) | 16,384 | 2 | 0 | 49.58 |

#### `ca ic` 48-bit

| allocation site | bytes allocated | blocks | bytes live at global peak | mean lifetime (% of run) |
|---|---:|---:|---:|---:|
| `rel_push (indexcalc.c:104) < sieve_thread (indexcalc.c:616)` (precompute list, 2048 then 4096 slots) | 4,816,896 | 2 | 4,816,896 | 50.01 |
| `rel_push (indexcalc.c:104) < ic_precompute_impl (indexcalc.c:1120)` | 802,816 | 1 | 0 | 1.89 |
| `rel_push (indexcalc.c:104) < sieve_thread (indexcalc.c:607)` | 802,816 | 1 | 802,816 | 5.21 |
| `ca_bsgs_table_new (bsgs.c:192)` | 664,176 | 303 | 0 | 0.00 |
| `ca_spmat_init (linalg.c:21) < build_matrix (indexcalc.c:916)` | 176,768 | 1 | 0 | 93.69 |
| `ca_spmat_init (linalg.c:22) < build_matrix (indexcalc.c:916)` | 176,768 | 1 | 0 | 93.69 |

#### j0-56 GLV solve

| allocation site | bytes allocated | blocks | bytes live at global peak | mean lifetime (% of run) |
|---|---:|---:|---:|---:|
| `ca_htab_init (util.c:71) < glv_rho_solve (curve.c:967)` | 12,582,912 | 1 | 12,582,912 | 99.89 |
| `ca_htab1_init (util.c:163) < ec_interval_all (group_ec.c:491)` | 4,194,304 | 1 | 0 | 0.10 |
| `glv_rho_solve (curve.c:908)` (4096 walks × 304 B) | 1,245,184 | 1 | 1,245,184 | 99.90 |
| `glv_rho_solve (curve.c:909)` (`Yn`) | 131,072 | 1 | 131,072 | 99.90 |
| `glv_rho_solve (curve.c:910)` (`B`) | 131,072 | 1 | 131,072 | 99.90 |
| `glv_rho_solve (curve.c:907)` (scratch) | 65,536 | 1 | 65,536 | 99.90 |

### 2.3 Short-lived churn

dhat finds one family of blocks that live for less than 0.1 % of a run with
ten or more blocks: the individual-log step of index calculus builds one BSGS
table per small subgroup (`ca_bsgs_table_new`, `src/bsgs.c:192`, and its
`ca_htab1_init`): 303 table + 303 hash allocations (741,744 B) for `ca ic`
48-bit, 196 + 196 per `ic_precompute_zp44` run. Their callgrind share is
below 0.1 % (`ca_bsgs_table_new` 153,860 Ir of 189 M in the round-2
profile). Not worth a pool. No walk, sieve or Lanczos loop allocates.

### 2.4 Cache behaviour (cachegrind, base)

`valgrind --tool=cachegrind --cache-sim=yes`, D1 48 KiB 12-way, LL 2 MiB
16-way (one Sapphire-Rapids core's L1d and L2), whole process. Cachegrind
models no hardware prefetcher: sequential streams count as misses here that
the hardware mostly hides (§4.2 shows what that means for the walks).

| workload | D refs | D1 misses (rate) | LL misses (rate) | where the D1 misses are |
|---|---:|---:|---:|---|
| `rho_ec36` | 131,360,170 | 8,078,498 (6.1 %) | 403,861 (0.3 %) | walk array, three passes a round (W = 220 × 280 B = 61.6 KB > 48 KB); LL misses: DP-table inserts (3 MB table, random) |
| `glv_rho_j0_32` | 32,015,328 | 112,648 (0.4 %) | 4,124 (0.0 %) | — (3 walks) |
| `rho_zp40` | 90,667,329 | 14,981 (0.0 %) | 5,485 (0.0 %) | — |
| `ic_precompute_zp44` | 126,834,768 | 5,223,703 (4.1 %) | 77,069 (0.1 %) | `spmv64` (86 % of D1 read misses): the CSR column/value streams |
| `linsolve_sparse` | 69,519,600 | 2,433,235 (3.5 %) | 5,922 (0.0 %) | `spmv128` (86 %): same streams |
| `precomp_build_ec32` | 346,477,082 | 14,475 (0.0 %) | 4,739 (0.0 %) | — (lane arrays fit in L1) |
| `ca ic` 48-bit | 147,943,652 | 6,419,188 (4.3 %) | 115,444 (0.1 %) | `spmv64` (86 %) |
| `ca ic` 56-bit | 929,329,255 | 45,226,807 (4.9 %) | 299,977 (0.0 %) | `spmv64` |
| `kangaroo_ec56_w34` (control) | 89,691,700 | 51,052 (0.1 %) | 8,509 (0.0 %) | — |
| j0-56 GLV solve | 7,592,062,645 | 786,404,060 (10.4 %) | 310,693 (0.0 %) | walk array, three passes a round (4096 × 304 B = 1.25 MB): about 9.9 D1 misses per group operation, all hits in a 2 MiB L2 |

In `spmv64` the gather vector (`v[col[k]]`, n × 8 B = 20 KB at 48 bits) stays
in L1: 88.4 M reads over 29.5 M terms give 3.9 M misses, which is the
col + val stream (8 B a term, 64-byte lines) and nothing else.

## 3. Structure (Phase A.3)

### 3.1 Reported memory fields: where `bytes_peak` goes

`ca_stats.bytes_peak` ("approximate peak heap usage of tables",
`include/cryptanalysis/ca_types.h:64`) is:

- **not** in `ca_perfbench` fingerprints (`tools/ca_perfbench.c:94–105`
  leaves it out on purpose);
- in `ca_bench` JSON rows (`tools/ca_bench.c:309`), the `ca` CLI's JSON
  (`tools/ca_cli.c:343`, `:911`, `:1045`), the Python/Rust bindings and
  `cloud/taskq/ca_ecdlp_job.py`;
- **not** in any checkpoint: rho writes header + table entries
  (`src/rho.c:283–300`), GLV writes header + `glv_walk` records, IC writes
  relations; no replay certificate reads it.

No commit here changes it: the identity gate's `ca_bench generic` JSON
comparison keeps `bytes_peak` and stayed identical, and the IC precompute
(the only footprint that changed) reports no `bytes_peak`.

How close it is to the measured peak (not changed; a different accounting is
not an improvement, and it would change `ca_bench` rows):

| solver | `bytes_peak` formula | example | measured live peak (dhat) |
|---|---|---|---|
| rho | DP table `cap × 24` + `r × 48` (`src/rho.c:1376`) | `rho_ec36`: 3,145,728 + r × 48 per solve | 3,237,137 for the process |
| GLV | DP table + `r × 32` (+ tau-pair tables) (`src/curve.c:1433`) | j0-56: 12,587,008 (`ca solve --alg glv`, seed 1) | 14,194,688: the 1.6 MB of walk state (§2.2) is not counted |

### 3.2 DP hash table (`src/util.c`)

- Open addressing, linear probing, 24-byte entries `{key, v0, v1}`, capacity
  the power of two ≥ 2 × expected (load ≤ 0.5 at the expected count), grow at
  load 0.75 by doubling.
- Sized up front from the expected DP count (`src/rho.c:1214`,
  `1.25 sqrt(n) / 2^dp + 1024`), so no profiled run grew it: dhat lists one
  table block per solve and no `htab_grow` site (8 blocks for the 8 solves
  of `rho_ec36`, 1 for j0-56), as round 2 saw in callgrind. A grow
  happens under the solve's mutex in threaded rho (`rho_dp_insert`) and holds
  both tables for its duration (3 × the old size); that is inherent to a
  rehash and occurs only on runs that outlast the estimate.
- Capacity and slot order are part of what the rho checkpoint writes (entries
  in slot order) and capacity is `bytes_peak`, so resizing is not WALL class
  here (same conclusion as round 2's skip list).
- Zeroing: `calloc` of a 3 MB table per solve is `__memset_avx2_unaligned_erms`
  in the profile (12.9 M Ir of `rho_ec36`, about one Ir per byte under
  callgrind's `rep stosb` accounting). The first solve's table comes from
  `mmap` (kernel-zeroed); later ones reuse freed heap and are zeroed by
  `memset`. Forcing every table onto fresh `mmap`
  (`MALLOC_MMAP_THRESHOLD_=131072 MALLOC_TRIM_THRESHOLD_=0`, no code change)
  took `rho_ec36` from min 24.04–25.21 ms to 31.54–33.58 ms over five
  alternating runs: page faults and kernel zeroing cost more than reusing
  warm memory. The current `calloc` is kept.

### 3.3 Walk-state layout and cache footprint

- `rho_walk` is 280 B (`src/rho.c:132`); with W = 220 walks at 36 bits a
  thread's walks are 61.6 KB, one KB-scale `Yn`/`B` each. Every field but
  `saved`/`win` is touched per committed step (round 2). Not written to
  checkpoints.
- `glv_walk` is 304 B (`src/curve.c:369`) and is written raw into the GLV
  checkpoint, so its layout is fixed (round 2 kept `hpos` in former padding
  and `Yh[]` as a side array for that reason). j0-56 runs 4096 walks: 1.25 MB.
- Both rounds stream the walk array three times: denominators, additions,
  commit. Cachegrind charges j0-56 about 9.9 D1 misses per group operation.
  Fusing the additions into the commit pass (one pass and the `Yn` staging
  array fewer) took `rho_ec36`'s simulated D1 misses from 8.08 M to 6.27 M
  but its wall time **up** (§4.2), as did the GLV version on j0-56: the
  hardware prefetcher hides the sequential misses, and splitting the
  Montgomery chains' latency-bound multiplications across the long commit
  body costs more than the misses. Not committed.

### 3.4 Lanczos / structured elimination storage (`src/linalg.c`)

- CSR is already narrow: `uint32_t` row pointers and columns, `int32_t`
  values (`src/linalg.h:17–24`); the Lanczos transpose (`lz_init`) has the
  same widths. Vectors are `uint64_t` because entries are residues mod a
  61-bit q; the 128-bit accumulators (`acc`, `ca_i128`) serve the moduli
  above the 64-bit kernel's range.
- The D1 misses of `spmv64`/`spmv128` are the sequential col/val streams
  (§2.4), which a prefetcher covers; the gathered vector is L1-resident.
  Packing the values into `int8_t` (5 B a term instead of 8) would cut that
  stream by 37 % but needs a second kernel path for wide coefficients, for
  a stream the profile does not show as a stall. Not done.

### 3.5 Relation records (`src/indexcalc.c`)

- `relation` is 784 B: `n`, 96 fixed `col`/`val` slots, `rhs` (4 B of
  padding before `rhs`). At 48 bits the matrix has 44,192 nonzeros over 2,762
  relations, about 16 used slots a relation: some 82 % of the relation
  storage is unused slots.
- The record is also the journal and snapshot format (`relation_size` in
  `ic_journal_header` and `ic_rexp_header`), so shrinking it would change
  checkpoint bytes; a variable-length record needs a format version and is
  left as a recommendation.
- What changed (commits 2 and 3, §4.1): the list's growth policy. It started
  at 1024 slots and doubled, so at 48 bits the step from 2048 to 4096 slots
  held 4.8 MB at once (85 % of the process peak), and each worker's local
  list took 1024 slots (802,816 B) to hold a handful of relations.
- The sieve buffers (`arr`, 2C + 1 bytes; `hmod`/`jmod`, 8 B × nfb) are
  allocated once per worker; they are small.

### 3.6 Alignment of hot arrays

`calloc` returns 16-byte alignment, and `mmap`ed blocks (≥ 128 KiB) start 16
bytes into a page, so every other 32-byte point of `Yn`, `B` or the
multiplier table crosses a cache line. Allocating the rho and GLV multiplier
tables, walk arrays, `Yn` and `B` on 64-byte boundaries (`aligned_alloc`)
changed nothing measurable: `rho_ec36` min 24.16 → 24.37 ms, `rho_zp40`
9.40 → 9.43 ms, `glv_rho_j0_32` 8.83 → 8.85 ms (ABAB × 5); j0-56, ten
alternating solves, min 4,041 → 4,046 ms, median 4,282 → 4,364 ms (load
3.0–3.2). Not committed.

### 3.7 False sharing in thread structs

- `rho_shared` (`src/rho.c:92`): `done` (loaded once a round by every
  walker), `total_ops`/`total_dps`/`restarts` (atomic adds per DP and every
  65,536 operations), the mutex and the table header share cache lines. A
  round is W steps of hundreds of cycles each, so a coherence miss per round
  is under 1 %; the per-DP adds already contend on the lock's line. Not
  changed.
- `rho_thread` (24 B elements, adjacent): `ops` is written once at the end.
- `lz_pool` (`src/linalg.c:644`): `ticket`, `done` and `job` share a line;
  `dots[t]` rows are described as "a cache line each" but the pool comes
  from `calloc` (16-byte aligned), so a row can straddle two lines. Each
  block writes its row once per job; at three jobs per Lanczos iteration
  that is a few misses per iteration. Not changed (no PMU to count it, and
  the expected effect is below this host's noise).

### 3.8 Generated tables (`src/generated/`, 29 headers, 14 MB of source)

All 29 declare `static const` arrays (no non-const table), and only
`src/ec_tau.c` includes them. They land in `.rodata`:
`libcryptanalysis.so` has `.rodata` 5,151,376 B, `.data` 8 B, `.bss` 120 B
(`size -A`); e.g. `ca_tau_wide8_correction`, `ca_tau_wide8_recipe` and
`ca_joint_pair_digit_x` are `O .rodata` symbols. Nothing copies them at
run time (the `malloc`s in `ec_tau.c` hold point tables computed from the
inputs). They are file-backed and paged on demand; each statically linked
tool carries its 5.2 MB `.rodata`.

## 4. Changes (Phase B), one commit each

### 4.1 Commits

| # | commit | file | item | class |
|---|---|---|---|---|
| 1 | `2229fde14` | `src/precomp.c` | Bernstein–Lange build: swap the lanes' `Y`/`Yn` buffers after each batched step instead of copying W points back | WALL |
| 2 | `a27d6cdb5` | `src/indexcalc.c` | reserve the precompute's relation list for its known target (`rel_reserve`) instead of doubling from 1024 slots | WALL (checkpoint payloads unchanged) |
| 3 | `7b998c6b5` | `src/indexcalc.c` | a worker's local relation list starts at 64 slots, not 1024 | WALL |

`src/curve.c` and `include/cryptanalysis/ca_modarith.h` are not touched, so
the Lean source-binding pin and `verification/pqc-assay/sources.sha256` stay
as they are.

### 4.2 Evidence

Identity gate, every commit (scratch build of the commit's `src/`,
`include/`, `tests/` on the base snapshot's CMake files, Release):

- `ctest -j4`: 20/20;
- all 31 `ca_perfbench` fingerprints identical to the pre-round-1
  `perfbench.jsonl` reference;
- `ca_bench generic --bits 24,28,32,36 --reps 3 --threads 1 --group both`
  JSON (every field but `seconds`, `bytes_peak` included) and text table
  minus time columns identical; `ca_bench glv` identical;
- `ca_rho_orbit_bench j0-56 1`: scalar 14684984045970115, 79,576,759 group
  operations, replay verified;
- `ca ic` 48-bit (x = 987654321987, 2,762 relations, 1,105 Lanczos
  iterations) and 56-bit (6,678 / 2,538) identical.

Item-specific identity:

- Commit 1: `solve --alg precomp --table 65536 --threads 1 --seed 3` (32-bit
  curve): full run, checkpointed run and resume identical to the base
  (chains 19,777, precomp ops 68,583,809), `precomp.table.ckpt` and
  `precomp.online.ckpt` byte-identical; the 2-thread build varies between
  two base runs as it does after the change.
- Commits 2–3: IC lsieve 48-bit with `--state-dir`: `relations.ckpt`
  byte-identical; the rexp snapshot (`--method rexp`, 40-bit, seed 9) and the
  `.precomp` sidecars differ from the parent's only in the elapsed-seconds
  and checksum bytes, as two parent runs do; `--resume` of the parent's
  checkpoints by the new binary gives the parent's result.

Instructions (callgrind, measured region, `ca_perfbench run --filter K
--exact --instr`):

| kernel | base | after 1 | after 2 | after 3 (final) |
|---|---:|---:|---:|---:|
| `precomp_build_ec32` | 630,732,851 | 615,724,155 (−2.4 %) | — | 615,724,155 |
| `precomp_online_ec32` | 156,987,477 | 156,987,477 | — | 156,987,477 |
| `ic_precompute_zp44` | 189,337,930 | — | 188,307,186 (−0.5 %) | 187,668,825 (−0.9 %) |
| `ic_randexp_zp36` | 26,687,629 | — | 26,689,805 | 26,606,177 (−0.3 %) |
| `ic_log_zp44` | 21,721,818 | — | — | 21,721,818 |
| `rho_ec36`, `glv_rho_j0_32`, `rho_zp40`, `linsolve_sparse` | 251,249,188 / 99,096,127 / 156,682,439 / 109,809,184 | — | — | unchanged |

Footprint before → after: §2.1 (`ca ic` 48-bit peak −39.6 %, 56-bit −23.1 %,
`ic_precompute_zp44` −29.2 %; bytes allocated −47 % / −40 % / −34 %); the
56-bit IC at 4 threads, commit 3 alone: peak 9,235,970 → 8,387,205 B.

Wall, local, unisolated, [pcc:unverified]. ABAB × 5, each run one
`ca_perfbench run --filter K --exact --samples 21 --min-samples 21
--warmup-seconds 0.1`; min and median over the five runs' minimum samples,
and the minimum process CPU time (user + sys). Base `dc4885a61` (A) vs the
final state (B), load 4.3–5.3:

| kernel | min A → B (ms) | B/A | median A → B (ms) | B/A | CPU min A → B (s) | B/A |
|---|---|---:|---|---:|---|---:|
| `precomp_build_ec32` | 55.15 → 54.80 | 0.994 | 55.50 → 54.90 | 0.989 | 1.29 → 1.28 | 0.988 |
| `ic_precompute_zp44` | 20.57 → 19.60 | 0.953 | 20.84 → 19.62 | 0.941 | 0.57 → 0.53 | 0.927 |
| `ic_randexp_zp36` | 3.34 → 3.26 | 0.976 | 3.35 → 3.29 | 0.983 | 0.17 → 0.17 | 0.989 |
| `ec_batch_add` (control) | 18.46 → 18.49 | 1.002 | 18.64 → 18.60 | 0.998 | 0.51 → 0.51 | 0.996 |
| `kangaroo_ec56_w34` (control) | 13.17 → 13.18 | 1.001 | 13.30 → 13.21 | 0.993 | 0.36 → 0.38 | 1.036 |

Per-commit ABAB (parent vs commit, same method): commit 1
`precomp_build_ec32` 0.997 / 0.995 (min / median; within noise, so commit 1
rests on its Ir); commit 2 `ic_precompute_zp44` 0.965 / 0.964 (control
0.999). Five alternating 56-bit `ca ic` runs (commit 2 vs parent): sieve
seconds 0.008–0.009 vs 0.011–0.015, total 0.313–0.349 s vs 0.315–0.467 s.
The IC wall ratio is larger than its Ir ratio because the removed work is
mostly page faults and zeroing of fresh megabyte buffers, which callgrind
does not count.

End-of-pass checks at the final state: memcheck clean on `test_precomp`,
`test_indexcalc`, `test_modarith`, `test_linalg` and on the nine
checkpoint/resume CLI runs (rexp, rho, bsgs, grumpy, precomp, dlog);
ASan/UBSan (Release, `-DCA_SANITIZE=ON`): ctest 19/20 with only the
pre-existing `isa-no-mmx` failure of §1.2, 0 sanitizer reports in ctest, the
30 CLI runs, all 31 perfbench kernels (fingerprints identical), j0-56 and
`ca ic` 56-bit at 4 threads; TSan (both changed files run in worker
threads): 18/18 C tests, 0 reports, plus `ca ic` lsieve and rexp at 4
threads, lsieve at 3 threads with a state dir, precomp at 4 threads: 0
reports.

### 4.3 Tried and rejected

| candidate | result | verdict |
|---|---|---|
| rho EC: additions fused into the commit pass (no `Yn` staging, one walk pass fewer) | identity gate passed; simulated D1 misses 8.08 M → 6.27 M, Ir 251.2 M → 254.4 M; ABAB × 5 `rho_ec36` min 23.85 → 27.07 ms (1.135), median 1.149; control 1.002 | rejected: the hardware prefetcher already hides the sequential misses, and spreading the four Montgomery chains' dependent products over the commit body costs more |
| GLV: the same fusion | gate passed; j0-56, three alternating pairs, min 4,211 → 4,924 ms | rejected (same reason); `src/curve.c` therefore untouched |
| precomp: exact division-free `% r` (Lemire–Kaser–Kurz, 128-bit `c`) for the multiplier index | identity and a 300k-input unit test passed; Ir 615.7 M → 667.1 M; ABAB `precomp_build_ec32` 1.029 / 1.030, online 0.994 | rejected: the lanes are independent, so the `div` latency overlaps |
| precomp: inline `ec_hash` for the native curve | Ir 615.72 M → 615.66 M; ABAB 0.991 / 0.994 | rejected: no effect beyond noise |
| 64-byte-aligned walk arrays, multiplier tables, `Yn`, `B` (rho and GLV) | §3.6: no change | rejected |
| fresh `mmap` for DP tables (glibc tunables) | §3.2: `rho_ec36` 24 → 31.5 ms | kept `calloc` |

The rejected diffs are kept in the scratch directory, not in the tree.

## 5. Skipped, with reasons

| item | reason |
|---|---|
| DP-table presize / smaller load factor / 32-byte entries | changes `bytes_peak` (in `ca_bench` rows) and the rho checkpoint's slot order; round 2 skipped it for the same reason |
| `relation` record shrink (82 % unused slots) | it is the journal/snapshot record (`relation_size`), so checkpoint bytes would change; needs a format version |
| `int8_t` CSR values for Lanczos | a second kernel path for a prefetched stream with no stall in the profile (§3.4) |
| hot/cold split of `rho_walk`; any reorder of `glv_walk` | `glv_walk` is the checkpoint format; the walk passes' misses are prefetched (§3.3, §4.3) |
| cache-line separation in `rho_shared` and `lz_pool` | under 1 % expected, not countable without a PMU (§3.7) |
| BSGS table pool for IC individual logs | < 0.1 % of instructions (§2.3) |
| `bytes_peak` counting the walk arrays | accounting change, not an improvement; would change `ca_bench` rows (§3.1) |
| full native fused batch in `pc_build_worker` (round 2's precomp item) | `ec_batch_op` is the arithmetic itself; the staging and dispatch parts are the 2–3 % that commit 1 and the rejected inline hash already probed |
| the sanitizer-only MMX in `.cold` sections | pre-existing compiler behaviour in UBSan report paths, outside the touched files; recorded in §1.2 |

## 6. Reproduce

Scratch scripts (not committed), each taking a build directory:
`cm-mc.sh` (memcheck over test executables), `cm-cli.sh` / `cm-cli2.sh`
(the CLI and checkpoint runs, optionally under a valgrind prefix),
`cm-heap.sh` (dhat + massif), `cm-cg.sh` (cachegrind),
`cm-ir.sh` (callgrind Ir of the measured region), `c2-gate.sh` / `c2-cmp.sh`
(identity gate, from round 2), `cm-icck.sh` / `cm-pcck.sh` (IC and precomp
checkpoint bytes and resume), `cm-abab.sh` (alternating wall runs).
Commands are given in §1.1, §2 and §4.2.

## Sources checked

No `research-kb` tool was attached to this subagent session. Read:
`cryptanalysis:docs/perf/20261112-c-hotpath-audit.md`,
`cryptanalysis:docs/perf/20261112-build-flags-and-cuda.md`,
`cryptanalysis:docs/perf/20261110-glv-invmod-wall-only.md`,
`cryptanalysis:docs/perf/20261110-lanczos-spmv-threads.md`,
`cryptanalysis:AGENTS.md` (CPU performance isolation gate and evidence
tiers). Fast remainder: D. Lemire, O. Kaser, N. Kurz, "Faster Remainder by
Direct Computation", Software: Practice and Experience 49 (2019), Theorem 1
(used only in the rejected experiment).
