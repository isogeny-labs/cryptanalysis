# Bounded GPU continuation: items 7 and 13

Status: **prepared; no remote GPU result yet**. Root owns provisioning,
credential handling, evidence fetch and deletion of one dedicated two-hour
RunPod pod. This workstream does not alter existing pods or campaign stores.

The [frozen protocol](PROTOCOL.md) and [native launch script](remote_launch.sh)
bind a public ECC2K-130 sigma client to the pinned source snapshot at
`0ea8931d21d567f83de47c30bdaac0585f479c11`. The snapshot contains only
the required native sources, headers, KATs and build files; its 39 files are
hashed in `source/ecc.sha256`. `launch.sha256` binds the prospective command
script, checker and negation-contract originals.

The exact launcher is:

```sh
bash experiments/ideas_gpu_20261018/remote_launch.sh \
  /root/cryptanalysis/experiments/ideas_gpu_20261018/remote/run-0
```

It refuses an existing run directory and records each command, stdout,
stderr, exit code and GNU time resource receipt. Root must fetch the entire
output directory before deleting the pod. Run ID 53181 is quarantined;
global campaign uniqueness has not been established and no shared-store
upload occurs. Public P/Q use the exact normal-basis constants in
`source/tree/ecc2k130/src/hostcheck.h`. The polynomial-basis registry alias
`EC1N131Ckb1h136f03e58c98` is a different representation and is not silently
reused as this native record's curve identity.

Local correctness checks completed before remote dispatch:

- Pinned host sigma arithmetic: **2862 checks**, including **48/48** campaign
  known answers reproduced from public P/Q.
- Native host carry-less multiplication control: **28,633 checks**.
- Portable software multiplication control: **28,639 checks**.
- New native ingester: eight independently generated public-curve records,
  **8/8** golden-model trail replays and DP32/DP64 agreement. A changed
  coordinate was rejected with exit 1. An initial zero-length fixture was
  rejected; its logs remain beside the corrected positive-length fixture.

Raw local receipts are in `local_checks/`. These are CPU correctness
checks, not GPU coverage or performance measurements.

The pending remote gates require CUDA 13.3.73 build/device compatibility,
native KAT, GPU golden-model replays, health and exact checkpoint-restart
record equality before challenge collection. The bounded challenge slice
is two 180-second periods with graceful stop/restart and DP32 cutoff 32.
All full reports receive independent curve, weight, namespace and encoding
checks; long challenge trails are not fully replayed on the CPU. Native
duplicate ingestion is a separate gate. A detected collision is not a
recovered scalar or completed challenge.

The exact negation hypothesis is **H-RHO-bc6ea6**, experiment
**EXP-RHO-60da4f**. It already has native code and substantial prior trials.
Its implementation notes disclose an affine/Jacobian protocol deviation,
heavy censoring and baseline-control limitations. The four-arm L32 native
replay here preserves that deviation and does not close the full contract.
The challenge sigma client is not relabelled as its prime-field experiment.

The frontier component is documented separately in `frontier-binding.md`.
Its original memory-wall input and actual closure runner must pass their
runtime and resource gates; a row-reduction kernel alone cannot measure D.

No result in this package currently changes the IC leaderboard or the
existing campaign rates/forecast figures. Checked graph sources include
`papers/ecdlp-constant/sec-ecc2k-campaign.tex` and
`papers/ecdlp-constant/sec-ecc2k-gpu.tex`: no new GPU datum exists to replace
their historical measurements. The [run-flow diagram](reports/run-flow.svg)
marks every remote stage pending. The [report PDF](reports/report.pdf)
contains the same preparation status and explicit remaining criteria.
