# Build flags (ISA level, FP contraction, LTO) and CUDA kernel items C7, C8, C10–C13

Date: 2026-11-12. Branch `claude/nice-babbage-bn0fn0`; identity baseline is
`origin/main` at `0568f9b9` (a `git archive` snapshot, so no co-tenant edit to
`src/` could leak into either arm). Source:
`crypto:docs/assessment-speed-productionization-20261110.md` §3b, items C7, C8
and C10–C13; `crypto:AGENTS.md` §10 (hardware-class discipline).

Host: 4-vCPU cloud VM, `Intel(R) Xeon(R) Processor @ 2.10GHz` with
`avx512f/bw/dq/vl/ifma/vbmi`, `avx512_fp16`, `amx_*`, `adx`, `bmi2`, `fma`
(Sapphire-Rapids class), Linux 6.18, gcc 13.3.0, clang 18.1.3, cmake 3.28.3,
valgrind 3.22.0, no GPU, no nvcc, no PMU. Co-tenant jobs held the load
average at 10–15 for the whole session, so every wall-clock number below is
a local, unisolated, exploratory measurement **[pcc:unverified]**; the
instruction counts (callgrind) do not depend on contention. No pcc claim,
`benchrec` record or leaderboard row is made here.

## Commits

| Commit | Change |
|---|---|
| `3d587a53e` build | `CA_ARCH` (`-march=`), `CA_NATIVE` kept as a deprecated alias, `-ffp-contract=off` on every C and CUDA-host TU, `-mno-mmx` with a named ISA level (GCC, x86), `CA_LTO`, `CA_BUILD_*` compile definitions, ctest `isa-no-mmx`, CI cell `-DCA_ARCH=x86-64-v3 -DCA_LTO=ON` |
| `acee95c2b` deploy, cloud | `deploy/docker/Dockerfile` agent image and the `cloud/taskq` examples build at `x86-64-v3` |
| `31931a5a3` cuda | C10 index mask / 32-bit remainder, C12 `__ldg` table reads and opt-in shared-memory table, C13 opt-in PTX Montgomery product, `CA_CUDA_LINEINFO` |
| docs | this note and `docs/session-logs/2026-11-12.md` |

## 1. Build flags

### 1.1 What CMake now does

| Option | Default | Effect |
|---|---|---|
| `CA_ARCH` | empty | `-march=${CA_ARCH}` on every C TU (library, tools, tests) and, under nvcc, on the CUDA host half (`-Xcompiler`). Empty = compiler baseline (`x86-64` / `armv8-a`). Documented values `x86-64-v2`, `x86-64-v3`, `x86-64-v4`, `native`. A value the compiler rejects stops configure. |
| `CA_NATIVE` | OFF | deprecated alias: sets `CA_ARCH=native` with a `DEPRECATION` message; conflicts with any other `CA_ARCH` |
| (always) | — | `-ffp-contract=off` for GNU/Clang/IntelLLVM C, `-Xcompiler=-ffp-contract=off` for nvcc host code, `-ffp-contract=off` for clang CUDA |
| (with `CA_ARCH`, GCC, x86-64) | — | `-mno-mmx` (section 1.4) |
| `CA_LTO` | OFF | `check_ipo_supported`, then `CMAKE_INTERPROCEDURAL_OPTIMIZATION ON` for every target (object library, both libraries, tools, tests); GCC adds `-ffat-lto-objects` when the static library is built, so the installed `libcryptanalysis.a` stays linkable without LTO |
| `CA_CUDA_LINEINFO` | OFF | nvcc: `-lineinfo` and `-Xptxas -v`; clang CUDA: `-gline-tables-only` and `-Xcuda-ptxas -v` |
| `CA_GPU_PTX_MONT`, `CA_GPU_SMEM_TABLE` | OFF | CUDA-only compile definitions for the two kernel variants of section 2 |

Configure prints `cryptanalysis: arch=x86-64-v3 compiler="GNU 13.3.0" lto=1
fp-contract=off`, and the object library gets `CA_BUILD_ARCH`,
`CA_BUILD_COMPILER`, `CA_BUILD_LTO` and `CA_BUILD_FP_CONTRACT` as compile
definitions. Nothing in `src/` reads them yet; section 1.9 has the patch.

