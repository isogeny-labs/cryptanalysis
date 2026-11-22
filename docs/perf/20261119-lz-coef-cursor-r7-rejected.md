# R7: light-row coefficient cursor — REJECTED [pcc:unverified]

**Verdict: REJECT. No production source changed. No end-to-end speedup claim.** This is a fresh synthetic standalone SpMV extraction, not current native `ca ic` or ECC2K130. Execution, timings and correctness are producer-reported only. [pcc:unverified]

## Frozen baseline and new profile
Pinned `main` `6b64ee6ca07f92db014cf24d277439730ac31f4b`; `src/linalg.c` blob `39253dbaf80aa0fa2ad132507a83d7ec1f9eae04`. The baseline is the exact unscaled 64-bit light-row branch extracted from `spmv_body` with original two-chain `lz_sum_idx64` and original Shoup reduction; heavy rows and scaled D/DR are *excluded*. Previous R1–R6 extracted gather/prefetch/hoist/Shoup/two-chain nonunit changes were rejected, so this is a distinct one-loop candidate.

Fresh baseline-only `gcc -O2 -pg -fno-inline` `gprof`, q56=72057594037925687, 1024x65536 width8, 57% nonunit, 90000 rounds, CPU0: `lz_sum_idx64` 39.51% self (already optimized); `spmv_baseline` 39.51% self, including target unoptimized nonunit loop; `shoup_mul.constprop.0` 11.85%. 0.76s total sampled in 0.01s ticks. **This is not a native IC hotspot ranking**.

## One bounded change, preregistered before timing
Replace `oval[t-idx]` inside the 64-bit nonunit loop with an aligned `coef=oval+u0` cursor incremented alongside `t`, leaving operations, order, matrix data, unit gather, Shoup, and all other code fixed. Hypothesis: reduce primary CPU ns/row without changing residues. Detailed [pre-committed protocol](20261119-lz-coef-cursor-r7-protocol.md); local `PROTOCOL.md` SHA-256 `bc3b24cc3f7a91e3b8bcbd5544bf26e2ae3bd055df3b873aa85486a07528bee4`; candidate C and baseline B source SHA-256 `ac3035cbd96fbd8a5c31fcc4a6e5c9ef20a0b35bdfd58ba98bab635b77847ab8`.

## Measurements [pcc:unverified]

| Synthetic case | B median CPU ns/row | C median CPU ns/row | C/B paired CPU geometric ratio [95% paired bootstrap] | C/B full child-process wall [95% bootstrap] | N pairs |
|---|---:|---:|---:|---:|---:|
| **Primary** q56 1024x65536 w8, 57% nonunit | 7.726 | 8.567 | **1.1062 [1.0618, 1.1600]** | 1.1045 [1.0602, 1.1560] | 12 |
| q44 1290x716 w8, 57% nonunit | 5.461 | 5.821 | 1.0702 [1.0274, 1.1134] | 1.0710 [1.0291, 1.1146] | 12 |
| q44 1290x716 w8, 8% nonunit (92% ±1) | 4.039 | 4.554 | 1.1091 [1.0673, 1.1497] | 1.1071 [1.0636, 1.1483] | 12 |
| q56 1024x65536 w12, 57% nonunit | 10.260 | 10.529 | 1.0167 [0.9905, 1.0355] | 1.0124 [0.9868, 1.0326] | 12 |
| B/B same-baseline A/A | 7.577 | — | 0.9944 [0.9779, 1.0096] | 0.9923 [0.9744, 1.0094] | 12 |

**Correctness and sampling:** 22/22 ASan+UBSan independent child tests, 11/11 B/C fingerprints; 120/120 timed subprocesses each checked all output rows against a separate `%q` per-term oracle before timing, then bytewise B/C equality. All successful; no hidden failures. 4 cases x 12 alternating BC/CB pairs x 2 arms + 12 B/B pairs x 2 = 120 children, each 20,000 SpMV rounds; seeded SplitMix64 `0x5d7e9d98144`. 10,000 fixed-seed paired bootstrap resamples are **descriptive**, not adjusted for shared-host interference. All 60 pair CPU and wall ratios in [paired raw values](20261119-lz-coef-cursor-r7-pairs.csv). Original 120 subprocess stdout/commands/wall/CPU JSONL, sanitizers, full gmon, gprof, disassembly, compiler binaries, and SHA256SUMS preserved in conversation archive `profile_20261119_run7.tar.gz` SHA-256 `74303021f1c71b1ee020e707efe54926f260fa5a8f958049d0ba23c2ec47cbd0` (not S3).

**Environment and replay:** AMD EPYC 9V74 KVM 5-vCPU shared VM, Linux 6.18.57, gcc 14.2.0, Python 3.13.5, CPU0 pinned. `gcc -std=c11 -O3 -Wall -Wextra -Werror -march=x86-64 -o spmv_probe spmv_probe.c`; `gcc -O1 -g -fsanitize=address,undefined -fno-omit-frame-pointer -o spmv_probe_asan spmv_probe.c`; `gcc -O2 -pg -fno-inline -o spmv_probe_pg spmv_probe.c`; `python3 validate.py`; `(cd raw && taskset -c 0 ../spmv_probe_pg 1024 65536 8 90000 B 72057594037925687 57 && gprof ../spmv_probe_pg gmon.out > profile_B_gprof.txt)`; `python3 run_panel.py && python3 analyze.py`. Script hashes/commands in local bundle.

**Rejection:** Primary CPU C/B >1 with 95% descriptive interval fully above 1, plus q44 regressions. A/A includes 1. No code retained. Whole-process *synthetic child* timing is not end-to-end IC. Unmet: `/workspace/isogeny-workspace`, Conductor `conductor_check_conflicts`/`coord_start_work`, S3, real relation matrices, full cold native collect→LA→descent→verification including positive controls and matched rho, independent PCC standing. No production merge permitted; report-only negative-result record. Next: native claimed isolated profile on real 44/56-bit IC before new hotspot selection. [pcc:unverified]
