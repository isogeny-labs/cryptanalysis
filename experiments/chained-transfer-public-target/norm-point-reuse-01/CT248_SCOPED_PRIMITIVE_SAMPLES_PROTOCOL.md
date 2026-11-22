# CT248 — scoped primitive samples aligned to the frozen 48-vector comparison (prospective)

**Date:** 2026-11-19. **Standing:** [pcc:unverified]. This protocol is committed **before** CT248 implementation or runtime results. Continue existing draft cryptanalysis PR #1871; do not open a duplicate lane or touch the original 695/701 record schema.

## Diagnosed source-only gap

CT244's generated `Runtime` has one cumulative seven-slot clock, printed in `Drop`. However the pinned original test `src/tests.rs` (Git blob `bcd27773a7b179c3beeb3d5782a5de97a7df19f2`) invokes `reset_calls()` **before each** of three comparative arms and `calls()` **after each** arm, 48 selected vectors × 3 = 144 snapshots. Neither operation resets or snapshots the CT244 clock. Therefore one runtime-lifetime clock mixes all cofactor/setup/exceptional/control and candidate routes; it cannot price direct169 vs literal13×13 vs retained13×13 on paired selected rows. This is an instrumentation scope defect, not a reported arithmetic or speed result.

## Narrow additive repair

1. Keep the original exact evaluator blob `8016634385d76207b23a3eb3a4dae9b0366ac68d`, existing CT125 transformer and all 695/701 records unchanged. Guard the original selected-vector test source blob `bcd27773a7b179c3beeb3d5782a5de97a7df19f2` and 3 reset/3 read anchors before generating the separate `fixed-jacobian-chain-priced-01` sibling.
2. Retain the existing CT244 *lifetime* clock unchanged. Add an independent, zero-initialized **epoch** seven-slot clock and a checked sample sequence; increment both clocks only around the same real six `Rational6::eval` directions and same target `curve::padd` doubling.
3. Only when `CT244_PRIMITIVE_TRACE=1`, each original `reset_calls()` also zeros the epoch clock; each original `calls()` emits one **separately namespaced** `CT248_PRIMITIVE_SAMPLE` JSON object with exact monotonic sequence number, seven epoch counts/ns, and the three original per-arm counters. No extra map/halving/verification calls and no changed original counter values.
4. **Fail closed at readout:** sum the four C13 slots, two C169 slots and D slot with overflow-safe arithmetic; require exact equality to the source `degree13_elliptic_evaluation`, `degree169_elliptic_evaluation`, and `norm_point_doubling` in the current reset-to-readout epoch. A mismatch panics rather than presenting a misleading physical price. Leave lifetime/drop trace present but clearly unpaired.
5. With tracing off, preserve counter results and all original stdout; the epoch branch does no work other than the off-state check. With tracing on, require **144** ordered selected arm sample events; a downstream verifier, not a label invented by the generator, checks route sequence `direct, literal, retained` per the pinned test. Any different sample count/order, type aliasing or unexpected route call counts fails auditing.
6. Extend Python normal and `-O` synthetic mutation controls to reject erased/duplicated `reset_calls` or `calls` anchors, altered original source blob, and wrong original test source. Run only source generation and Rust syntax format in bounded GitHub-hosted CI; native semantic typecheck remains dependent on approved original six-object S3 credential restoration.

## Interpretation/limits

This repair makes **route-local** physical timing *possible*; it provides **no timing**, uncertainty or speed evidence itself. The clocks measure eval/doubling expressions, not admissions, field transitions, source maps/\(\Phi\), corrections, halving, final Jacobian norm, setup, RSS, IC linear algebra, or verification. Printing/timer overhead requires an A/A control and isolated same-host ABBA. The original 695/701 strict parity, six-object manifest custody, full cold **single-target** ECDLP comparison against optimized rho, BSGS and frontier IC, independent native replay and signed PCC remain mandatory. No AWS secret mutation, unapproved EKS/Spot compute, protected merge, or gain claim.

## Exact negative/positive decision

- Source/check fails: repair source only; preserve original custody and failure logs.
- Valid 144 epoch samples but nonpositive conservative primitive route delta: record negative, abandon unchanged norm-reuse optimization.
- Positive physical delta: proceed to isolated full-route and complete ECDLP pricing; never promote from clocks alone.
- Authentication still rejects STS: do not repeat unchanged S3 calls; continue unblocked source verification and independent transfer work.

**Sources checked:** original evaluator and original selected-vector tests on cryptanalysis PR #1871; CT244/245/246/247 source and redacted CI, CT125 #1533, earlier frozen CT198 route attribution #1748, crypto #4215, CT243 negative crypto #4715, root #3877 and tracking issue #3904.