A ctest `isa-no-mmx` (x86-64 with `objdump` only) fails if any instruction in
the linked library names `%mm0`–`%mm7`.

### 1.2 Where FP contraction could change an output

The project compiles as `-std=gnu11`, where GCC defaults to
`-ffp-contract=fast`: once `-march` enables FMA (x86-64-v3 and up, and every
aarch64 build) a product feeding an addition may be fused, with one rounding
instead of two.

Scratch probe (`fma_probe.c`: `a*b+c` as a positive control, plus the exact
expression shapes of the sizing rules), `gcc -O3`, FMA instructions in
`objdump -d`:

| | `-march=x86-64` | `-march=x86-64-v3` |
|---|---:|---:|
| GCC default (`fast`) | 0 | 1 (the control `a*b+c`, as `vfmadd132sd`) |
| `-ffp-contract=off` | 0 | 0 |

The sizing expressions themselves (`1.5*sqrt(sqrt_n/lg)`, `r*1.41421356 <=
want`, `1.25*sqrt_n/d + 1024`, `expected/(128*total_walks)`) contain no
product that feeds an addition, so none was fused even at the default.

Whole library, every `src/*.c` at `-O3 -march=x86-64-v3` with the
library's definitions, `vf[n]m{add,sub}*` instructions counted with
`objdump`, source lines from `-g`:

| Contraction rule | FMA instructions | Where (non-timing) |
|---|---:|---|
| GCC default (`fast`) | 140 in 12 TUs | `grumpy.c:244` `m = alpha*sq + 0.5`; `indexcalc.c:71-72` factor-base `B`, `C` interpolation `B0 + f*dB`. Every other site (rho, curve, gpu_rho, bsgs, kangaroo, pohlig, precomp, linalg, cheon, group_ec) is `ca_now()` in `ca_internal.h:19`, i.e. elapsed time only |
| `-ffp-contract=off` | 0 | — |

So the lines the assessment names (`rho.c:1076-1077,1108-1113`, `curve.c`
now `:805,:888`, `gpu_rho.c:358-398`) were never contracted by GCC 13.3. The
two real sites cannot or did not diverge here: in `indexcalc.c` `f` is a
multiple of 1/4 and every term is exact; for `grumpy.c` an exhaustive scratch
check of `sq = 1 … 2^32` with the default `alpha = 0.7` found 0 values where
`(uint64_t)(alpha*sq + 0.5)` differs between separate and fused rounding. A
user-supplied `alpha` or a later edit could still diverge, as could any
aarch64 build (FMA is baseline there; the `ubuntu-24.04-arm` CI cell and
Graviton hosts). With `-ffp-contract=off` on every TU this is a property of
the build, not a case analysis.

### 1.3 Identity at every level

Every arm against the `0568f9b9` snapshot built with the old CMakeLists:
`ctest -j4`; all 31 `ca_perfbench` fingerprints (also equal to the scratch
`perfbench.jsonl`); `ca_bench generic --threads 1 --json` (201 rows, every
field except `seconds`, `binary_sha256`, `command_line`, `host`,
`git_commit`) and its text table with the seconds and Mops/s columns masked;
the `ca_bench glv` table (13 curves × 20 runs each); `test_gpu` output.

| Arm | Flags | ctest | 31 fingerprints | generic rows / table | glv | test_gpu |
|---|---|---|---|---|---|---|
| def | new CMakeLists, `CA_ARCH` empty | 19/19 | identical | identical | identical | identical |
| v2 | `-DCA_ARCH=x86-64-v2`, before `-mno-mmx` | **test_curve never finished** (section 1.4) | identical | identical | identical | identical |
| v2 | `-DCA_ARCH=x86-64-v2` (`-mno-mmx`) | 20/20 | identical | identical | identical | identical |
| v3 | `-DCA_ARCH=x86-64-v3` | 20/20 | identical | identical | identical | identical |
| v4 | `-DCA_ARCH=x86-64-v4` | 20/20 | identical | identical | identical | identical |
| native | `-DCA_NATIVE=ON` (deprecation message printed) | 19/19 | identical | identical | identical | identical |
| lto | `-DCA_LTO=ON` | 20/20 | identical | identical | identical | identical |
| v3lto | `-DCA_ARCH=x86-64-v3 -DCA_LTO=ON` | 20/20 | identical | identical | identical | identical |

