# CT309 — preregistered full-native primitive/wall nesting admission (2026-11-22)

**Scope:** Existing draft [#1912](https://github.com/isogeny-labs/cryptanalysis/pull/1912); source-only integrity amendment before any native experiment. Scientific standing [pcc:unverified].

## Source-observed defect

CT304 currently checks two producer-supplied receipt wall times are positive, raw stdout/stderr hashes match their receipts, full original/reuse populations pass CT302, and CT248 scoped clocks reconcile with the optimized runtime lifetime clocks. However CT304 never checks whether the total **in-process** seven-slot primitive intervals from the optimized runtime could fit inside its externally captured process wall time. CT302 compares scoped intervals only to lifetime intervals, so a producer can claim an external wall duration of 1 ns while preserving nonzero internally measured intervals and matching its own changed receipt hash. This is a consistency defect, not an observed forged authentic record or evidence of actual runtime.

Prior work checked a similar but different single-packet CT175/CT179 timer nesting in CT180. CT309 applies the missing check to CT304's **entire 695-record / 144-sample native process**, without altering the smaller CT180 or its semantics.

## Frozen prospective remedy

1. Only after successful CT304 raw-byte/receipt authentication and CT302 full-population/schema validation, read the **one** `CT244_PRIMITIVE_TIMING` lifetime row in the optimized raw stdout using duplicate-key and nonfinite-constant rejection. The existing CT248 guard already requires exactly seven nonnegative integer `elapsed_ns` slots and reconciles all 144 selected epochs into them.
2. Require `sum(lifetime.elapsed_ns) <= optimized_receipt.external_wall_ns`. This bound is valid for the current single-threaded CT244 native evaluator if seven timed primitive call intervals are disjoint and contained in the captured process lifetime, on a host where Rust `Instant` and external `perf_counter_ns` measure comparable monotonic durations. Do not assume this for concurrent/nested clocks, multiple native processes, or uncalibrated cross-host clocks.
3. Refuse a claimed `external_wall_ns` below that sum, including a synthetically forged, internally consistent SHA/length receipt. Retain complete original/reuse mathematical validation, exact binaries, role and host gates; do not use this bound to infer a performance advantage.
4. Source-only positives: exact frozen 48 selected vectors plus explicitly synthetic 694 other records and 144 samples with either zero clocks or one positive C169 clock in an otherwise unchanged 695-record transcript. Negative: same valid positive-clock transcript paired with a source-consistent receipt that claims an impossible shorter wall. Run in normal and optimized Python; preserve old controls. The source-only test cannot become timing evidence.

## Gates and exclusions

Original authenticated six-object S3 provenance, approved tool/config parity, valid STS, native Rust semantic compilation and execution, 695/701 arithmetic parity, physically calibrated C169/C13a/C13b/D/N2_actual, all-phase cold single-target IC and strongest rho/BSGS comparisons including memory, uncertainty and signed independent PCC remain required. No AWS, EKS/Spot, new binaries, original model, source fixture, or signed ledger changes are authorized. [pcc:unverified].
