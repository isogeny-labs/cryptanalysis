# Sparse Lanczos Shoup final correction — R5 extracted diagnostic (2026-11-18)

**Verdict: REJECTED, report-only PR.** No production optimization retained. All measurements are self-reported **[pcc:unverified]**. This is an unisolated synthetic prime-field extracted SpMV test, **not** a native index-calculus, ECC2K130, or end-to-end ECDLP experiment.

## Pinned baseline / closure audit

Repository `isogeny-labs/cryptanalysis` at `main` commit `6b64ee6ca07f92db014cf24d277439730ac31f4b`; exact `src/linalg.c` blob SHA `39253dbaf80aa0fa2ad132507a83d7ec1f9eae04`. The unchanged baseline `lz_sum_idx64`, `shoup_mul`, and unscaled light-row `spmv_body` path were extracted into the test source. Historical native profiles and closure decisions: [2026-11-12 optimized linear algebra](../perf/20261112-tet-ca-indexcalc-linalg.md); earlier extracted-only rejected candidates: PR #1776 (short-row), #1777 (four-chain), #1780 (bound-hoist), and prefetch. Those changes were **not** repeated. No claim is made that the extraction is today's native hotspot.

A **fresh local extracted-only** baseline profile, `gcc -O2 -pg -fno-inline` for 90,000 rounds of 1290×716 width8, saw 0.49s sampled: `lz_sum_idx64` 0.21s / 41.87% self, `spmv_baseline` 0.18s / 36.77%, and `shoup_mul.constprop.0` 0.09s / 18.38%, 116.1m Shoup calls. Gprof has 10ms granularity and a different build than the benchmark. The gather is already optimized and repeatedly tested; the Shoup reduction is the next **distinct** hot helper for this standalone extraction.

## Frozen hypothesis and ONE bounded candidate

Change **only** Shoup's final correction from
`return r >= q ? r-q : r;` to `return r - (q & ((uint64_t)0 - (uint64_t)(r >= q)));`.
Keep the exact `qhat = high64(a*wp)`, `r=a*w-qhat*q`, `w=1`, existing two-chain gather, vectors, synthetic matrix, input generator, seed and independent row oracle. Hypothesis: branchless correction improves CPU ns/row for the primary 44-bit sparse matrix without changing outputs. Candidate is in test source **only**.

**Pre-registered falsification / retention gate:** reject if any differential/UBSan/ASan failure; paired-bootstrap primary 95% interval not entirely < 1; secondary regression or unstable A/A; or lack of independent native same-target cold IC end-to-end nonregression. Full native gate is **BLOCKED**, not passed, so upstream source remains unchanged regardless of microbench result.

## Inputs / execution [pcc:unverified]

- GCC 14.2.0, AMD EPYC 9V74 KVM, Linux 6.18.57, CPU affinity 0, **shared unisolated host**. Benchmark `gcc -std=c11 -O3 -Wall -Wextra -Werror -march=x86-64`. Both compiled arms inside same binary.
- Synthetic SplitMix64 `0x5d7e9d98144`, ~92% ±1 and other coeffs 2–4. Primary 1290×716 width8, `q=17592186044399`; secondary same dimensions width4 and width12, and 1024×65536 width8, `q=72057594037925687`. Light-row bound checked; no native relation matrix.
- Per fixture, 12 BC/CB fresh-process pairs (20,000 SpMV rounds/child), plus 12 B/B A/A process pairs: **120 timed children**. In each child both arms first pass a separate `%q` per-row oracle and byte-for-byte output comparison.
- **22/22** ASan+UBSan child runs and **11/11** baseline/candidate checksum pairs passed; all 120 timed children passed internal row oracle/bytewise checks. Additional **1,400,000** UBSan w=1 Shoup baseline/candidate/`a%q` comparisons over seven moduli passed. Independent PCC signature absent.
- CPU ns/row and total process wall; geometric C/B ratio for paired processes (<1 faster), percentile descriptive 95% bootstrap using 10,000 paired resamples and seed 20261118. Shared-host drift and resource contention remain uncontrolled.

## Measured results [pcc:unverified]