The committed trees were checked the same way, built from `git archive` of
the commit (so including the co-tenant `src/` commits up to `451d4ee5c`)
against the same `0568f9b9` outputs: `3d587a53e` at the default level and
`31931a5a3` at the default level and at `-DCA_ARCH=x86-64-v3 -DCA_LTO=ON`:
ctest 20/20 and every check identical in all three.

19 vs 20 tests: `isa-no-mmx` was added after the def and native builds. The
v2 (with `-mno-mmx`), v3, v4, lto and v3lto builds also contain the CUDA
header changes of section 2, so their `test_gpu` and
`c_gpu_rho_emulate_ec32` rows double as emulator identity evidence.

### 1.4 x86-64-v2 with GCC 13.3: an MMX register and a hung test

At `-march=x86-64-v2` the first build's `test_curve` ran for minutes of CPU
time (6 s at baseline). `gdb` on the live process: `ca_isqrt(16773703)`
called from `reduce_scalar` ← `ca_ec_mul_tau4`, with the estimate `x` near
`2^63` and decrementing by one per loop. The x87 status word showed `SF`
(stack fault) and `IE`, the tag word five valid zero registers and `R0 =
0xffff0000000000000000`, the bit pattern an MMX write leaves. The library
contained exactly one MMX instruction pair, in `ca_ec_mul_tau2`:

```
movq   (%rsp),%mm0
movq2dq %mm0,%xmm7
```

from the vectorised `residue3`/`digit_for` in `src/ec_tau.c:1892-1904`, with
no `emms`. The x87 stack stays tagged full, so the next `long double`
operation (`__builtin_sqrtl` in `ca_isqrt`) pushes onto a full stack, yields
the invalid-operation NaN, `fisttpll` converts it to `0x8000000000000000`,
and the fix-up loop `while (x*x > n) x--` runs from `2^63`.

| `ec_tau.c` compiled with | MMX instructions |
|---|---:|
| `-march=x86-64` | 0 |
| `-march=x86-64 -mssse3` | 0 |
| `-march=x86-64 -msse4.1` | 2 |
| `-march=x86-64 -msse4.2` | 2 |
| `-march=x86-64-v2` | 2 |
| `-march=x86-64-v2 -mno-mmx` | 0 |
| `-march=x86-64-v3` | 0 |
| clang 18 `-march=x86-64-v2` | 0 |

No source file uses MMX, so with a named ISA level CMake adds `-mno-mmx`
(GCC, x86-64). The `isa-no-mmx` ctest is the guard: run on the pre-fix v2
library it fails (exit 1); on the fixed v2, v3, v4 and lto builds it passes.
Neither the baseline nor v3/v4/native contained an MMX instruction.

### 1.5 Instruction counts and wall time

Callgrind instruction counts of the measured region (`ca_perfbench run
--instr`, `--instr-atstart=no`), one sample. Deterministic; v4 cannot be
counted because valgrind 3.22 has no AVX-512 support.

| kernel | base Ir | def / base | v2 / base | v3 / base | v4 | lto / base | v3lto / base |
|---|---:|---:|---:|---:|---|---:|---:|
| `c_mont_mul_x8` | 174,064,098 | 1.0000 | 1.0000 | 1.0000 | n/a | 1.0000 | 1.0000 |
| `c_ec_batch_add` | 254,160,855 | 1.0000 | 1.0000 | 1.0467 | n/a | 1.0001 | 1.0478 |
| `c_rho_ec36` | 298,406,013 | 1.0000 | 1.0000 | 0.9740 | n/a | 1.0012 | 0.9796 |
| `c_glv_rho_j0_32` | 105,018,578 | 1.0000 | 0.9989 | 0.9888 | n/a | 1.0030 | 1.0020 |
| `c_ic_precompute_zp44` | 189,337,945 | 1.0000 | 1.0000 | 1.0346 | n/a | 0.9993 | 1.0357 |
| `c_gpu_rho_emulate_ec32` | 75,858,752 | 1.0124 | 1.0118 | 1.0075 | n/a | 1.0133 | 1.0086 |

