# CT196 — Timed norm counter-observability protocol (frozen before implementation)

**Date:** 2026-11-17. **Standing:** [pcc:unverified]. **Parent:** CT195, cryptanalysis PR #1740; immutable CT125 source and frozen 48-vector fixture. No native benchmark performed or authorized by this protocol.

## Source-level defect hypothesis

CT195 validates that its instrumented `norm_point` increments `Cell<Calls>.transported_norm_doubling` during preflight, but after the timing loops the repeated counter writes are never read. The optimizer may remove unobserved writes (or otherwise change the timed call accounting), even though `N2_actual` outputs are consumed by `black_box`. Therefore CT195's intended real-vs-counter-neutral pricing may not actually charge the real counter writes. This is a *possible* compiler issue, not an observed miscompilation or an empirical performance claim.

Rust's authoritative `std::hint::black_box` specification says the barrier is **best-effort** and not a correctness mechanism: https://doc.rust-lang.org/std/hint/fn.black_box.html. The pinned CT125 `Calls` field is `u64` and is returned via `runtime.calls()`; producer sources: `experiments/chained-transfer-public-target/fixed-jacobian-chain-evaluator-02/derived/lib.rs`. Shared KB MCP unavailable in this runtime; repo CT125/192/194/195 source and the official Rust documentation are the scoped fallback. No novelty claim.

## Frozen expected arithmetic

For each of 48 public packets and 2 routes, the **original** panel has 16 blocks × 2 `N2_actual` slots per block × 64 repetitions = **2,048 actual norm invocations**. `D_padd` slots contribute zero `Cell<Calls>` changes. The **separate CT195 counter-neutral** panel has 16 × 2 × 64 = **2,048 additional actual norm invocations**, and its `N2_arith_no_counter` control must contribute zero.

Thus each of the 96 route operands must have independently observed full `Calls` structure exactly equal to `before + (2,048, 4,096)` in the `transported_norm_doubling` field after the respective original and control panels, with all 20 other fields unchanged. **4096 actual norm invocations per operand; 393,216 across all 96.** Every observed delta is emitted alongside the original two arrays and must fail closed before publication on mismatch. The reads and checks must occur **after** the timed loops, not inside them, to avoid introducing per-repetition checking overhead. The external benchmark roster stays 4,608 + 4,608 recorded slots (warmups included for counter-observation). The 48-packet fixture, CT125 source bytes, preflight class/norm equality, both transfer directions, all route labels and authorization gates remain unchanged.

## Implementation and sabotage contracts

- Introduce a single integral constant for actual norm calls per 16-block panel; use checked addition for expected `u64` counts if needed.
- Observe the full runtime counter object before both panels, between panels and after both panels, enforcing exact expected equality and returning error on mismatch. Use `black_box(runtime.calls())` at observation boundaries as a benchmarking hint, but never replace exact assertions with compiler hints.
- Emit the observed per-panel deltas into each raw operand record, and summarize totals only after all 96 operands pass checks.
- Add source-validation guards with at least three mutation controls: lost mid-panel observation, wrong expected norm count, and missing final counter check; do not weaken CT195 tests.
- Run source-only Python tests in normal and `-O` mode; neither asserts Rust typecheck nor native timing. On an admitted native build, check release assembly and compare raw matched-host timing with sham/physical crossover before interpreting any ratio.

## Outcomes and next gates

Whether the actual-minus-neutral timed difference is positive, null or negative, retain the result. Even exact live counter parity does not prove that the optimizer executed one increment on every iteration; **release disassembly is still mandatory**. Authentic 695/701-record custody, all-48 native Rust arithmetic replay, same-host C169/C13a/C13b/N2_actual/D pricing, full cold single-target ECDLP including transfer, setup, linear algebra, recovery, verification and memory, matched strongest rho/BSGS/IC, uncertainty and independently signed PCC all remain outstanding. No paid compute or merge-gate bypass is authorized.
