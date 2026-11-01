# CPU baseline/A-A v3 report

Status: `invalid_exactness_or_provenance`. This campaign supports no timing,
non-regression, or speedup claim.

The v3 build and registry gates passed. The retained Rust and C executables
matched the frozen artifact manifest, both registry commands exited zero, the
10 intended Rust IDs existed, and the complete C registry matched all 34 frozen
IDs in order.

The first wall session then proved that the frozen Rust cell set was not the
cell set executed. `perfindex.py` applies each `--filter` as a substring
(`scripts/perf/perfindex.py:132-140`). Consequently the frozen filter
`gf2_la/rref_random_4940x8357` selected both that ID and
`gf2_la/rref_random_4940x8357_w17`. The unexpected suffix variant completed an
A/B pair in round 1. The session was interrupted immediately after the mismatch
was observed. Nine planned pairs and one unplanned pair had completed; their
partial clocks are inadmissible and will not be reused.

No C wall session, four-thread wall session, Callgrind run, perf-stat run, or
perf-record run started. Because interruption prevented `isolated_bench` and
`perfindex.py` from completing, no isolation receipt or `compare.json` was
emitted. The exact progress/traceback text returned by the executor is retained
alongside an explicit record of those absent files.

Immutable evidence:

- v3 registration: `24ce34273f780c6d24e03a0ce7d34c2ccc8ef0b1`
- v3 freeze: `b944b42c85c77dfac71f07d52ce6ecfeea45fb15`
- v3 canonical protocol hash: `38e165778da0e3799f89a5513af107aa577e160687eec9a7b509c8d382803e0d`
- invalidation evidence commit: `9824211dc54f6be6dfb7883c379d4e93becf5922`
- invalidation receipt SHA-256: `f340114ee4b6c0633244dc49caa9ce18ca28667128c162bb6bdc8cfdebbd64c4`
- executor transcript SHA-256: `eefcbc204159f2538d09b9c0bbed68099089670cada23170c6aac09d442835d7`
- Rust/C registry SHA-256: `b225091d89a02e7400b01bb7704c1f358192049753d4bc279d70dcb352f194a0` / `eafa8c3f389a88115f05ba1c5b602fc3b199cc0a6c80ed71432917c59cc97d44`

A fresh additive protocol is required. It must bind a tested exact-ID selection
mechanism and newly built artifacts before any new wall invocation. Retrying or
repairing the v3 session is forbidden.
