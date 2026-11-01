# PDP oracle PS-5: no GPU and no owner-approved allocation, so the device gate and the 50x claim are unevaluated

- **Status:** `open`
- **Kind:** access/tool limit (no GPU in the agent environment) and resource limit (no owner-approved allocation or cap);
  not a mathematical obstruction and not an implementation gap in the CPU-executable part.
- **Affected work:** PS-5 of the `crypto` repository's PDP oracle speedup program
  ([protocol](https://github.com/aburan28/crypto/blob/main/research/pdp_oracle_speedup_20261011/protocols/PS-5.md),
  [plan](https://github.com/aburan28/crypto/blob/main/research/pdp_oracle_speedup_20261011/PLAN.md));
  this repository's [companion protocol](../experiments/pdp-oracle-speedup-20261011/README.md) and
  [PS-5 record](../experiments/pdp-oracle-speedup-20261011/ps5/README.md) (requirements 6, 8, 9, 10 and 11 of its table); the GPU rows of PS-6.
- **Next action owner:** the repository owner (allocation and cap), then any session with a CUDA device
- **Last updated:** 2026-10-25

## Problem

We cannot yet establish that PS-3's straight-line program, executed on a CUDA device with logic mapped to `lop3`, reaches at least 50x PS-3's single-core pairs per
second (or falls below the 20x stop line) because no GPU is available to the agent environment and the protocol requires an explicit owner-approved allocation and cap
(planning cap 8 GPU-hours) that has not been given.

Instance: the five frozen programs of PS-2 for `l = 8..12` (batch of 8 tasks, `n = 3l`, SHA-256s in the PS-5 record), the PS-0 verdict corpus and its digests, the curve
`y^2 + xy = x^3 + x^2 + 1`.  Original acceptance criteria (PS-5): the whole PS-0 corpus replayed on the device with identical digests (the gate before any timing); pairs per
second per device and per core-equivalent; counted bit operations per pair; an A/A run on the device; ABAB against PS-3 on one core of the same host with the number of contended
runs; success at least 50x with identical digests, stop below 20x; run records carrying the hardware block.  The expected ratio (device 32-bit logic throughput over one core's 512-bit
logic throughput) is to be filled from the device datasheet and a microbenchmark at the start of the task.

## Evidence and uncertainty

- **Observed:** `nvidia-smi` is absent and `gpu.devices` is empty in [`raw/manifest.json`](../experiments/pdp-oracle-speedup-20261011/ps5/raw/manifest.json).
  The kernel source compiles with the pinned `nvcc` 13.3.73 for `sm_80` at `l = 8` (PTX: 63,630 `lop3.b32` = the program's gates; SASS: 63,752 `LOP3`, 255 registers, spills;
  [`raw/ptxas_l8_sm_80.txt`](../experiments/pdp-oracle-speedup-20261011/ps5/raw/ptxas_l8_sm_80.txt), [`raw/sass_hist_l8_sm_80.txt`](../experiments/pdp-oracle-speedup-20261011/ps5/raw/sass_hist_l8_sm_80.txt)).
  The CPU emulation of the same generated code replays all 400 PS-0 targets (`l = 8..12`, 211,265,840 pairs) with digests and root sets equal to PS-0's
  ([`raw/parity_l*.jsonl`](../experiments/pdp-oracle-speedup-20261011/ps5/raw/)).
- **Derived or proved:** counted bit operations per pair are derived in the PS-5 record (for `l = 11`: 103,030 fused gates per 256-lane-slot run, 12,878.75 bit operations per lane slot).
  Nothing about device speed is derived or proved.
- **Suspected explanation:** none needed: the blocker is availability and authorisation.
- **Missing capability:** a CUDA device and an owner-approved allocation with a cap; a device `gpu` block; a datasheet-sourced figure and a device microbenchmark for the expected ratio.
- **What this evidence does not establish:** that the kernel runs correctly on a device (hardware `lop3` semantics and the device build's digests are unverified), how it performs
  (a kernel that needs 255 registers and spills at `l = 8` may or may not be fast), or any ratio to PS-3.  A CPU-emulation time is not a GPU time.

## What would unblock it

An owner-approved allocation and cap, and a device run of the kernel from this repository against the frozen inputs.

- [ ] The owner states a GPU allocation and a cap in writing for PS-5 (the protocol's planning cap is 8 GPU-hours); every pod or instance started is deleted and no credential enters the tree.
- [ ] The device and its `gpu` block are recorded; the expected ratio is computed from the device datasheet (cited) and a device microbenchmark of 32-bit `lop3` throughput, with the PS-3 single-core 512-bit logic figure from the same host class.
- [ ] The whole PS-0 corpus (`l = 8..12`, 80 targets each) is replayed on the device with verdict and root digests equal to PS-0's and every root set equal (the gate before any timing).
- [ ] Pairs per second per device and per core-equivalent at `l = 11..13` (and 14..16 if time allows) with an A/A run on the device and an ABAB run against PS-3 on one core of the same host (at least five rounds; contended runs counted).
- [ ] The ratio is reported against the 50x success and 20x stop thresholds, with run records carrying the hardware block.

These are necessary for the PS-5 acceptance criteria and sufficient for PS-5 as written; they establish one device's ratio only (the protocol: a result holds for the device measured), and PS-6's
charged comparison and the `crypto` scoreboard rows would remain.

## Next discriminating step

- **Action or proof obligation:** the first device gate: build `pdp_ps5_kernel.cu` for the device's architecture from the `l = 8` program with
  `suite/cuda/build_pdp_ps5.sh -n NVCC`, launch it over the `l = 8` corpus through the repository's GPU tooling (`cloud/runpod_pod.py`, `cloud/cairn_queue.py` or
  `cloud/modal_run.py --image cuda`), and compare the hit lists with the CPU emulation's per target.  Link: protocol PS-5, the PS-5 record.
- **Inputs and controls:** the frozen `l = 8` program and corpus; the CPU emulation's records as the control; the self-test's job-level comparison (every wire and every lane mask) as the
  localiser if digests differ.
- **Execution limits and stop condition:** the owner's cap; the protocol's stop (below 20x after the gate passes).  The `l = 8` gate is a fraction of a GPU-minute; the `l >= 11` timing is the larger spend.
- **Outcomes and next actions:** digests equal then timing at `l = 11`; digests differ then bisect with the per-wire comparison on one job (likely culprits: `lop3` semantics, compiler reassociation across the inline asm, spills) before any timing; a build that fails or
  an occupancy of one warp per scheduler then block the program (smaller batch, fewer live inputs) and record it as a new variant with its own hash; infrastructure failure then keep the receipt and retry within the cap.
- **Recheck trigger:** an allocation and cap from the owner, or a session with a CUDA device.

A planned step is not a completed experiment.

## Resolution and history

- 2026-10-25: opened with the PS-5 CPU-executable part ([`experiments/pdp-oracle-speedup-20261011/ps5/`](../experiments/pdp-oracle-speedup-20261011/ps5/README.md)).  Unresolved.
