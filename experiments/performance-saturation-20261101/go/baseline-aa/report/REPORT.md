# Go coordinator A/A campaign report

The frozen two-arm baseline/A/A campaign completed all 276 planned
invocations. All 120 measured fingerprint pairs matched, and counted
allocation evidence passed the preregistered A/A gate.

| Evidence | Status | Reason |
|---|---|---|
| Correctness fingerprints | valid | 120/120 measured pairs matched |
| B/op and allocs/op | valid | all six median ratios passed the fixed 0.98–1.02 gate |
| Wall and CPU time | invalid | 29/420 isolation samples were contended; 230/240 measured rows changed steal ticks |
| Candidate timing baseline | inadmissible | v2 forbids carrying a failed timing control into candidate claims |

The protocol SHA-256 is
`8120278e7c96fd2f6bc5a2ffa4a02f3e02f4668c492f3882a2b6a1d170adf696`.
Both arms used the byte-identical binary SHA-256
`5dd11a5911decbcfd2c8503ee00964c6cd473e99d48b0714176b19936e44f257`.
Six cases used three warmups and 20 fixed mirrored repetitions per arm at
exactly 100 benchmark operations each.

Raw per-invocation stdout, stderr, metadata, runner manifests, rows, summary,
and the isolation receipt are retained. A separately frozen A/B protocol on a
valid Tier-1 backend is required before making any candidate speed claim.

See [paired-ratios.md](../analysis/paired-ratios.md) for the retained ratios.
