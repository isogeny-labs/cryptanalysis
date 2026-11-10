# clmad on sm_120: ptxas constant-fold defect, ecc2k130 device tests, two-class timing (2026-11-10)

Copies for browsing of the study
[`research/clmad_audit_20261110/`](../../research/clmad_audit_20261110/REPORT.md)
(record `benchmarks/records/20261110T0408Z-clmad-audit.json`; protocol frozen before data):

- `report.pdf`: the result report; `repro.svg`/`.png`: our reproducer's exit codes; `repro_author.svg`/`.png`: the
  third-party reproducer's; `timing.svg`/`.png`: per-launch cycles per `clmad` by operand class.

Class: correctness and timing audit of a vendor instruction, not an ECDLP speed result. No row here enters the IC
leaderboard. Every statement `[pcc:unverified]` (one session, one run per arm, no independent replay yet).

## Result

| arm | GPU | toolkit | Q1 our reproducer | Q2 test-packed-cuda exit | `clmad.lo`/`.hi` latency, cycles per op (1 warp) | occupancy geometry (2 blocks/SM x 256) | Q3 |
|---|---|---|---|---|---|---|---|
| cuda13.3.1 | NVIDIA RTX PRO 6000 Blackwell Server Edition | nvcc 13.3.73, driver 595.91.07 | not reproduced | 0 | 63.528 / 63.530 | 255.90 / 255.90 | no class distinguishable (pos t -23189, neg max abs t 1.30) |
| cuda13.4.3 | NVIDIA GeForce RTX 5090 | nvcc 13.4.92, driver 595.91.07 | not reproduced | 0 | 55.084 / 55.087 | 255.86 / 255.86 | no class distinguishable (pos t -36705, neg max abs t 1.00) |

Addendum A1, the third-party reproducer (github.com/robik75/ptxas-clmad-constant-operand, commit `45d6922ee752`) run unchanged:

| arm | GPU | toolkit | result |
|---|---|---|---|
| author-cuda13.3.1 | NVIDIA RTX PRO 6000 Blackwell Server Edition | nvcc 13.3.73 | reproduced at N = [14, 15, 18, 19] (correct at N = 16 and at -O1/-O0) |
| author-cuda13.4.3 | NVIDIA RTX PRO 6000 Blackwell Server Edition | nvcc 13.4.92 | reproduced at N = [14, 15, 18, 19] (correct at N = 16 and at -O1/-O0) |

Reading: the reported `ptxas` defect (a `clmad` whose multiplicand folds to the constant one loses its high half at
`-O2`/`-O3` and under driver JIT) is real on sm_120 and is **not specific to 13.4.92: ptxas 13.3.73 shows it too**.
Our independent reproducer folds the same step (6 fewer `CLMAD` in SASS at `-O1` and above) and still computes
correctly on both toolkits, so the defect is sensitive to the surrounding code. The `ecc2k130` packed-arithmetic
device tests pass on both toolkits with the production defines; no `clmad` operand in those kernels is a
compile-time constant. The timing instrument validated on both GPUs (positive control detected, negative control
flat) and found no operand class distinguishable for `clmad.lo` or `clmad.hi` at either geometry: a bound at this
sample size, not a constant-time guarantee.

Host: RunPod, dedicated-GPU tier, one pod per arm (ids in `results/<arm>/allocation.json`), driver 595.91.07, no clock lock
(not permitted in the container). Cost: four pods, about 10 minutes of GPU time in all.
