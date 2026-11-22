# 2026-11-18: four-accumulator Lanczos gather — REJECTED [pcc:unverified]

**Negative result; report-only PR. No production source changes, no leaderboard entry, no ECDLP speedup claim.** Profiling and timing below are unisolated, local **extracted-only** diagnostics, *not* the full native cryptanalytic workload. Exact scripts, gprof captures, per-process clocks, sanitizer logs, and binaries are preserved in the conversation attachment `profile_20261118_fourchain.tar.gz`; it is **not** a repository or S3 artifact.

## Baseline, closure and preregistered hypothesis
- Repo: `isogeny-labs/cryptanalysis` `main` commit `6b64ee6ca07f92db014cf24d277439730ac31f4b`. Exact `src/linalg.c` blob SHA `39253dbaf80aa0fa2ad132507a83d7ec1f9eae04`.
- Extracted exact production `lz_sum_idx64` **two** accumulator gather and the light, unscaled SpMV `spmv_body` path into a standalone harness. Original source is untouched. Candidate only replaces the gather helper with **four independent unsigned 64-bit sum chains**; four loads/loop and tail handling are retained. Both arms share matrix, coefficients, output buffer, compiler, and a fixed input generator.
- Historical upstream 2026-11-12 native profile found sparse SpMV 67.8% of instruction reads **before** the optimized kernel rewrite; the optimized revision already has two-chain 64-bit gather and light/heavy splitting (`docs/perf/20261112-tet-ca-indexcalc-linalg.md`). Prior extracted tests rejected next-row prefetch and short 0..8 switch dispatch (PR #1776); historic 128-bit unroll was also rejected. This is not relabelled as an ECDLP algorithmic discovery.
- **Preregistered hypothesis**: using four independent chains reduces CPU ns/row for the 44-bit 1290×716, width8 near-unit matrix without any output change. **Falsify** on correctness failure, primary benefit indistinguishable from noise, secondary regression, host drift, or missing native cold end-to-end nonregression. The end-to-end retention gate must pass before source can be changed; it was not runnable here.

## Profile first, target selection (gprof -O2 -pg -fno-inline)
Fresh local extraction only: 90,000 passes of 1290×716 width8, with 0.01-second gprof sample resolution:
- Baseline `lz_sum_idx64`: **0.23s / 36.92%** of 0.61s sampled, with 116,101,290 helper calls. Wrapper `spmv_baseline`: 0.13s/21.33%; `shoup_mul`: 0.10s/16.41%.
- Candidate `lz_sum_idx64_four`: **0.24s / 37.53%** of 0.64s sampled. Profile builds are not identical to optimized timing builds; do not extrapolate these percentages to whole native IC.

## Frozen protocol
- Machine: Xeon Platinum 8573C, Linux 6.18.57, GCC 14.2.0. `-O3 -march=x86-64` timed build, single pinned CPU 0 but **no single-tenant isolation**. Synthetic fixture generation: SplitMix64 seed `0x5d7e9d98144`, approximately 92% ±1 coefficients, other 8% in {2,3,4}; all light-row 64-bit accumulator bounds enforced.
- Four fixtures: `1290x716` width8/4/12 q=`17592186044399` (44-bit), and `1024x65536` width8 q=`72057594037925687` (56-bit). Matrix and vector construction are identical per arm. The 1290×716 matrix **matches only dimensions/approximate density** of prior actual 44-bit native work, not its exact entries.
- 12 alternated BC/CB **independent-process pairs per fixture**, 20,000 SpMV rounds per process; plus 12 B/B control pairs. Total **120 timed subprocesses** (96 B/C + 24 B/B). All children first check original **and** candidate against an independent `%q` row oracle and bytewise equality. Additional **22/22 ASan+UBSan configurations pass** and 11/11 B/C fingerprints agree, including zero unit-length rows.
- Primary outcome: geometric mean of 12 paired CPU ns/row C/B ratios (less than 1=faster), 10,000 paired bootstrap resamples, seed 20261118. Descriptive percentile 95% intervals, **not** independent confidence guarantees. Whole subprocess wall is startup+fixture+standalone SpMV, **not** full IC end-to-end. Every individual command, process and CPU time, seed and checksum exists in the conversation bundle.

## Empirical timings [pcc:unverified]

| Extracted fixture | B median CPU ns/row | C median CPU ns/row | paired C/B [descriptive 95%] | whole subprocess wall C/B |
|---|---:|---:|---:|---:|
| 1290×716 width8, 44-bit | 4.566 | 4.506 | **0.977** [0.908,1.051] | 0.982 |
| 1290×716 width4, 44-bit | 3.197 | 3.450 | **1.090** [1.042,1.141] | 1.098 |
| 1024×65536 width8, 56-bit | 6.041 | 6.229 | **1.038** [1.010,1.068] | 1.031 |
| 1290×716 width12, 44-bit | 5.635 | 5.615 | **1.022** [0.977,1.071] | 1.025 |
| baseline/baseline control (same 44-bit width8) | 4.539 | — | **0.920** [0.674,1.106] | 0.996 |

The primary 44-bit apparent 2.3% gain **does not exclude unity**. Width4 and 56-bit width8 regressed. The A/A control had strong perturbation (one pair ratio ~0.189), so host drift further limits inference. No change retained. All 120 timed processes had successful pre-timing differential/oracle checks; tests are local self-checks, not independent replay.

**Raw paired CPU ratios (12 per case, order as measured):**
- 44-bit width8: `0.77764,1.08614,1.01225,0.99654,0.84837,0.89929,0.83006,1.26969,1.02601,1.04118,1.04202,0.98982`
- 44-bit width4: `1.09731,1.12898,1.18404,0.97475,1.21517,0.98691,1.06304,0.98586,1.04749,1.22446,1.17942,1.03625`
- 56-bit width8: `1.04730,1.02322,1.10076,0.98869,1.15115,0.98920,0.98789,1.06175,1.09608,1.02995,0.97520,1.01563`
- 44-bit width12: `0.89693,1.07253,1.10431,1.00219,1.07561,1.02926,0.92960,0.94965,1.00349,1.04090,0.96852,1.22685`
- A/A: `1.29035,1.04286,0.99727,0.94466,1.12381,1.03729,0.97480,1.10129,1.00231,0.99491,0.18895,1.22410`

## Exact replay commands

```sh
gcc -std=c11 -O3 -Wall -Wextra -Werror -march=x86-64 -o spmv_probe spmv_probe.c
gcc -std=c11 -O1 -g -fsanitize=address,undefined -fno-omit-frame-pointer -o spmv_probe_asan spmv_probe.c
gcc -std=c11 -O2 -pg -fno-inline -o spmv_probe_pg spmv_probe.c
python validate.py
(cd raw && ../spmv_probe_pg 1290 716 8 90000 B 17592186044399 >profile_B_output.json && mv gmon.out profile_B_gmon.out && gprof ../spmv_probe_pg profile_B_gmon.out >profile_B_gprof.txt)
(cd raw && ../spmv_probe_pg 1290 716 8 90000 C 17592186044399 >profile_C_output.json && mv gmon.out profile_C_gmon.out && gprof ../spmv_probe_pg profile_C_gmon.out >profile_C_gprof.txt)
python run_panel.py && python analyze.py
# Per timed subprocess: taskset -c 0 ./spmv_probe ROWS COLS WIDTH 20000 B_or_C q
```

Source SHA256 `cb934e0af41c56335aa0827a3604b487d470b0a2971b6847d9df54842813fc91`; optimized binary SHA256 `ec257a15a3271035491d8f224950725d0ee2e3e7faa45493fa09326b49069a9c`; full `raw/panel.jsonl` SHA256 `9c4d5e5603ff74ff04fc0bc3e20527848a82c15c9c4174af64997e932db70c50`; summary SHA256 `19b4d1a7889acff39e56b354e7f5060d7a841fd40473c052edda7ceeb6f1ac65`. Hashes do **not** constitute a signed execution proof.

## Gaps and next action
No `/workspace/isogeny-workspace`, Conductor `conductor_check_conflicts → coord_start_work`, S3 checkpoint, isolated runner, native whole-IC relation collection/matrix/solver/descent, matched rho, independent replay or signed PCC verification accessible. Therefore no production optimization or ECDLP speedup claim is permitted. Retain the previous exact baseline. **Next:** coordinate and capture the full current native `lz_spmv` profile, with stable A/A and positive controls, then optimize a previously unclosed hotspot and prove cold IC end-to-end nonregression before retention.