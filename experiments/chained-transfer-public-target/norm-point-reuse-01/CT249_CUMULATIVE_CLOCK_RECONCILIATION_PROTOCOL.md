# CT249 — reconcile scoped primitive timings with native lifetime clock (prospective)

**Date:** 2026-11-19 America/Denver. **Standing:** [pcc:unverified]. Protocol frozen before implementation and before native input. Continue existing draft PR #1871; no new fixture, model, paid compute, or original evaluator modifications.

## Question and currently unguarded gap

CT248 validates 144 arm-local sample records against the 48 selected vector counters, but its `decode` ignores the existing `CT244_PRIMITIVE_TIMING` runtime-lifetime event. Consequently the CT248 auditor can accept a modified, incomplete, or duplicated set of *elapsed times* (with valid counts) even when those scoped totals contradict the producer's independent cumulative record. The cumulative record is written by the same generated Rust instrumentation, so cross-checking it is a useful **internal consistency check, not independently reproduced time** or a PCC signature.

## Frozen acceptance contract

1. Require exactly one `CT244_PRIMITIVE_TIMING` JSON object from the same single-test combined original stdout/stderr log, in addition to exactly 144 `CT248_PRIMITIVE_SAMPLE` and one original 48-vector event. Refuse missing/duplicate lifetime clock events. Do not accept CI grep echoes as independent records.
2. Demand exact `ct244-primitives-v1` schema; the seven ordered direction labels `C13_0_to_1,C13_1_to_0,C13_1_to_2,C13_2_to_1,C169_0_to_2,C169_2_to_0,D_target_norm`; the original lifetime scope `runtime_lifetime_after_constructor; eval-only; uncalibrated`; `measured_complete_solve=false`; `pcc=unverified`; and `scoped_samples_emitted=144`. Strict JSON object keys, nonnegative integer arrays of length seven, and Boolean-as-number rejection are required.
3. For each of seven primitive directions, `lifetime.calls[j] >= sum(sample.calls[j])` and `lifetime.elapsed_ns[j] >= sum(sample.elapsed_ns[j])`. These are **necessary but not sufficient** by additive clock implementation; out-of-epoch map and norm work contributes to the lifetime totals and must not be silently attributed to any selected arm. For uncalled lifetime slots, require lifetime nanoseconds zero. Return both scoped and residual counts/nanoseconds without promoting them to route or ECDLP costs.
4. New synthetic positive control must have nonzero outside-epoch work and pass; a zero-extra control must also pass. Mutation controls reject dropped/duplicate/mistyped cumulative records, incorrect labels or scope, smaller cumulative counts/times than scoped, false complete-solve/PCC standing, inconsistent emitted sequence, and nonzero time on uncalled directions.
5. Keep CT248's source-counter parity and exact 48-row route ordering checks. Do not alter generator, original full 695/701 records, 48-packet contents, or any cost formula. Run normal and `python3 -O -S` hosted source-only controls on exact PR head; native model hydration remains gated by valid AWS STS and six exact SHA/length checks.

## Decision and limits

A passing audit would only establish **synthetic guard coverage** until genuine full native logs exist. Even genuine logs establish producer-instrumentation consistency rather than independent physical reproduction. No measured `C169/C13a/C13b/D/N2_actual`, A/A, ABBA, optimized rho/BSGS/frontier IC, memory, complete cold target solve, or signed PCC is implied. The direct–retained primitive expression comparison remains `C169 - C13a - C13b`; `D` cancels. An observed negative route or complete ratio must be retained, not relabeled a success.

**Sources checked:** cryptanalysis #1871 CT244/CT248 generator, CT248 auditor and pinned selected source-test blob `bcd27773a7b179c3beeb3d5782a5de97a7df19f2`; cryptanalysis #1533, #1748; crypto #3877, #4215, #4715, tracking issue #3904. No research-KB result asserted.
