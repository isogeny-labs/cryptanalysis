# R6 — 2026-11-18 light-row nonunit accumulator, REJECTED [pcc:unverified]

**No production source changes.** This is a local, unisolated, extracted-kernel diagnostic. It is NOT a native `ca ic` run, a cold end-to-end ECDLP result, a genuine relation matrix, or independent verification. No optimization retained.

## Baseline, source, hotspot, closure

- `isogeny-labs/cryptanalysis` `main` **`6b64ee6ca07f92db014cf24d277439730ac31f4b`**, unchanged exact `src/linalg.c` blob `39253dbaf80aa0fa2ad132507a83d7ec1f9eae04`. Baseline light-row nonunit loop and `lz_sum_idx64` / `shoup_mul` faithfully extracted; all other changes confined to a standalone local C diagnostic, NOT upstream.
- Native historical pre-optimization 2026-11-12 Callgrind: SpMV 68% and 78% of instructions for 44/56-bit IC. **Not a contemporary native profile.** [Source](https://github.com/isogeny-labs/cryptanalysis/blob/main/docs/perf/20261112-tet-ca-indexcalc-linalg.md). R1–R4 gather optimizations and R5 Shoup correction rejected. Earlier rejected *128-bit heavy-row* unroll differs from this candidate's *64-bit light-row nonunit* loop.
- **Fresh extracted-only B-arm gprof**, q56 / 1024×65536 / width8 / 57% nonunits / 90000 SpMV rounds: `lz_sum_idx64` (previously optimized) 0.33/0.74 s (43.37% self); `spmv_baseline` 0.27/0.74 s (36.03% self, includes unoptimized nonunit accumulation); `shoup_mul.constprop.0` 0.13/0.74 s (16.68%). 10ms gprof sampling granularity. Chose an unoptimized hot region within `spmv_baseline`, **not** a certified hottest native function.

## Frozen hypothesis and protocol

Test one change: replace `for (t=ub; t<e; ++t) u += oval[t-idx] * vv[*t]` with a two-chain pair loop `a += oval[t-idx]*vv[t[0]]; b += oval[t+1-idx]*vv[t[1]]`, a final odd term, and `u += a+b`. All integers and outputs remain in unsigned light-row bounds. Do not change unit gather, Shoup, coefficients, other loops, layout or seed. Hypothesis: lower primary CPU ns/row and no other material regression.

- Fixed SplitMix64 seed `0x5d7e9d98144`. Primary q=72057594037925687, 1024 rows × 65536 columns, width8, 57% nonunit 2–4 coefficients. Secondary 44-bit q=17592186044399, 1290×716 width8 57% nonunit; same 44-bit geometry 8% nonunit (92% ±1, representative of actual matrix's coefficient mix); 56-bit width12 57% nonunit. **These are synthetic** and omit heavy-row/scaled `D` cases, real relation collector, sparse solve, descent and rho comparison.
- GCC 14.2.0, `-std=c11 -O3 -Wall -Wextra -Werror -march=x86-64`; AMD EPYC 9V74 KVM Linux 6.18.57 with 5 visible vCPUs / one NUMA node; `taskset -c 0`, shared host. 12 fresh-process alternating BC/CB pairs per fixture, 20,000 rounds per child; 12 B/B primary controls = **120 timed children**. In-process CPU and whole-process wall tracked separately. 10,000 paired bootstrap resamples seed 20261118, descriptive 95% percentile intervals, not shared-host inference.
- Before timing, **every child** evaluates both B and C, runs independent per-row modular `%q` oracle, and checks byte-for-byte output equality. 22/22 ASan+UBSan differential test children pass including 0% and 100% nonunit; 11/11 B/C fingerprints match; **120/120 timed** children passed self-checks. [pcc:unverified]

## Results (geometric paired C/B; lower is better) [pcc:unverified]

| Fixture | Median B CPU ns/row | Median C CPU ns/row | C/B CPU [bootstrap 95%] | C/B process-wall [bootstrap 95%] | n pairs |
|---|---:|---:|---:|---:|---:|
| **56-bit primary, width8, 57%** | 7.410 | 7.430 | **1.0166 [0.9993,1.0386]** | 1.0177 [1.0001,1.0392] | 12 |
| 44-bit width8, 57% | 4.848 | 5.119 | 1.0529 [1.0377,1.0710] | 1.0487 [1.0344,1.0667] | 12 |
| 44-bit width8, 8% | 3.768 | 4.402 | 1.1629 [1.1461,1.1824] | 1.1570 [1.1290,1.1840] | 12 |
| 56-bit width12, 57% | 10.637 | 10.194 | 0.9476 [0.9296,0.9674] | 0.9479 [0.9267,0.9721] | 12 |
| **B/B same-code control** | 7.554 | — | 1.0035 [0.9864,1.0229] | 1.0033 [0.9860,1.0239] | 12 |

**Reject:** primary CPU CI crosses unity; 44-bit secondary inputs regress 5.3% and 16.3%. Width12's ~5.2% extracted-only improvement does **not** justify acceptance: the primary target, crucial representative coefficient mix, and native end-to-end gate fail. **No candidate integrated.** No solve speedup or leaderboard update.

## Reproducibility and evidence boundaries

Local conversation bundle: `profile_20261118_run6.tar.gz`, SHA-256 **`09543071bc2e6207d203162a549227c131187578e2580becaef056bc064495f4`**. Includes `PROTOCOL.md` (pre-registration), exact `spmv_probe.c` B and C, `run_panel.py`, `analyze.py`, `validate.py`, `COMMANDS.txt`, `raw/host.txt`, complete 120-child JSONL, B/B results, per-child correctness logs, sanitizer logs, gprof text + original gmon, build binaries, metadata, hashes, 60-pair CSV and 10000-resample summary. **Local archive is not in this PR or in S3.**

Selected SHA-256: `spmv_probe.c` `0bee5bdd41a231e19a25478429c47cafc2a2385eb2ebd3926bc1de7999def931`; 120-child `raw/panel.jsonl` `fd5e4a6359aeecb74b8f8caf9f1e0142cf99da4807bfc7f0fc7ce1bf71aa37fb`; `raw/summary.json` `2bd49cba03703634981c2c793b5311edb2eb7db0380d47523fbdd2c41ae309a6`; gprof text `84bdfe65603fb9170109e421ab1470d6357eef3e3fd20399047ae0bc94295f4f`. Source, commands, measurements and profiles are pinned by the bundle; this PR is report-only.

Replay from extracted bundle:
```sh
gcc -std=c11 -O3 -Wall -Wextra -Werror -march=x86-64 -o spmv_probe spmv_probe.c
gcc -std=c11 -O1 -g -fsanitize=address,undefined -fno-omit-frame-pointer -o spmv_probe_asan spmv_probe.c
gcc -std=c11 -O2 -pg -fno-inline -o spmv_probe_pg spmv_probe.c
python3 validate.py
(cd raw && taskset -c 0 ../spmv_probe_pg 1024 65536 8 90000 B 72057594037925687 57 > profile_B_output.json && gprof ../spmv_probe_pg gmon.out > profile_B_gprof.txt)
python3 run_panel.py && python3 analyze.py
```

Native workspace `/workspace/isogeny-workspace` and Conductor `conductor_check_conflicts → coord_start_work` not exposed; container cannot reach GitHub DNS for cloning; no isolated worker, cold full `ca ic`, S3 checkpoint or independent signed PCC replay. These acceptance gates are **BLOCKED** rather than passed. Next: on the native workspace, run `bin/ws route` then `bin/ws need`, coordinate via Conductor, profile full IC with real matrices and paired cold pipeline checks, compare matched rho and independently verify. Preserve this negative experiment as **[pcc:unverified]**.