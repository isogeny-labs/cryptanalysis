# 2026-11-18 run 4: hoisted loop bound in sparse Lanczos gather — REJECTED

**Status: negative result, report only; no production change. All local measurements are [pcc:unverified].** This is an extracted-only experiment, not a validated cold index-calculus or ECDLP improvement. Signed PCC, native validation, matched rho and independent replay unavailable.

## Frozen source, prior findings and specific hypothesis

- Repository: `isogeny-labs/cryptanalysis`, baseline `main` commit `6b64ee6ca07f92db014cf24d277439730ac31f4b`; `src/linalg.c` blob `39253dbaf80aa0fa2ad132507a83d7ec1f9eae04`. Verified retrieved on this run. The exact existing `lz_sum_idx64` two-chain helper and light/unscaled `spmv_body` code were copied into a standalone probe, **not edited upstream**.
- The 2026-11-12 `docs/perf/20261112-tet-ca-indexcalc-linalg.md` baseline already includes unit-term gathering, two accumulation chains, light/heavy split. Prior local tests rejected next-row prefetch, short-row dispatch (#1776), and four chains (#1777); the prior 2026-11-12 bitwise tail variant also regressed. None repeated.
- **Pre-registered hypothesis:** hoisting the final complete group pointer, `last=e-4`, and using `p<=last` as the four-term loop continuation condition saves pointer-distance operations on unit-heavy sparse rows without changing any arithmetic, data layout, tail, or RNG. This tests a *loop-bound micro-optimization*, not a new cryptanalytic method. Frozen protocol and candidate source are in the local evidence bundle `profile_20261118_run4.tar.gz`.
- **Falsification/retention gates (frozen before testing):** both arms must be identical on every row and pass independent modular oracle and sanitizers; primary CPU ns/row ratio must have paired bootstrap upper bound <1; no material regression in secondary cells; A/A control must be stable; and full native cold IC must show no end-to-end regression. If any gate fails, **do not change production code**.

## Profile first — only the isolated extract

`gcc -O2 -pg -fno-inline`, 90,000 SpMV repetitions, 1290×716 with unit-heavy width 8 (gprof 0.01 s sampling granularity):

| symbol | baseline sample self | candidate sample self | observed calls |
|---|---:|---:|---:|
| `lz_sum_idx64` / `lz_sum_idx64_limit` | 0.19s, **39.62%** of 0.48s | 0.32s, **55.22%** of 0.58s | 116,101,290 per arm |
| `shoup_mul.constprop.0` | 0.09s, 18.77% | 0.04s, 6.90% | 116,102,580 per arm |

These are **separate extracted probe profiles** with profiler instrumentation; percentage denominators differ, and they are not representative profiles of full `ca ic` or directly comparable to `-O3` wall measurements. The original gather is the largest observed isolated self-time target. The candidate compiled but was slower in its own sampled profile.

## Exact fixture and test protocol

- Hardware: local shared host Xeon Platinum 8573C, Linux 6.18.57, GCC 14.2.0, CPU 0 affinity, **no isolation**. Benchmark `gcc -std=c11 -O3 -Wall -Wextra -Werror -march=x86-64`; sanitizer `-O1 -g -fsanitize=address,undefined -fno-omit-frame-pointer`; profiler `-O2 -pg -fno-inline`.
- SplitMix64 matrix/vector seed `0x5d7e9d98144`; approximately 92% ±1 and 8% other coefficients (2–4), generated identically in each child. All light-row arithmetic respects its 64-bit sum bound. This is a synthetic matrix with published IC-like dimensions, **not** the actual native IC input.
- Primary `ic44_1290x716`: 1290 rows × 716 columns, width 8, q=17592186044399. Secondary `short44_1290x716` width 4; `long44_1290x716` width 12; `wide56_1024x65536` 1024×65536, width 8, q=72057594037925687.
- 12 alternating BC/CB **fresh-process pairs per cell**, 20,000 full SpMV rounds per child; 12 baseline-baseline pairs for A/A; 96 B/C + 24 B/B = **120 timed subprocesses**. Every child ran both arms against an independently written `%q` reference for every row and then byte-for-byte compared them **before** timing. All 120 checked out.
- ASan+UBSan: **22/22** fixtures/arms completed; 11/11 baseline/candidate output fingerprints identical. No test failure discarded.
- Reported ratio = paired geometric mean of candidate/baseline *process CPU* ns/row. 10,000 paired bootstrap resamples, seed 20261118, 2.5/97.5 percentile descriptive intervals. Whole-subprocess wall recorded separately but is **not** end-to-end IC. Raw per-process argv, CPU and wall times, stdout/seed, failures, gprof captures and host metadata are preserved in the conversation reproducibility bundle.

## Measured results (candidate/baseline <1 faster)

| synthetic case | B median CPU ns/row | C median CPU ns/row | C/B paired geometric mean | descriptive bootstrap 95% |
|---|---:|---:|---:|---:|
| primary `ic44_1290x716` | 4.026 | 5.781 | **1.438** | [1.386, 1.494] |
| `short44_1290x716` | 2.905 | 3.511 | **1.189** | [1.133, 1.249] |
| `wide56_1024x65536` | 6.145 | 7.275 | **1.181** | [1.154, 1.208] |
| `long44_1290x716` | 4.817 | 7.030 | **1.500** | [1.458, 1.548] |
| A/A `control44_BB` | 3.781 | B/B | **1.023** | [0.995, 1.056] |

**Falsified.** Primary 43.8% regression plus all three secondary regressions; all descriptive C/B intervals entirely above unity. The A/A control interval includes unity, but the shared host remains unisolated and non-independent. Correctness is not the gate that failed; observed performance and absent native end-to-end testing fail the retention criteria. **No source change is retained** and no speedup is claimed [pcc:unverified].

## Exact replay and evidence provenance

The archive `profile_20261118_run4.tar.gz` (conversation artifact, not checked into this repo) includes `spmv_probe.c`, `PROTOCOL.md` frozen pre-timing, `validate.py`, `run_panel.py`, `analyze.py`, `COMMANDS.txt`, exact binaries, gprof and gmon outputs, `raw/panel.jsonl` (all 120 subprocess records), `raw/sanitizer_tests.json`, `raw/summary.json`, `raw/host.txt`, `raw/manifest.json`, stdout/stderr and SHA256 manifest. Archive SHA256: `2e8e4d68fac838135975bd39f28488c2434598916f40d86f1345a15d3d01c3d7`; `README.md` SHA256: `cbf125bdfb96fc9773de11268d28016b4fc6d6f29305b58354e38daba196e394`; `raw/summary.json` SHA256: `3156248693c11750ba8647c8dec0be7ec934af41a914be861bfede295a6cad84`. A hash does not attest execution.

```sh
gcc -std=c11 -O3 -Wall -Wextra -Werror -march=x86-64 -o spmv_probe spmv_probe.c
gcc -std=c11 -O1 -g -fsanitize=address,undefined -fno-omit-frame-pointer -o spmv_probe_asan spmv_probe.c
gcc -std=c11 -O2 -pg -fno-inline -o spmv_probe_pg spmv_probe.c
python3 validate.py
(cd raw && ../spmv_probe_pg 1290 716 8 90000 B 17592186044399 && gprof ../spmv_probe_pg gmon.out >profile_B_gprof.txt)
(cd raw && ../spmv_probe_pg 1290 716 8 90000 C 17592186044399 && gprof ../spmv_probe_pg gmon.out >profile_C_gprof.txt)
python3 run_panel.py && python3 analyze.py
```

**Limitations:** no `/workspace/isogeny-workspace`, no callable Conductor `conductor_check_conflicts` or `coord_start_work`, no native checkout or full cold `ca ic` / relation collection+linear algebra+descent run; no S3 checkpoint, signed PCC verification, or matched rho. Attempted container `git ls-remote` could not resolve github.com. Live read-only source and report PR are through GitHub connector. This is a bounded extracted diagnostic, not a claim of end-to-end improvement.

**Next:** native workers should first claim scope with Conductor, perform `bin/ws route/need` and gather a current complete `ca ic` profile, frozen real input matrices and A/A control in an isolated environment. Then select the hottest *unclosed* function outside the multiply-tested gather and require bit-identical native output and cold end-to-end nonregression.
