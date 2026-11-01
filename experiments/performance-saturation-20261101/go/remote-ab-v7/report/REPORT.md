# Go coordinator remote A/B v7 report

The frozen overall verdict is **`unsupported`**.  The candidate is correct and
dramatically faster on all six registered scans, but it does not satisfy the
preregistered conjunction: allocation event counts fell by about 85.7%, short
of the required 95% reduction in every case.

| Claim | Result | Evidence |
| --- | --- | --- |
| `C-ab-correct` | supported | 120/120 measured fingerprint pairs match |
| `C-ab-allocation` | unsupported | B/op ratios are 0.00055-0.00106, but allocs/op ratios are 0.14290-0.14349, above 0.05 |
| `C-ab-timing` numeric sensitivity | passes | medians are 14.79x-16.63x; conservative family lower bounds are 14.58x-16.44x |
| `C-ab-timing` formal interpretation | conditional | the runner's mechanical timing gate passes, but v7 did not numerically define material PSI or explicitly attest L2 |
| Overall frozen vocabulary | `unsupported` | `allocation_only` is impossible because allocation failed; `supported_within_scope` would imply both comparative claims passed |

All 276 planned invocations completed: 36 warmups and 240 measured rows in the
fixed mirrored order, exactly 100 operations each.  Both arm tests passed,
every raw member matched the 841-entry archive manifest, both exact binary
hashes matched, and the remote source commit/tree were
`45bb49aaa28da23232cf84ac08d57e536c6482e6` /
`8bc996dc46517e8cb85aa0fdb7710c6d1cb359da`.  The isolation record reports
zero measured steal deltas, zero cgroup throttling, unchanged affinity, no
memory-event increments, and the exact 64,000,000,000-byte memory limit.  Pod
`ol7fl01jrbvtyc` was deleted by exact ID and its absence was verified.

## Analysis status

The exact ratios and deterministic bootstrap calculation are retained in
[`../analysis/paired-ratios.json`](../analysis/paired-ratios.json) and
[`../analysis/paired-ratios.md`](../analysis/paired-ratios.md).  The analyzer
verifies the receipt, archive/member hashes, complete row inventory, mirrored
order, binaries, raw artifacts, fingerprints, and isolation mechanics before
computing ratios.

The analyzer was created after the rows existed.  V7's frozen
`analysis_plan.script` is null, and the protocol did not pin bootstrap count,
RNG, CI construction, or the exact Holm procedure.  Its exact rational
Bonferroni bounds are a disclosed sensitivity analysis.  They cannot repair
that preregistration gap.  Likewise, the timing claim remains conditional on
accepting the runner's `timing_valid: true`, because the words “material PSI”
and “L2” lacked numeric/attestation fields.  Neither limitation can change the
overall `unsupported` result caused by the allocation-count gate.

To reproduce from a fresh temporary directory, extract
[`../../evidence/remote-run-v7/result.tar.gz`](../../evidence/remote-run-v7/result.tar.gz)
and run:

```sh
python3 experiments/performance-saturation-20261101/go/analyze_remote_ab.py \
  --run /path/to/extracted/go-ab-v6-run \
  --protocol experiments/performance-saturation-20261101/go/protocol.v7.json \
  --receipt experiments/performance-saturation-20261101/go/evidence/remote-run-v7/http-receipt.json \
  --archive experiments/performance-saturation-20261101/go/evidence/remote-run-v7/result.tar.gz
```

## Sources and scope

The analysis checked the frozen v7 protocol, the repository's
[`LITERATURE.md`](../../LITERATURE.md), `docs/COORDINATOR.md`, `docs/FFI.md`,
the Go benchmark/allocation guidance linked from the literature note, and the
retained RunPod receipt/archive.  Those sources require exact delta/vector
semantics, fixed operation counts, allocation reporting, and separate
diagnostic versus decisive evidence.  No new algorithmic novelty is claimed.
The result applies only to the six fixed Go wrapper scans on this cpu3c host
class; it is not a whole-coordinator throughput claim.

The next registered candidate should target the measured one-allocation-per-log
entry slope, freeze an actual analyzer, and add an unambiguous `timing_only`
terminal label before collecting new rows.
