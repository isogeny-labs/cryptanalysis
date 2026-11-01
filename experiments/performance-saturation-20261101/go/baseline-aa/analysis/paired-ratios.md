# Go coordinator baseline/A–A analysis

Frozen protocol: `8120278e7c96fd2f6bc5a2ffa4a02f3e02f4668c492f3882a2b6a1d170adf696`.
All 276/276 invocations completed, and all 120/120 measured fingerprint
pairs matched exactly.

Counted allocation evidence passes the A/A gate: every median `B/op` ratio
is within `0.999999989..1.000000000`, and every median `allocs/op` ratio is
exactly `1.0`.

Wall and CPU evidence is invalid. The isolation receipt contains 29/420
contended samples (maximum other-process use `1.02` CPU-seconds/sample), and
230/240 measured rows have a nonzero steal-tick delta. The numerical clock
ratios are retained below but cannot support a timing claim or serve as a
candidate timing baseline.

| case | B/op A/A | allocs/op A/A | wall A/A (invalid) | CPU A/A (invalid) |
|---|---:|---:|---:|---:|
| `VersionVector/log_1024` | 1.000000 | 1.000000 | 1.002237 | 1.002206 |
| `VersionVector/log_8192` | 1.000000 | 1.000000 | 1.009976 | 1.009523 |
| `DeltaSinceCaughtUp/log_1024` | 1.000000 | 1.000000 | 0.992780 | 0.992877 |
| `DeltaSinceCaughtUp/log_8192` | 1.000000 | 1.000000 | 1.010912 | 1.011546 |
| `DeltaSinceOneBehind/log_1024` | 1.000000 | 1.000000 | 1.007460 | 1.001531 |
| `DeltaSinceOneBehind/log_8192` | 1.000000 | 1.000000 | 0.976935 | 0.976955 |

Verdict: `invalid_measurement` for clocks. Exact fingerprints and counted
allocations remain admissible within this fixed workload.
