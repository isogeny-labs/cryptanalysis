# Original high-memory closure cell binding

This launcher uses the existing **CPU** MutantXL closure on the rented GPU
host's RAM. It supplies no CUDA F4 kernel and does not run the new fixed-row
disk reducer. GPU use by the concurrent ECC2K-130 work is a separate workload.

The cryptanalysis checkout has no matching `crypto_lib` Rust crate/modules;
an `extern crate` alias cannot compile this runner. The payload therefore ships
the already-built native x86_64 Linux `dreg_closure` ELF, exact source snapshots,
input files and hashes. The binary is 3.2 MiB, SHA256
`55f44161c30130a207d6933d08031d3843f793da3990fbbad73ecb6a89b9906d`.
It requires libc/libgcc_s and GLIBC at most 2.34 (Ubuntu 22.04+ ABI). Runtime
compatibility is still gated by actual tiny SAT/UNSAT executions on the pod.
Source snapshots support inspection; they are not a standalone replacement
for the full crypto checkout and its Cargo dependencies when rebuilding.

## Frozen original workload

- Source repository base: `aburan28/crypto`,
  `e063d98475589d9aba7ae265a8cba830927e3156`; kernel sources unchanged in the
  campaign working tree. Source/binary digests are in `source/frontier/payload.sha256`.
- Exact committed input:
  `research/dreg_closure_scale_20261016/draws/m3-19-7.jsonl`, draw **0**.
  Whole-file SHA256:
  `a6bf7f1545cb5d91fffb41fa455c065b6fd0d547dce85aed2c5cdd5483c91532`.
- `m=3,n=19,ell=7,N=40`; random subspace basis and x_R are frozen in that
  record. The source drawer counted zero solutions. The degree-four closure
  previously saturated without refuting; it must do so again before admission.
- Existing successor binding:
  `research/dreg_closure_driver_20261016/RESULTS.md`, "Why degree 5 past ell=7
  is not measured here": dense degree-five N=40 needs about 760k columns and
  approximately 70 GB. This is the original next memory-wall question.
- Exact frontier command:
  `dreg_closure --to 5 --max-cols 800000 --draw 0 original-m3-19-7.jsonl`.
  It builds degrees 3/4/5 with full MutantXL fixed-degree saturation, recording
  XL/closure refutation, saturation, ranks, products and counted word operations.
  A refuting basis bounds **closure refutation degree**; it does not establish
  generic F4 solving degree or a complete ECDLP cost.

## Instrument controls and prerequisites

The tiny committed control is m4/n5/ell2/N18. Its whole-file SHA256 is
`b159fa3786cb4c35027a8d82fa0e15bd432e9a920260984e3f4244c538452d96`.
Draw2 must refute under closure by degree4; satisfiable draw0 must not refute
under XL or closure at degrees3/4. Both are executed before the high-memory draw.

Run `frontier_launch.sh NEW_OUTPUT_DIR` after shipping the entire
`source/frontier/` directory. Prerequisites are native x86_64 Linux,
`timeout`, `prlimit`, `jq`, `sha256sum`, `awk`, and GNU `/usr/bin/time` (or an
explicit `FRONTIER_TIME_BIN`). Missing tools fail closed; the launcher installs
nothing. The outer image/launch must explicitly provide these utilities.

At least **96,000,000,000 effective host RAM bytes** are required, checking
host MemTotal and cgroup memory.max. The process address-space cap is
80,000,000,000 bytes; no claim is made that this guarantees completion.
`RAYON_NUM_THREADS=1`, one process at a time; maximum entire frontier launcher
time is1200 seconds including two at-most60-second tiny controls. GNU time
records elapsed/CPU/max RSS/fault/I/O diagnostics. Shared GPU host timings do
not qualify an isolated speed comparison. The provider lifecycle is owned by
the root launcher, not this script.

The closure engine has **no internal checkpoint**. Restart is per draw in a
fresh output directory; a killed/OOM/capped draw stays censored and its failed
attempt remains charged. Do not interpret an empty output as degree-five
failure or proof. The script does not silently replace the cell with a smaller
matrix. Every terminal condition writes a descriptive status; only a complete
degree-five saturation/refutation with expected degree-four control can pass.
Independent replay and a run report remain required after actual execution.

## Explicit remaining gates

The requested m4 ell6/7 and guessed ell8/9 successors remain separate trials.
Canonical m4/n23/ell6 has70 variables and exceeds the current u64 builder.
No previously frozen native m4 ell6 successor draw was found, and this bounded
launch does not invent one or regenerate a substitute. Wider representations,
prospective draw selection and full original family grids remain open.

Before claiming launch readiness, verify the payload SHA256 and run the tiny
compatibility controls. Local CPU control results (if present) are not pod
executions, CUDA measurements, or completion of this original frontier draw.
