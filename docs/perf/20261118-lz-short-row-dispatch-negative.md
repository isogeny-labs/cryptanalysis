# 2026-11-18: short-row `lz_sum_idx64` dispatch — negative result

**Disposition: REJECTED. No upstream kernel change. No claimed ECDLP / end-to-end speedup.** All producer-reported timing and test outcomes in this note are [pcc:unverified].

## Baseline, closure, and hypothesis

Repo: `isogeny-labs/cryptanalysis` at main commit `6b64ee6ca07f92db014cf24d277439730ac31f4b`, `src/linalg.c` blob `39253dbaf80aa0fa2ad132507a83d7ec1f9eae04`. The standalone probe uses the unchanged exact upstream `lz_sum_idx64` and light-row unscaled SpMV path, alongside a candidate. Prior closure: [2026-11-12 linalg audit](https://github.com/isogeny-labs/cryptanalysis/blob/6b64ee6ca07f92db014cf24d277439730ac31f4b/docs/perf/20261112-tet-ca-indexcalc-linalg.md) already introduced two-accumulator gather and light/heavy row partitioning, and rejected general unrolling and other row-loop optimizations. The earlier 2026-11-18 next-row prefetch pilot was rejected; this is a *different* candidate.

**Hypothesis:** specializing unit-gather row lengths 0–8 into direct sums and falling back to the exact original for longer rows reduces CPU ns/row on IC-like small sparse rows, preserving outputs, without increasing whole-process cost. Fail if matched controls show material drift, there is no robust CPU win, any independent oracle/differential check fails, or the cold full IC pipeline cannot establish nonregression.

## Local profile and chosen function

Fresh, *extracted-only* `-O2 -pg -fno-inline` gprof profile of a 1290×716 sparse fixture over 120,000 repetitions (0.95 s sampled): `lz_sum_idx64` self 0.38 s (40.0%), `spmv_baseline` self 0.39 s (41.1%), `shoup_mul` self 0.12 s (12.6%). Sampling precision 0.01 s; **not** an optimized-production profile. Historical native 44-bit IC profile had SpMV 67.8% self Ir *before* the linalg rewrite and cannot stand in for a new native profile. The gather helper was the hottest individually named not-yet-tested local helper; not asserted to be the current hottest native function.

## Frozen candidate

Only the inner gather helper differs. For lengths 0–8, return the explicitly unrolled sum `v[p[0]] + ... + v[p[n-1]]` (with independent subexpression grouping), and for lengths above 8, delegate to the unchanged `lz_sum_idx64`. The candidate changes no modular arithmetic formula, group-operation count, curve or RNG input. Test harness uses deterministic SplitMix64 seed `0x5d7e9d98144`; mostly ±1 coefficients, with nonunit terms as in the original light-row extraction. This candidate is **not** applied to `src/linalg.c`.

## Measurement and validation

Linux Xeon Platinum 8573C VM; GCC 14.2, `-O3 -march=x86-64`, `taskset -c 0`; shared, unisolated CPU. Four fixtures, each 8 `BC/CB` paired runs, 2,000 iterations/process, separate processes per arm: 64 benchmark processes. Eight identical-baseline `B/B` pairs provide 16 additional control processes; **80 total timed processes**. Each process runs both paths against an independent modulo-`q` row oracle and byte-identical output comparison before timing. All 80 passed those checks. ASan+UBSan differential suite: 22/22 configurations passed, 11/11 baseline/candidate fingerprints identical. Paired C/B geometric CPU-time ratios; lower means faster; 10,000 paired bootstrap resamples, seed 20261118, *descriptive* 95% intervals.

| Fixture | Baseline median CPU ns/row | Candidate median CPU ns/row | Paired C/B (95% bootstrap) | Whole extracted-process C/B |
|---|---:|---:|---:|---:|
| 1290×716, width=8, q=17592186044399 | 4.233 | 4.178 | 0.978 [0.881, 1.089] | 1.006 |
| 1290×716, width=4, same q | 3.152 | 3.555 | **1.122 [1.085, 1.150]** | 1.100 |
| 1024×65536, width=8, q=72057594037925687 | 6.847 | 6.412 | 0.957 [0.909, 1.017] | 0.962 |
| 1290×716, width=12, 44-bit q | 5.180 | 5.612 | 1.090 [0.996, 1.200] | 1.041 |
| Baseline/Baseline, width=8, 44-bit | 4.226 | — | **0.932 [0.888, 0.980]** | 0.934 |

**Verdict:** The intended short-row workload regressed about 12.2% in the local CPU metric, and the A/A control's interval *excludes 1* despite identical code, revealing drift or uncontrolled host bias. No improvement survived a reliability gate; **do not retain candidate or update a benchmark leaderboard**. The process ratio is the synthetic probe executable, **not end-to-end IC**. This does not establish anything about real-size curve hardness.

## Provenance and commands

- Upstream baseline commit: `6b64ee6ca07f92db014cf24d277439730ac31f4b`; blob: `39253dbaf80aa0fa2ad132507a83d7ec1f9eae04`.
- Probe source SHA-256: `51da1d57a497729045de36911d7f188f251a44cff1e73d5cdb59e2ea7b2403c6`.
- Optimized binary SHA-256: `1a1e0364f155d611a77c8c44da8c0273218fb75d33d77c8479287957eff9bfa9`.
- Raw 80-process panel SHA-256: `f66cd246931898410c3f821ab28e513ca5a7e23d94e64eeec4f88a92b8534650`.
- Summary SHA-256: `ac03371812b6d8b08e4d2b4ad5d83aeb3c64795eeae6fbf8f8c80c5c304e5b3d`.
- Raw profiles: `profile_B_gprof.txt`, `profile_C_gprof.txt` and `gmon.out` files in the frozen conversation evidence bundle `profile_20261118_lzshort.tar.gz`; this PR references but **does not store** that full bundle. The bundle also contains `spmv_probe.c`, `run_panel.py`, `analyze.py`, `validate.py`, `COMMANDS.txt`, all subprocess records, manifest, raw sanitizer outcomes, host details, fingerprints and 10,000-resample analysis.

From the evidence bundle directory:
```sh
gcc -std=c11 -O3 -Wall -Wextra -Werror -march=x86-64 -o spmv_probe spmv_probe.c
python3 run_panel.py > raw/run_panel.stdout 2> raw/run_panel.stderr
python3 analyze.py | tee raw/analyze.stdout
gcc -std=c11 -O1 -g -fsanitize=address,undefined -fno-omit-frame-pointer -Wall -Wextra -Werror -march=x86-64 -o spmv_probe_asan spmv_probe.c
python3 validate.py > raw/validate.stdout 2> raw/validate.stderr
gcc -std=c11 -O2 -g -pg -fno-inline -Wall -Wextra -Werror -march=x86-64 -o spmv_probe_pg spmv_probe.c
(cd raw && taskset -c 0 ../spmv_probe_pg 1290 716 8 120000 B 17592186044399 > profile_B_output.json && mv gmon.out profile_B_gmon.out)
gprof -b spmv_probe_pg raw/profile_B_gmon.out > raw/profile_B_gprof.txt
(cd raw && taskset -c 0 ../spmv_probe_pg 1290 716 8 120000 C 17592186044399 > profile_C_output.json && mv gmon.out profile_C_gmon.out)
gprof -b spmv_probe_pg raw/profile_C_gmon.out > raw/profile_C_gprof.txt
```

## Remaining blockers and next discriminating step

This runtime had no workspace checkout (`/workspace/isogeny-workspace` absent), git transport DNS, Conductor `conductor_check_conflicts → coord_start_work` actions, native isolated runner, or full target-descent IC execution; no native end-to-end cost, independently verified discrete-log target, matched rho accounting, or PCC signed verdict. GitHub PR-title search found no current open `lz_sum_idx64` PR, but **that is not a substitute for Conductor coordination**. The artifact/PR is a negative-result report only; upstream production code remains unchanged.

Next run should first obtain Conductor work claim, then a frozen native 44/56-bit IC baseline with complete phases and verified target; profile with Callgrind or hardware sampling on an isolated host, enforce stable A/A plus a positive timing control, and select a distinct unclosed optimization. No speculative optimization should be retained without native end-to-end nonregression.
