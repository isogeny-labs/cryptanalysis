# RTX 5090 GPU A/A v7 report

The frozen v7 session is **`aa_calibration_admissible`**.  It completed the
exact one-pod design: 10 correctness-gated warmups, 60 unprofiled executions,
and two post-timing Nsys captures.  Both arms were byte-identical, every
shape/rank/refuted/pinned/word-operation check passed, the remote command
returned zero, and exact pod `wqywy6u8ckeja4` was deleted with absence
verified.

This is an A/A noise and profiler baseline.  It contains no optimization
candidate and supports no speedup, equivalence, or optimality claim.

## Bound evidence

| Binding | Value |
|---|---|
| Frozen protocol | `4b71152b91077781544520da18b0bafa4a762cf634be4c278867452c11e20c08` |
| Source commit / tree | `c6f7a0208e10823b7248c9138b7a46273990abe5` / `c4562cb6a2d72e549f5700feb870d9211b17fa56` |
| Source tar SHA-256 | `ee0d64e8fa7bb6b7a8dcd9e5fb161bc79d702fd5933f1ea30c1376c237dad694` |
| A/A binary SHA-256 | `1d956f19107477589e376bad46e3eb226d8d33905397a58caee160bced278452` |
| HTTP receipt SHA-256 | `053e6983c0c0fad8b72d35aaf22d3050763ede83e610e75da821677f3fc6dba7` |
| Result archive SHA-256 | `c69fae2f4ded148451c3492174cae6fec1d033e009a4f4e37fd71fdc99c011aa` |
| 396-entry archive manifest | `04885fe46b048a152aa0cd2bcffa9de46c2386dcc8a6f8a532f68367ea39a6fd` |
| Rows SHA-256 | `91dd95bf0528154f5a9e0c7f28697f4c79ad415130c5ca95ba5b623764e1f7b8` |

The archive has 397 regular, uniquely named members: the 396 manifest-bound
outputs plus the manifest itself.  Every member's bytes, SHA-256, and receipt
binding were independently checked.  The source ref was publicly checked,
the observed device was one RTX 5090 (`sm_120`, driver `595.91.07`), and the
provider placement was Secure Cloud at $1.19/hour.  The exact Nsys package was
installed before the runner; NCU was neither installed nor invoked.

## A/A device calibration

Ratios are current/control device time.  Intervals are the frozen analyzer's
exact ordinary paired-bootstrap intervals over all `6^6` resamples.

| Cell | Control median (ms) | Current median (ms) | Median pair ratio | Exact 95% interval |
|---|---:|---:|---:|---:|
| `k0n13m2d5` | 77.4 | 77.4 | 1.000000 | [0.999354, 1.000646] |
| `k0n9m3d5` | 44.9 | 44.9 | 1.000000 | [1.000000, 1.001114] |
| `k1n11m2d5` | 25.6 | 25.6 | 1.000000 | [0.997396, 1.001305] |
| `k1n11m2d6` | 240.9 | 240.95 | 1.000000 | [1.000000, 1.000208] |
| `k0n13m2d6` | 1785.1 | 1785.1 | 1.000140 | [0.999907, 1.000318] |

The exact answers matched in all 70 warmup/measured rows.  Arm order was
mirrored: control ran first in measured rounds 1, 3, and 5; current ran first
in rounds 2, 4, and 6.

## Nsys diagnostics

The two profiled primary executions were collected after the unprofiled gate
and do not enter the table above.

| Kernel | Control total (ms) | Current total (ms) | Share in each arm |
|---|---:|---:|---:|
| `f4e_update` | 922.553 | 922.649 | 51.66% |
| `f4e_panel_block` | 744.488 | 744.555 | 41.69% |
| `f4e_materialise` | 95.485 | 95.456 | 5.35% |
| `f4e_gather` | 23.315 | 23.308 | 1.31% |
| total kernels | 1785.847 | 1785.975 | 100% |

Both profiles contain exactly 2,941 launches of each main kernel.  The
byte-identical arms differ by only 0.007% in total profiled kernel time.

The primary upload remains a material, noisy end-to-end target.  Nsys records
one 3,961,244,664-byte **pageable** HtoD copy: 2.099 seconds in the control
profile and 0.701 seconds in the current profile.  Across the 12 unprofiled
primary rows the combined upload median was 711.8 ms, with a 654.1--3204.5 ms
range.  Because the arms are byte-identical, those differences are transfer
variability rather than an arm effect.  Any pinned-host-memory follow-up must
be separately frozen and judge complete matrix-stage time, including
registration/allocation and cleanup; it must not claim the faster A/A arm as
a candidate.

## Scope and sources checked

The report follows the separation in
[`LITERATURE.md`](LITERATURE.md): unprofiled rows decide calibration, Nsys is
diagnostic, and inaccessible NCU counters are not retried or silently omitted
from a counter claim.  The relevant primary guidance recorded there is the
[Nsight Systems User Guide](https://docs.nvidia.com/nsight-systems/UserGuide/index.html),
[NVIDIA counter-permission guidance](https://developer.nvidia.com/ERR_NVGPUCTRPERM),
and the [Runpod Pod API](https://docs.runpod.io/api-reference/pods/POST/pods).
The exact internal sources were the frozen v7 protocol, runner, analyzer,
installer, and v6 invalid-measurement record.

Reproduction and review pointers:

- [`v7-outcome.json`](v7-outcome.json) is the compact machine-readable verdict.
- [`evidence/remote-aa-v7/analysis.json`](evidence/remote-aa-v7/analysis.json)
  contains all paired ratios and intervals.
- [`evidence/remote-aa-v7/nsys-summary.json`](evidence/remote-aa-v7/nsys-summary.json)
  records the kernel and transfer diagnostics.
- [`evidence/remote-aa-v7/result.tar.gz`](evidence/remote-aa-v7/result.tar.gz)
  is the immutable full result.