`def` is the new CMakeLists at the default level; it differs from `base`
only in the CUDA header of section 2, which only the emulator kernel
executes. The v2, v3, lto and v3lto binaries include the same header, so
their emulator row carries its +1.2 % as well.

ABAB, 5 rounds, arm order rotated each round, 5 samples per kernel per arm
per round; each cell is the median of the round medians / the minimum of the
minima, in ms.
`base2` is a hard link to the `base` binary (A/A). Load average 14–15 during
the run **[pcc:unverified]**.

| kernel | base | base2 | v3 | v4 | lto |
|---|---:|---:|---:|---:|---:|
| `c_mont_mul_x8` | 24.1 / 15.7 | 24.1 / 15.7 | 22.2 / 15.7 | 18.9 / 15.7 | 23.9 / 15.7 |
| `c_ec_batch_add` | 32.8 / 18.7 | 26.3 / 19.0 | 22.9 / 18.7 | 40.0 / 22.2 | 27.2 / 22.9 |
| `c_rho_ec36` | 50.1 / 33.2 | 48.4 / 33.2 | 54.0 / 33.3 | 45.4 / 33.5 | 50.6 / 37.3 |
| `c_glv_rho_j0_32` | 19.8 / 11.9 | 16.0 / 12.0 | 12.0 / 11.0 | 28.1 / 11.2 | 23.4 / 12.3 |
| `c_ic_precompute_zp44` | 36.5 / 24.7 | 28.9 / 20.1 | 25.1 / 20.1 | 33.0 / 20.2 | 33.5 / 21.4 |
| `c_gpu_rho_emulate_ec32` | 19.8 / 11.0 | 14.8 / 10.4 | 14.0 / 10.1 | 22.6 / 16.1 | 16.0 / 12.9 |

Reading: the A/A medians differ by up to 25 %, so no wall-clock ratio in
this table is distinguishable from noise; the minima agree within 2 %
between `base` and `base2` on four of six kernels (not on ic_precompute or
the emulator kernel).
At x86-64-v3 the instruction count changes by −2.6 % (rho_ec36), −1.1 %
(glv_rho_j0_32), +3.5 % (ic_precompute) and +4.7 % (ec_batch_add); an
instruction count does not weigh a `mulx` against a `mul`, or an AVX2
instruction against a scalar one, so it does not predict the wall-clock
direction. LTO changes it by −0.1 % to +0.3 % on the five kernels outside
the emulator. Neither is a measured gain on this host **[pcc:unverified]**;
an isolated Tier 0/1 run (AGENTS.md "CPU performance isolation gate") is the
next step if the lab wants a number.

### 1.6 LTO: keep it OFF by default

`CA_LTO=ON` builds and passes every identity check, but on this host the
measured-region instruction counts are within −0.1 % … +0.3 % of the
baseline on the five kernels the CUDA header does not touch (consistent with
the hot loops living in one TU each or in header `static inline`
functions), the
full build took 179 s (212 s for v3lto) against 57–58 s
without LTO under the same load (25 executables each pay an LTO link), and a
static archive needs `-ffat-lto-objects` to stay usable by non-LTO
consumers. Recommendation: default OFF; the new CI cell keeps it compiling.

### 1.7 `-fno-semantic-interposition`: not added

A build with `-DCMAKE_C_FLAGS=-fno-semantic-interposition -DCA_WERROR=ON`
fails: the extra inlining makes GCC 13.3 report `-Wmaybe-uninitialized` for
`mo.r2`, `mo.pinv`, `mo.p`, `mo.r1` in `ca_powmod` and `ca_mult_order`
(`src/modarith.c` through `ca_modarith.h:109-131`). The objects are already
compiled with `-fvisibility=hidden`, so only exported `CA_API` entry points
are interposable; the expected effect is small. Adding the flag needs a
`src/modarith.c` change first (other owner).

