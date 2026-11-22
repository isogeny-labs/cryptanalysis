# R8 2026-11-19: unroll two nonunit light-row terms — REJECTED [pcc:unverified]

**Verdict:** Do not retain the candidate. Exact baseline pinned to `isogeny-labs/cryptanalysis` main `6b64ee6ca07f92db014cf24d277439730ac31f4b`, `src/linalg.c` blob `39253dbaf80aa0fa2ad132507a83d7ec1f9eae04`. No production source change is proposed. This is only a **synthetic standalone extracted light-row SpMV** diagnostic, **not** full native IC, an ECDLP solve, ECC2K130, or independently verified execution.

### Profile and one bounded candidate

Fresh baseline-only `gcc -O2 -pg -fno-inline` gprof on q56 1024×65536 width8 57% nonunit, 90,000 rounds, CPU0: 0.92 sampled CPU seconds (10ms resolution). `spmv_baseline` 48.96% sampled self, including the nonunit loop (its individual fraction is **not** isolated); `lz_sum_idx64` 39.71% (already optimized), `shoup_mul` 9.79%. These are **extracted function percentages, not current native IC workload fractions**.

Candidate changes exactly the nonunit coefficient loop (original: one term `u += (uint64_t)oval[t-idx]*vv[*t]` per iteration) to compute two successive products `a`, `b`, then `u += a+b` in one accumulator update with one-term tail. Same rows/coefficients/index order, lz_sum_idx64, q and Shoup. Previous R1–R7 rejected other schemes; not re-tested here. Source/scripts and disassembly in the archive below.

### Frozen fixtures, correctness and method

GCC 14.2, `-O3 -std=c11 -Wall -Wextra -Werror -march=x86-64`; AMD EPYC 9V74, 5 visible KVM vCPUs, one NUMA node, child affinity CPU0. Synthetic SplitMix64 seed `0x5d7e9d98144` with coefficient magnitudes 2–4 and bounded `width*5*q < 2^64`. q44=`17592186044399`; q56=`72057594037925687`. Fresh baseline and candidate compiled in **one** translation unit. Baseline function byte-for-byte the extracted upstream loop; no `src/linalg.c` patch. Row reference oracle computes per-term direct `%q`.

**22/22** GCC ASan+UBSan differential children passed; **11/11** baseline/candidate fingerprints match; **160/160** timed subprocesses validated every row against independent in-process oracle and B/C byte match before timing; 0 timeouts/exclusions/errors. Four fixtures × 16 alternated BC/CB paired runs + 16 B/B baseline-control pairs = 160 subprocesses and 80 pairs. Each process runs 20,000 SpMV iterations. 10,000 pair-bootstrap seed 20261119 resamples; descriptive 95% intervals, **not** corrected for VM contention.

| Fixture | B CPU ns/row median | C CPU ns/row median | Paired C/B CPU [95% bootstrap] | Whole-child wall C/B [95%] | Pairs |
|---|---:|---:|---:|---:|---:|
| **Primary q56, 1024×65536 w8, 57% nonunit** | 7.4873 | 7.2442 | **0.96736 [0.93505, 1.00078]** | 0.96831 [0.93664, 1.00104] | 16 |
| q44, 1290×716 w8, 57% nonunit | 5.1410 | 5.1019 | 0.99464 [0.95684, 1.02637] | 0.99375 [0.95508, 1.02467] | 16 |
| q44, 1290×716 w8, 8% nonunit | 4.0540 | 4.2339 | **1.05221 [1.02435, 1.07948]** | 1.04999 [1.02210, 1.07637] | 16 |
| q56, 1024×65536 w12, 57% nonunit | 12.000 | 11.3241 | 0.92094 [0.87476, 0.96619] | 0.91968 [0.87283, 0.96334] | 16 |
| **B/B control, primary identical baseline** | 7.588 | N/A | 0.98054 [0.95730, 1.00263] | 0.98111 [0.95825, 1.00301] | 16 |

Primary 95% interval crosses 1; mostly-unit secondary case **regresses by 5.22%**. B/B ratio 0.981 (interval includes unity) signals timing drift. Width12 gain cannot override the primary and secondary gates. **Reject. No code retained.** All measurements are producer-reported [pcc:unverified].

### Reproducibility and unresolved acceptance gates

Archive: `profile_20261119_run8.tar.gz`, SHA-256 **`564c1c6898dd33249209f021fe840805c30d262504b298c50e2d27206e603dd6`** (attached to chat, not durable S3). Exact source/test drivers, `PROTOCOL.md`, `COMMANDS.txt`, `pairs.csv` (80 raw paired CPU/wall observations), all 160 per-process command/stdout/stderr/wall records in `raw/panel.jsonl` (SHA-256 `0f780205a9c66cd3cea785cd0af8c3cab0f6e3e7e65ffd2731ccc098603634fb`), `raw/summary.json`, 22 sanitizer logs, `raw/profile_B_gprof.txt`, binary `raw/profile_B_gmon.out`, `raw/objdump_spmv_full.txt`, toolchain, hardware, all input seeds, `raw/SHA256SUMS`.

Executed commands:
```bash
gcc -std=c11 -O3 -Wall -Wextra -Werror -march=x86-64 -o spmv_probe spmv_probe.c
gcc -std=c11 -O1 -g -fsanitize=address,undefined -fno-omit-frame-pointer -o spmv_probe_asan spmv_probe.c
gcc -std=c11 -O2 -pg -fno-inline -o spmv_probe_pg spmv_probe.c
(cd raw && taskset -c 0 ../spmv_probe_pg 1024 65536 8 90000 B 72057594037925687 57 > profile_B_output.json && cp gmon.out profile_B_gmon.out && gprof ../spmv_probe_pg gmon.out > profile_B_gprof.txt)
python3 validate.py > raw/validate.stdout 2> raw/validate.stderr
python3 run_panel.py > raw/run_panel.stdout 2> raw/run_panel.stderr
python3 analyze.py > raw/analyze.stdout 2> raw/analyze.stderr
```

**Unmet original deliverable:** Native current-workload profile and matched same-input full cold collect→LA→descent→verification end-to-end regression, plus independent signed PCC verification. No workspace/Conductor claim endpoint or GitHub DNS from compute container, real relation matrices, S3 access, or isolated native runner. This PR is ready-for-review **negative-result documentation only**, not production code or a leaderboard speedup. Next discriminating step: obtain real native matrices/profile with stable A/A and positive controls and matched rho before another kernel change. [pcc:unverified]