| Fixture | Baseline median CPU ns/row | Candidate median CPU ns/row | C/B CPU paired [95% interval] | C/B whole child wall [95% interval] |
|---|---:|---:|---:|---:|
| **Primary** 44-bit width8 | 3.808 | 3.808 | **1.0026 [0.9871, 1.0195]** | 0.9984 [0.9791, 1.0176] |
| 44-bit width4 | 2.835 | 2.816 | 0.9864 [0.9472, 1.0255] | 0.9867 [0.9491, 1.0236] |
| 56-bit wide vector width8 | 5.949 | 5.948 | 1.0097 [0.9915, 1.0267] | 1.0097 [0.9923, 1.0264] |
| 44-bit width12 | 4.820 | 4.816 | 1.0073 [0.9556, 1.0713] | 1.0084 [0.9593, 1.0707] |
| B/B A/A control | 3.748 | — | 0.9940 [0.9812, 1.0091] | 0.9944 [0.9814, 1.0097] |

**All intervals include 1. No demonstrated improvement; reject candidate.** Both shapes compiled to conditional moves on this host. This benchmark does **not** count IC relation yield, rank, collector, linear algebra setup, descent, total cost, or a rho reference. No end-to-end speedup claim.

## Reproducibility and limitations

Full conversation-side archive: `profile_20261118_run5.tar.gz` SHA-256 `453fd945c5429e17f1bed31d0fb8bbee1a9ee82e63ee10178fc1102fa6d99ea0`. It includes frozen `PROTOCOL.md`, `spmv_probe.c`, `shoup_arith_verify.c`, `run_panel.py`, `analyze.py`, `validate.py`, `COMMANDS.txt`, host/compiler manifest, original 120-process `raw/panel.jsonl`, `raw/summary.json`, all tests/output, `pairs.csv`, original `raw/profile_B_gmon.out`, `gprof` printout and `objdump` extraction. This archive was **not** pushed to S3 or to this GitHub PR. A reproducibility bundle hash is not a signed execution receipt.

Selected SHA-256: protocol `b1eaf15602ab757b3d04546db72c73df013bd2906d3f6796b4ba15f0370788a1`; test source `88824b2761d19a255335a2b8d51274936f8e149d987cc517a1a0f0a1b72f70b8`; timed executable `8a913d72a7c643969051b8b1360a935afe0bc7b37b98e6f11dc1142fab1db9bd`; raw panel `198a318a28b5f977f856c1a92a61343258a61a178d4074b99f85205d9b2cdae0`; summary `db853bb887143141871f8ee0709a47457832d97214c8ab8ce2225184301539c4`; gmon `92ef42d3fdde6908f97d332063eaaf914061912a7fd34f3e1d3f74f134bed6f8`; pairs CSV `6d7a38b9e0336ce65ef25db602b1ddac6186ee34deafac0031d25a738525de84`.

Commands from archive:
```sh
gcc -std=c11 -O3 -Wall -Wextra -Werror -march=x86-64 -o spmv_probe spmv_probe.c
gcc -std=c11 -O1 -g -fsanitize=address,undefined -fno-omit-frame-pointer -o spmv_probe_asan spmv_probe.c
gcc -std=c11 -O2 -pg -fno-inline -o spmv_probe_pg spmv_probe.c
python3 validate.py
(cd raw && taskset -c 0 ../spmv_probe_pg 1290 716 8 90000 B 17592186044399 && gprof ../spmv_probe_pg gmon.out >profile_B_gprof.txt)
python3 run_panel.py && python3 analyze.py
gcc -std=c11 -O1 -g -Wall -Wextra -Werror -fsanitize=undefined -fno-omit-frame-pointer shoup_arith_verify.c -o shoup_arith_verify && ./shoup_arith_verify
```

Access blocker: no `/workspace/isogeny-workspace`, outbound GitHub DNS unavailable, Conductor `conductor_check_conflicts` / `coord_start_work` not exposed, no EKS isolated runner, S3 uploader, native CMake `ca ic` cold pipeline, or signed PCC verifier. This is a **report-only** PR through the authenticated GitHub connector. No producer source edits, leaderboard row or signed speedup.

**Next:** use official `bin/ws route` then `bin/ws need` and Conductor claim on native runner, profile *current* cold 44/56-bit IC and genuine relation matrices with stable A/A plus positive controls; then select an unclosed native hotspot, verify target and cold total cost independently, and compare against matched rho.