### 1.8 What the lab builds with

| Build site | Before | Now / proposal |
|---|---|---|
| `deploy/docker/Dockerfile` (agent image) | no `-march` | **changed**: `ARG CA_ARCH=auto` → `x86-64-v3` on an x86-64 build host, baseline elsewhere |
| `cloud/taskq/examples/cpu-rho-{solve,benchmark}.json` (`ca-cpu`, `arch: amd64`) | no `-march` | **changed**: `-DCA_ARCH=x86-64-v3`; README updated |
| `cloud/taskq/examples/gpu-rho-sm120.json` (host half) | no `-march` | **changed**: `-DCA_ARCH=x86-64-v3` |
| `cloud/taskq/Dockerfile.{cpu,gpu}` | toolchain only, tasks build in `setup` | nothing to change |
| `.github/workflows/deploy.yml:65` (helm job document) | no `-march` | proposal: leave as is (it mints a document, no timing) |
| `.github/workflows/rho-walltime-tier1.yml:86` | no `-march` | proposal: keep baseline for the pinned ref/cand comparison, or add `-DCA_ARCH=x86-64-v3` to all three arms together, never to one arm |
| `.github/workflows/nightly.yml:99` | `-DCA_NATIVE=ON` (deprecated alias, still works) | proposal: `-DCA_ARCH=x86-64-v3`, so nightly numbers do not depend on which runner model GitHub assigns |
| `scripts/runpod_deploy_glv.sh:65`, `README.md:150` | `CA_NATIVE=ON` | proposal: `CA_ARCH` (the alias keeps them working) |

`x86-64-v3` (AVX2, BMI2, FMA, MOVBE) runs on every current EC2 x86 family,
Intel from Haswell and AMD from Zen 1. It does not run on the
previous-generation c3/m3/r3/i2/t1 (Ivy Bridge and older) or on Atom-class
cores; a scheduler that can still place those must exclude them or keep the
baseline. Native and x86-64-v4 are not proposed for Spot images.

### 1.9 Follow-up for the `src/` owner: `ca_build_info()`

The compile definitions exist; exposing them needs this patch (checked in a
scratch copy: compiles with `-Wall -Wextra -Wmissing-prototypes -Werror`,
prints `arch=unknown;compiler=unknown;lto=unknown;fp-contract=unknown`
without the definitions and `arch=x86-64-v3;compiler=GNU 13.3.0;lto=1;fp-contract=off`
with them):

```diff
--- a/include/cryptanalysis/ca_types.h
+++ b/include/cryptanalysis/ca_types.h
@@ CA_API const char *ca_version(void);
 CA_API const char *ca_version(void);
+/* How this library was compiled: "arch=...;compiler=...;lto=0|1;fp-contract=..."
+ * (CMake records CA_ARCH, the compiler id and version, CA_LTO and the FP
+ * contraction rule; builds outside CMake report "unknown").  Static string. */
+CA_API const char *ca_build_info(void);
 CA_API const char *ca_status_string(ca_status s);
--- a/src/util.c
+++ b/src/util.c
@@ const char *ca_version(void) { return CA_VERSION_STRING; }
 const char *ca_version(void) { return CA_VERSION_STRING; }
+
+/* Set by CMakeLists.txt on the library objects; absent in the Go, Python
+ * and Rust builds that compile src/ directly. */
+#ifndef CA_BUILD_ARCH
+#    define CA_BUILD_ARCH "unknown"
+#endif
+#ifndef CA_BUILD_COMPILER
+#    define CA_BUILD_COMPILER "unknown"
+#endif
+#ifndef CA_BUILD_LTO
+#    define CA_BUILD_LTO unknown
+#endif
+#ifndef CA_BUILD_FP_CONTRACT
+#    define CA_BUILD_FP_CONTRACT "unknown"
+#endif
+#define CA_BUILD_STR2(x) #x
+#define CA_BUILD_STR(x)  CA_BUILD_STR2(x)
+const char *ca_build_info(void)
+{
+    return "arch=" CA_BUILD_ARCH ";compiler=" CA_BUILD_COMPILER ";lto=" CA_BUILD_STR(
+        CA_BUILD_LTO) ";fp-contract=" CA_BUILD_FP_CONTRACT;
+}
--- a/tools/ca_bench.c
+++ b/tools/ca_bench.c
@@ static void json_header(...)
     json_str(f, ca_version());
+    fputs(",\"build_info\":", f);
+    json_str(f, ca_build_info());
     fputs(",\"binary_sha256\":", f);
```

