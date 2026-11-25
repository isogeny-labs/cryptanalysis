# Exact checkpoint continuation, 2026-10-19

This records infrastructure recovery. There is no new full-subgroup solve,
independent target, timing panel or performance promotion.

## Recovery and identity

The original PID 21441 was absent on 2026-10-19 reconnection, with no other
campaign worker running. The last retained progress rows are from
2026-10-17 01:20:27 UTC; the exact disappearance time is unknown. Before
resumption, the full three a=0 checkpoints and the completed Q_7 records were
copied, their SHA-256 digests retained, and all 16 public jobs byte-compared
with the immutable latest archive.

The original binary still hashes to
`e02c63d3fc033ce6ccc007aca13cd74aa0c342572744bce7869e984585525231`
and remains bound to crypto `dbd33f00da0a0ac35f285603ec168ad9d91a1d79`.
It resumed the same public/campaign directories as PID 641, start tick
23288, comm `cover_rho-campa`, actual affinity `[4]`. It acknowledged
`paused_with_checkpoints` at Unix 1792381583. CPU ticks advanced
9193 to 17583 and all three a=0 work/timestamp streams advanced after resume.
The [machine receipt](resume.json) retains the observations, input-byte checks,
pre-resume hashes, operational table counts and subsequent maintenance pause.

The pre-resume a=0 tables contained 704,913 E entries, 709,225 inverse/E
entries and 7,314 native entries. At the maintenance pause they contained
705,475, 709,787 and 7,315 respectively, with unchanged job/method identities
and 32 lanes each. The durable checkpoint counters can precede the last
logged quantum; uncheckpointed work is not silently treated as retained.

## Completion and timing accounting

The unchanged controller reloads each already-complete a=1 Q_7 checkpoint on
restart and repeats its separate-process E/Jacobian verification. The live
completion log therefore has 27 rows but only 24 unique `(a,index,arm)`
completions. The three appended rows are Q_7 verification replays. Original
completion rows and old Q_7 candidate/verification files were retained before
resuming; the replayed candidate bytes match the originals.

The native summary reads one checkpoint per target/arm, independently of
duplicate completion-log rows. Repeated verification is not a new solve, target
or independent-host performance replay. There are still zero a=0 completed
targets. Later partial counters span interrupted execution sessions and remain
censored, with no continuous-original-host timing claim.

No original target was regenerated, held-out witness read or supplied,
interval/prefix substituted, collision table discarded, or paid resource
provisioned. The [a=0 compute problem](../../../../problems/binary-genus2-a0-full-solve-compute.md)
and [ecbench-adapter problem](../../../../problems/ecbench-binary-genus2-full-subgroup-adapter.md)
remain open. The newest full checkpoints and backup are workspace-local;
this receipt does not establish durable retention.

## Frozen deliverables

All four scientific run directories, their report copies, the inspected PDF
and all four benchmark bundles are unchanged. The latest scientific archive
remains `run-20261014T2250Z`. Existing quantitative graphs and benchmark
indexes still describe the same eight matched a=1 targets: no additional
completed observation exists to plot or admit. No new benchmark or PDF is
created for censored progress. Complete common pricing, qualified isolation,
independent-host performance replay, ecbench audit and full geometric/Picard
formalization remain unresolved.

## Repository-specific validation

This repository mirrors one campaign's runtime receipt, not a second experiment
or crypto's current-head validation history. Suite validation archives, native
source and frozen performance evidence remain unchanged. Only continuation
documentation and the existing compute-problem history are updated here.
Crypto's dependency repair and inherited CI diagnostics are maintained in
[PR1830](https://github.com/aburan28/crypto/pull/1830).

## Operational receipt scope

The new `resume.json` omits recovered scalar values from the three Q_7
verification replays. It retains both-group verification outcomes, input
bindings, native-work counts and verification timings. Full original
verification evidence and local replay receipts remain unchanged. The replay
rows remain three duplicates of the existing 24 unique completions.
