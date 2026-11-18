# CT195 — source-tested norm-point counter bookkeeping decomposition

2026-11-18 UTC · [draft PR #1740](https://github.com/isogeny-labs/cryptanalysis/pull/1740), stacked on CT194 #1738 · **[pcc:unverified]**

## Concrete finding (source observation, not native performance)

The original CT125 norm method `norm_point(to, point)` first runs `self.bump(|c| c.transported_norm_doubling += 1)` and then `descend_point(curve::pmul(&target.f, &target.curve, &point, 2))`. CT125's `bump` operates on a `Cell<Calls>` holding the entire 21-field `Calls` struct; the CT192 `N2_actual` branch includes the bump, while `D_padd` does not. CT194 addressed compiler input hoisting but did not isolate this accounting difference. This is **a potential bias in attribution**, not evidence that native counter manipulation is nonzero or that a transfer is faster.

Source: [pinned CT125 Rust](https://github.com/isogeny-labs/cryptanalysis/blob/research/ct194-opaque-input-timing-20261117/experiments/chained-transfer-public-target/fixed-jacobian-chain-evaluator-02/derived/lib.rs) Git blob `b80eb91a39ae1e87f0fcde95e52ea3d3634558bc`. Rust [Cell<T> behavior](https://doc.rust-lang.org/std/cell/) and [best-effort black_box](https://doc.rust-lang.org/std/hint/fn.black_box.html).

## Implementation and guard

- Frozen [CT195 prospective protocol](CT195_COUNTER_NEUTRAL_PROTOCOL.md) in commit `7cbbf7a3` **before** touching the Rust code. Added only an isolated guarded derivative method `ct195_arithmetic_norm_no_counter`, executing the identical scalar-2 point arithmetic and descent but without `bump`. The original `norm_point` and CT125 raw pinned source remain unchanged.
- For every one of 48 frozen public Jacobian classes and both physical routes (96 prospective operands), native preflight now requires the neutral result equal the real norm, neutral evaluation leave *all* 21 counters unchanged, and the real norm change **only** `transported_norm_doubling` by one. Exact original full-class equality, 19-word output, 21 call counters and original selected roster remain required before timing.
- Preserved the original CT192 `N2_actual/D_padd` panel as distinct `raw_slots`: **4,608 recorded timing slots planned, zero executed**. Added `counter_control_slots` for matched `N2_actual/N2_arith_no_counter`, another 4,608 planned: total 9,216 recorded, excluding warmups. Every call uses an opaque public input and output. Each has 4 warmup and 12 measured four-slot blocks per operand, 64 repetitions per slot. The entire second panel requires a distinct `CT195_EXTRA_PANEL_ADMISSION_RECEIPT` **in addition to** the original CT192 receipt *before* work starts. Environment values alone do not authenticate real owner/provider approval.
- A distinct `ct195-* /v1` schema prevents treating augmented records as the original v1. Added source-validator and 3 tests covering actual arm/neutral source equality, mutation of arithmetic-only path, lost admission receipt, altered counter assertion, absent raw panel, and barrier bypass. All original corpus/Git blob pins are unchanged.

## Evidence and failures

**Exact-source scoped CI:** [workflow #44211422013](https://github.com/isogeny-labs/cryptanalysis/actions/runs/44211422013) on code head `e976ca385172d46845e5a2a8d00d88ffb1849fcc` **passed**. Decoded source-only job `134490470901`: 20/20 Python tests in normal mode and 20/20 with `python -O`, guarded exact Git-blob checks, derivative materialization, `rustfmt` syntax parsing on generated Rust and main, Cargo TOML parser. [CT126 source guards #44211422010](https://github.com/isogeny-labs/cryptanalysis/actions/runs/44211422010) passed. The earlier [source CI #44211366854](https://github.com/isogeny-labs/cryptanalysis/actions/runs/44211366854) failed 3 mutation-test subcases because their byte literal held escaped newlines instead of newline bytes; fixed at `e976ca38` without weakening the test, and final scoped CI passed. Other inherited broad workflows and PCC have failures or were pending; a scoped pass does not satisfy them.

**No native Rust typecheck, link, disassembly, all-48 arithmetic replay, same-host timing, original 695/701 custody, signed PCC, paid EKS/Spot run or complete ECDLP solve.** The extra 4,608 planned slots have no acquired compute authorization. This source-only p=223 instrument cannot be extrapolated to 2^31−1.

## What would distinguish explanations

On an independently approved pinned host, first check release assembly that both measured paths really execute one arithmetic norm per iteration and that the real path's counters remain observable. Authenticate original corpus and replay all 48 exact packets/counters before analyzing a panel. A measured norm ratio between real and neutral paths (with sham and random physical crossover/block controls) would isolate **instrumentation overhead under that build**; a null must be retained as a null. Only after same-host native `C169,C13a,C13b,N2_actual,D`, full cold identical-target transfer/rho/BSGS/IC solutions, setup/geometry/inversions/LA/recovery/verification/RSS, uncertainty and independent PCC can a complete speedup be considered.

Scientific status: **source implementation checked; native cost sign and magnitude unknown; full ECDLP objective open; [pcc:unverified]**.