Optional, same owner: on x86 GCC/clang, `ca` could check
`__builtin_cpu_supports("x86-64-v3")` at start-up when built with that level
and exit with a message instead of `SIGILL` on an older host.

## 2. CUDA kernel (`cuda/ca_device.cuh`, `cuda/rho_kernel.cu`)

**Every device-side change in this section is untested on a GPU.**

### 2.0 Oracle and toolchain

`src/gpu_emulate.c` runs `ca_dev_rho_thread` for every thread id over host
buffers; the header is compiled as host C there, so `test_gpu` (walk
invariants `a·G + b·H = X` over 64 walks, emulated runs in Z_p^* and on
curves, `ca_dev_*` against the host arithmetic), the perfbench kernel
`dlp/c_gpu_rho_emulate_ec32` and the `ca solve --alg gpu-rho --backend
emulate` matrix below all run the code the GPU runs, except what sits
behind `__CUDA_ARCH__`.

Device compiles: `scripts/build_cuda_kernel.sh --fetch` (the CI job's own
script) fetched NVIDIA's pip wheels, so clang 18.1.3 `-x cuda
--cuda-device-only` plus `ptxas` 12.9.86 ran here for sm_70/80/89/90 and
`--walks 4` / `16`, as in the CI job "CUDA kernel (compile + register
report)"; the two opt-in variants were compiled the same way by hand. The
CUDA files pass clang-format 18.1.3 and 21.1.8 over the whole file.

### 2.1 C10: the per-step index reduction

`ca_dev_index` now takes `hi = (uint32_t)(h >> 32)` and returns `hi & (r-1)`
when `r` is a power of two, else `hi % r` in 32 bits; `(i + 1) % r` became
`ca_dev_next_index` (`i + 1 == r ? 0 : i + 1`, valid since `i < r` always:
`i` comes from `ca_dev_index` or from `pend`, which only `ca_dev_next_index`
and a restart (0) write). The value is `(h >> 32) % r` in every case. Host
guarantee: `gpu_rho.c:330-338` picks `r = 8` doubled up to the cap (a power
of two) unless `ca_gpu_rho_params.r` is set, and an explicit `r` may be any
value ≥ 4 — so the general remainder stays, behind a launch-uniform branch.

Static PTX (sm_80, kernel `ca_rho_walk_kernel`): `rem.u32` 13 → 11 (the two
`next_index` sites), `rem.u64` 6 → 6 (all in `% n` of the walk restart, not
per step). clang had already narrowed `(h >> 32) % r` to a 32-bit `rem`, so
the assessment's "64-bit modulo" holds for the source but not for clang's
output; nvcc was not available to check. At run time a power-of-two `r` now
skips the per-step `rem.u32` (a multi-instruction software routine on every
NVIDIA architecture).

Emulator identity: `test_gpu` output and the `c_gpu_rho_emulate_ec32`
fingerprint identical in every arm of section 1.3; and 54 `ca solve --alg
gpu-rho --backend emulate` runs on the `generic-26` instance
(`cloud/taskq/instances/generic-26.json`), seeds 1–3, `--r` 0 (automatic),
20, 24, 64, 100, 1000, 1024 with and without `--no-negation`, plus `--r` 4,
5, 6, 7 with `--no-negation` — so the non-power-of-two remainder path is
exercised — print the same JSON (every field but `seconds`) from the base
`ca`, the def `ca` and the v3lto `ca`. (`--r 4` with the negation map did
not finish within two minutes on the base binary either: a 4-entry table
with the negation map is dominated by fruitless cycles; it is left out.)

Host cost of the change in the emulator: the `c_gpu_rho_emulate_ec32`
instruction count rises 1.24 % (75,858,752 → 76,800,790, def vs base), since
the mask path adds a test and a branch where the old code had one `div`,
which callgrind counts as one instruction. Wall time over 10 alternating
rounds under load 20: median of medians 20.9 ms (base) and 23.0 ms (def),
minima 14.5 and 14.9 ms, inside the noise **[pcc:unverified]**. The host
emulator is a correctness oracle, not a production path.

### 2.2 C12: multiplier table reads, walk-state layout, launches

- Table reads go through `ca_dev_mult(g, i, j)`: `__ldg` on the device
  (read-only data cache; 27 `ld.global.nc` in the sm_80 PTX), a plain load
  on the host. Register count and stack frame unchanged (table below).
- `CA_GPU_SMEM_TABLE` (default OFF): a second kernel
  `ca_rho_walk_kernel_smem` copies the `r × 32`-byte table into dynamic
  shared memory once per block, then runs the same body on a local copy of
  the arguments pointing at it; the launch shim uses it when the table fits
  in 48 KiB and falls back to the unchanged kernel otherwise. The original
  kernel keeps its name and signature, because the Rust binding loads the
  mangled `_Z18ca_rho_walk_kernel15ca_gpu_rho_args` from the build-time PTX.
  clang 18's NVPTX backend aborted ("Cannot cast between two non-generic
  address spaces") when the shared pointer was stored into the by-value
  parameter itself; the local copy avoids it. Trade-off: at `r = 1024`
  (negation map) 32 KiB per block limits an sm_70 SM to 3 blocks of 128.
- Not done: structure-of-arrays walk state. `tests/test_gpu.c:161-168`
  reads `state[4*w + c]` (and the header documents that layout), and the
  state and aux words are loaded once and stored once per launch, against
  `steps ≥ 64` walk steps per launch (`gpu_rho.c:381-402`), so the 256-byte
  stride is paid at most once per 64 steps.
- Not done: double-buffered DP output on two streams. The backend contract
  (launch → host DP processing → `restart(wid)` → next launch) makes the
  restart flags of launch k+1 depend on the host's processing of launch k;
  overlapping them applies restarts one launch late and changes the walks.
  It needs a change to `src/gpu_rho.c` and a new replay definition.

### 2.3 C13: PTX Montgomery product (opt-in)

`CA_GPU_PTX_MONT` (default OFF, device code only): `a·b` on 32-bit limbs with
`mul.lo/hi`, `mad.lo.cc`, `madc.hi[.cc]`; two word-by-word reduction rounds
with `m = r_i · (−p⁻¹ mod 2³²)` (the low word of `pinv`), split into a
low-half and a high-half carry chain each; a 3-word `sub.cc`/`subc` and a
select instead of the branchy `if (c2 || r >= p)`. The result is the
canonical residue whenever `a·b < p·2⁶⁴` (one operand ≤ p, which holds at
every call site), so any correct implementation returns the same word.

A scratch C model mirrors every PTX instruction (`CC.CF` as a variable) and
was compared with the portable `ca_dev_mont_mul`: 5,980,000 products over
20,000 odd moduli (top bit set, random size, `2^64 − 2k`, 32-bit,
`2^k + small`), each with the 64 pairs from {0, 1, 2, p−1, p−2, ⌊p/2⌋,
⌊p/2⌋+1, p} and 236 random pairs: 0 mismatches. That checks the algorithm
and the carry bookkeeping, not `ptxas`'s translation of the inline assembly
or the hardware.

Static PTX, sm_80: `mul.hi.u64` 336 → 0, `mad*.cc.u32` 0 → 1,944, 9,804 PTX
instructions against 5,664 (the 64-bit multiplies were single PTX
instructions that `ptxas` expands; the limb version is spelled out), cubin
151,400 bytes against 158,696. Registers in the table below. Whether the
issued instruction count per step drops can only be read from SASS or a
profiler on a GPU.

### 2.4 C11: warp-cooperative batched inversion — not implemented

The proposal shares one Fermat inversion among the 32 lanes of a warp via
`__shfl_up_sync` prefix and suffix products. On SIMT hardware that does not
reduce issued instructions: today each lane computes its own inversion, but
the 32 lanes do it in the same warp instructions, so a warp already issues
one inversion's worth of instructions (≈ 64 squarings + ≈ 32 products) per
step for its 32 × 8 = 256 walks. A cooperative version issues the same
inversion (every lane executes it, or 31 lanes idle while one does) plus
2 × 5 shuffle-and-multiply rounds, about 10 more Montgomery products per
lane per step. The levers that do change the ratio are a larger `CA_GPU_W`
(more walks per inversion per lane; changes the walk set and therefore the
replay, and grows the 736-byte stack frame) or a cheaper inversion (an
addition chain for `p − 2`; the current loop also does one unneeded final
squaring). Neither was in scope; `__launch_bounds__` was not added because
nothing here changes the register budget.

### 2.5 ptxas reports and occupancy (from the reports, not measured)

clang 18.1.3 + ptxas 12.9.86, 128 threads per block, 0 spills everywhere:

| Kernel / variant | sm_70 regs | sm_80 regs | sm_90 regs | stack frame |
|---|---:|---:|---:|---:|
| baseline (`0568f9b9`), W = 8 | 72 | 64 | 64 | 736 B |
| this change, W = 8 | 72 | 64 | 64 | 736 B |
| this change, W = 4 / W = 16 | 72 / 80 | 64 / 64 | 64 / 64 | 368 / 1,472 B |
| `CA_GPU_PTX_MONT` | 80 | 64 | 64 | 736 B |
| `CA_GPU_SMEM_TABLE` (smem kernel) | 80 | 56 | — | 736 B |

Occupancy from registers alone: 72 registers → 28 warps of 64 on sm_70
(44 %); 80 → 24 warps (38 %); 64 on sm_80/sm_90 → 32 of 64 warps (50 %),
on sm_89 32 of 48 (67 %); 56 on sm_80 → 36 warps (56 %) before the
shared-memory limit. The assessment's "~200 registers/thread" is not what
ptxas reports: the per-thread walk array `w[8]`, `den[8]`, `pre[8]` and
`idx[8]` live in the 736-byte local-memory frame (141 `ld.local` and 95
`st.local` in the PTX), which at 1,024 resident threads is about 736 KiB per
SM, larger than any L1. That local traffic, not registers, is the next
thing a profiler on a GPU should look at.

### 2.6 What the lab should run on a GPU

1. Build `-DCA_CUDA=ON -DCA_CUDA_LINEINFO=ON` and read the `ptxas` lines
   (nvcc, where clang was used here).
2. Identity: `ca solve --alg gpu-rho --backend cuda` and `--backend emulate`
   on the same instance and seed must recover the same `x`. The counters
   (`ops`, `iterations`, `table_entries`, `collisions`, `launches`) should
   match as well, with one known exception: the device writes the DPs of a
   launch in `atomicAdd` order, not thread order, so after a useless
   collision a different walk may be restarted and the counters may differ
   from that launch on. Compare the three builds (default,
   `-DCA_GPU_PTX_MONT=ON`, `-DCA_GPU_SMEM_TABLE=ON`) against each other on
   the device as well as against the emulator; the C10 change is already
   covered by the emulator.
3. A/B the three builds with ABAB ≥ 5 under the GPU benchmark rules, and
   only then consider turning either option on by default.

## Sources checked

KB unavailable in this subagent session (no `research-kb` tool was
attached); the sources read directly were
`crypto:docs/assessment-speed-productionization-20261110.md` §3b and §6,
`crypto:AGENTS.md` §10, `cryptanalysis:AGENTS.md` ("Hardware and placement",
"CPU performance isolation gate"), `cryptanalysis:src/{rho,curve,gpu_rho,
grumpy,indexcalc,modarith,ec_tau}.c`, `cryptanalysis:tests/test_gpu.c`,
`cryptanalysis:bindings/rust/cryptanalysis-cuda/{build.rs,src/kernel.rs}`
and `cryptanalysis:scripts/build_cuda_kernel.sh`.
