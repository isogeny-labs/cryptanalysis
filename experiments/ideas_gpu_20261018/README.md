# Bounded GPU continuation: items 7 and 13

Latest separate GPU-v3 attempt: **CUDA build passed, device initialization failed; no GPU walk executed**. Its effective125GB RAM also failed the192GB frontier gate. The CPU-v3 request was capacity-refused without allocating a pod. See [GPU-v3 addendum](GPU_V3_RESULTS.md); that pod was fetched/deleted and absence verified.

Status after recovered run1: **GPU correctness control executed; original ingestion failed; original memory-frontier attempt censored**. See [run1 results](RUN1_RESULTS.md), [run0 failure](RUN0_RESULTS.md), [current PDF](reports/report.pdf), and [independent archive audit](diagnostics/run1-audit/receipt.json). Root fetched the dedicated pod's evidence, deleted it and verified absence. No challenge slice or complete benchmark ran. The additive local v2 checker validates retained control reports without changing the original pipeline failure. Later allocation attempts are separate records.

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

The protocol requires CUDA13.3.73 build/device compatibility, native KAT, GPU golden-model replays, health and exact checkpoint-restart record equality before challenge collection. Run1 passed build/device/KAT and the short GPU control (3,145,728 iterations,1719DP,3 client replays,0dropped). Original ingestion v1 then rejected six native-valid zero-length reports. Health, restart, benchmark and challenge stages did not run. A separately frozen local v2 qualification checks all1719 reports and replays all6zero plus8positive trails;1705positive trails remain unreplayed. See [qualification details](diagnostics/ingestion-zero/README.md). The bounded challenge slice
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

The frontier component is documented separately in `frontier-binding.md`. Run1 passed its tiny SAT/UNSAT controls and attempted the original n19/m3/ell7,draw0,degree5 closure. It failed allocation after748.35s at77,709,264KiB peak RSS under an80GB address-space cap. Actual exit134/signal6 governs the outcome despite the contradictory GNU-time `%x` field0. Degree remains unmeasured. This is CPU XL/MutantXL closure on a GPU host, not GPU/distributed F4.

No result in this package changes the IC leaderboard or historical campaign rates/forecasts. Checked graph sources include `papers/ecdlp-constant/sec-ecc2k-campaign.tex` and `papers/ecdlp-constant/sec-ecc2k-gpu.tex`: the short DP46 correctness control does not supersede their campaign benchmarks. The [updated run-flow](reports/run-flow.svg), [recorded validation/memory plot](reports/run1-validation-memory.svg) and [report PDF](reports/report.pdf) distinguish actual passes, original failures, additive local qualification and unrun stages. Full challenge completion, complete negation contract and distributed/GPU F4 remain open.
