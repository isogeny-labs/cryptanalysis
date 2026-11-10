# clmad audit on sm_120: miscompile reproduction and two-class timing — protocol

Frozen before any device data. Follow-up to the open threads of
`crypto/docs/audits/GPU_SIDE_CHANNEL_DEFENSES_20261109.md` (A2, A3, A5, A7).

## Questions

Q1. Does `ptxas` from CUDA 13.4.3 (reported V13.4.92) miscompile a
    Karatsuba carry-less product whose running product starts from the
    constant one, on an sm_120 part, at `-O2`/`-O3`, as the third-party report
    github.com/robik75/ptxas-clmad-constant-operand says? Does CUDA 13.3.1,
    the toolkit our documented builds use, show the same?
Q2. Do the `ecc2k130` packed-arithmetic device tests (`test-packed-cuda`,
    production defines) and the host `clmad` tests pass under both toolkits?
Q3. Is the latency of a dependent `clmad` chain on sm_120 distinguishable
    between operand classes (a two-class timing test with controls)?

## Design

Hardware: one RunPod GPU pod per toolkit, GPU type from the list
[RTX 5090, RTX PRO 6000 Blackwell Server/Workstation] (all compute
capability 12.0), same type for both arms where availability allows. The
pod's `nvidia-smi` output, driver version, compute capability and clocks are
recorded in `results/<arm>/env.txt`. Clock locking is attempted and its
success recorded; it is not required.

Arms: `cuda13.3.1` (image `nvidia/cuda:13.3.1-devel-ubuntu24.04`) and
`cuda13.4.3` (image `nvidia/cuda:13.4.3-devel-ubuntu24.04`). Each arm runs
`pod/run.sh` from this directory unchanged.

### Q1 reproduction (`src/repro.cu`, written independently of the report)

- `clmul64` = `clmad.lo.u64` + `clmad.hi.u64` with zero addend.
- `mul128`: three 64x64 products (Karatsuba), 256-bit result folded to 128
  bits by XOR of the high 128 into the low 128 (any fixed fold suffices;
  the host reference applies the same fold).
- Kernel: one thread, `e = 1`, `e = mul128(e, a[t])` for `t < N`, unrolled;
  every intermediate stored. Host recomputes with a bitwise carry-less
  multiply and compares every step.
- Matrix: N in {14, 15, 16, 18, 19} x `-Xptxas -O{3,2,1,0}`, SASS for
  sm_120; plus N = 14 as PTX-only (`compute_120`, driver JIT); plus a
  schoolbook (four-product) control at N = 14, `-O3`; plus a carry-less
  squaring chain `e = clmul(e, e)` at N = 64, `-O3` (finding A7).
- SASS `CLMAD` instruction counts from `cuobjdump -sass` are recorded for
  every SASS binary.

Decision rule (per binary): exit 0 = every step matches; exit 1 = mismatch
(the kernel's own output names the first wrong step); exit 2 = CUDA error
(recorded, not counted either way). Q1 is "reproduced" for an arm if any
`-O2`/`-O3` Karatsuba binary exits 1 while the same N at `-O1`/`-O0` exits 0.
It is "not reproduced" if every binary exits 0. Any other pattern is
reported as is.

### Q2 (`ecc2k130` tests)

`make -C ecc2k130/runner test-clmad test-clmad-square` (host, g++) and
`make -C ecc2k130/runner test-packed-cuda` with the RTX PRO 6000 production
packed defines and `ARCH` for sm_120. Pass = make exit 0. Nothing else.

### Q3 two-class timing (`src/clmad_timing.cu`)

Instrument: `clock64()` around a dependent chain of `CHAIN = 2048`
operations per thread; the chain passes through the addend
(`r = clmad(x, y, r)`), the multiplicands `x, y` are fixed per thread for
the launch. Modes: `lo`, `hi`, `neg` (integer xor/add chain, negative
control), `pos` (inner trip count = popcount(x) & 7 plus one, positive
control). Geometries: latency (1 block x 32 threads) and occupancy
(2 blocks per SM x 256 threads).

Operand classes per thread pair (x, y): `zero`, `one`, `ones`, `topbit`,
`alt`, `lowhw` (random, Hamming weight 1 to 4), `highhw` (weight 60 to
63), `random_a`, `random_b` (independent seeds; the A/A pair), `fixed_a`,
`fixed_b` (two fixed random pairs, the same for every thread and rep).

Schedule: `reps` launches per (mode, class), order shuffled within each rep
with a seeded RNG, 3 warm-up launches discarded. Latency geometry
reps = 100; occupancy geometry reps = 50. Per launch the per-thread cycle
counts are recorded raw (latency geometry) or as per-launch min / median /
max over threads (occupancy geometry).

Decision rule, per (mode, geometry): statistic = per-launch median over
threads of cycles per operation. For every class C, Welch's t between C and
`fixed_a` over launches; and between `random_a` and `random_b` (A/A), and
`fixed_a` and `fixed_b`. Threshold |t| > 4.5 (dudect's). Validity: the
`pos` mode must show |t| > 4.5 for `lowhw` vs `highhw`, and the `neg` mode
must show |t| <= 4.5 for every pair; otherwise the instrument is invalid for
that geometry and no Q3 verdict is drawn from it. With a valid instrument:
"no class distinguishable" if every |t| <= 4.5 for `lo` and `hi`;
"distinguishable" naming the classes otherwise. Effect sizes are reported
as cycles per operation with the per-class spread. A null result bounds the
effect at this sample size; it is not a constant-time proof.

## What is not claimed

Nothing about other architectures, other toolkits, throughput under
contention, or power. A reproduced miscompile is a correctness finding in a
vendor tool; a timing null is a bound, not a guarantee.

## Outputs

`results/<arm>/` raw files; `results/summary.json`; `REPORT.md`; figures;
a `bench.record/v1` record under `benchmarks/records/`; a
`benchmarks/20261110-clmad-audit/` entry.

## Amendment A1 (2026-11-10, after the main runs, before this addendum ran)

The main runs did not reproduce Q1 with our reproducer on either toolkit,
while the SASS counts show the constant-one step folded away (78 `CLMAD`
at `-O1`..`-O3` against 84 at `-O0` for N = 14) under both. To separate
"our reproducer does not trigger it" from "the defect is absent here", the
third-party reproducer is run unchanged (`pod/run_author_repro.sh`: cloned
on the pod, commit recorded, its own `run.sh`, N in {14, 15, 16, 18, 19})
on both toolkits. Its exit codes are reported next to ours; they do not
change the Q1 rule, which stays bound to our reproducer. Its source is not
copied into this repository (no licence).
