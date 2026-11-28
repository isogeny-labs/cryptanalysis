# Paired x-filter integration pilot

The protocol was committed and published in draft PR #2013 before the
recorded pilot. The candidate patch is retained as `candidate.patch` (SHA256
`23d3812bd290bd115b3f24065244b06e57610039267f52e3f7fbc68a3dcf7573`);
it was **not** promoted into the core crate because the preregistered 1.5x
pilot gate failed. Candidate `pair_index.rs` SHA256 was
`63902b3b55d2961dc5ec3a4bd6f4a696b449c1f5496fb4c00dbf1d233593024d`.
The recorded pilot has three alternating four-arm blocks, six fresh
processes per path, on the frozen public target 0, seed 0, interval B384,
m=3. All 12 arms solved and independently checked `[k]G=Q`; all 12 report
the same scalar, query count 10,386, relation count 358, matrix rank 357
and byte-equivalent canonical certificate. The differential tests over
all finite points of a small curve, odd chunks and a 385-column no-bitmap
M31 base passed. The existing full Rust test suite also passed with the
candidate. An earlier four-child smoke ran without saved stdout; it is
excluded from these statistics.

| Arm | Median charged wall | Median charged CPU | Median online | Exact lookups |
|---|---:|---:|---:|---:|
| Generic batch control | 102.929 ms | 102.277 ms | 92.773 ms | 7,774,414 |
| Paired x-filter candidate | 102.628 ms | 102.132 ms | 92.858 ms | 1,019,867 |

The ratio of separate wall medians was 1.0029 and of CPU medians 1.0014,
far below the predeclared 1.5 threshold. The candidate reduced counted
exact table lookups by 86.9%, but paid for the paired scan and bitmap
filter while leaving candidate arithmetic and relation work unchanged.
These observations identify a bottleneck shift, not a full-pipeline gain.
Raw CSV SHA256 is
`1396740c86fc45fdfda7d8e9cb214f571db4102b7ec2e0f325616f39d18079f1`;
each stdout/stderr and binary hash is retained. A four-term or larger-base
result cannot be inferred from this m=3, B384 pilot. The prior separate
fused-native collector achieved 12–15% charged benefit on its own
workload; this result does not dispute it. Algebra and certificate semantics
were unchanged, so a new Lean theorem about timings or lookup counts would
not establish a cryptanalytic improvement.
