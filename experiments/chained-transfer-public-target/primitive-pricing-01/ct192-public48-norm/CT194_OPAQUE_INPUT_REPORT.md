# CT194 — source-level mitigation for loop-invariant primitive timing

2026-11-17 UTC · [draft cryptanalysis PR #1738](https://github.com/isogeny-labs/cryptanalysis/pull/1738) stacked on CT193 #1737 and CT192 #1735 · **[pcc:unverified]**.

## Scientific question and source observation

CT192's 64-iteration price loop handed the same public `point` repeatedly to both operations, but only passed the resulting computation through `black_box`. A sufficiently optimizing compiler could hoist the constant pure `curve::padd` to outside the repeat loop, or otherwise specialize math for known inputs. The side-effectful CT125 `norm_point` counter may produce a different optimization path. This threatens the **relative price** `N2_actual/D_padd` even when the arithmetic results match. **No real compiler hoisting or timing bias has been observed.**

The Rust standard library explicitly recommends opaque *inputs and outputs* to defeat misleading optimizations in microbenchmarks, while warning that `black_box` is best effort and not a formal guarantee: [Rust std::hint::black_box](https://doc.rust-lang.org/stable/std/hint/fn.black_box.html).

## Implemented amendment

- The actual 48-packet Rust driver now performs `let measured_operand = black_box(point);` **inside** every repetition, before either physical treatment. Each `N2_actual` and `D_padd` invocation consumes that opaque operand; the output of both is still black-boxed.
- The existing CT193 full target-class equality and original CT125 source derivative are unchanged. The original 48-vector Git blob `9ac741668dd1ffa9632ff0d58e6f4dd9f2dd18c3` and the CT125 runtime Git blob `b80eb91a39ae1e87f0fcde95e52ea3d3634558bc` remain pinned by the inherited source audit.
- Added a fail-closed source-contract guard for the exact per-iteration barrier, placement before dispatch, identical input treatment on both arms and nonremoved output barriers. Three additional tests verify the positive path and reject missing/moved/asymmetric barriers.
- Preserved ABBA/BAAB schedule, 96 route-specific operands, 4 warmup + 12 measured blocks and 64 calls per slot. **4,608 slots remain planned and unexecuted.** Counters and full parity preflight remain as in CT192/CT193.

## Actual validation

[Exact-code CT192 source workflow #44203079646](https://github.com/isogeny-labs/cryptanalysis/actions/runs/44203079646) on commit `100f880620f8a456b9bd6802157517c456ed4f23` completed **success**. The decoded `source-only` job log reports **17/17 ordinary** and **17/17 `python -O`** tests passing. It also ran `rustfmt` parsing on generated CT125-derived Rust and the updated driver, frozen Git blob/fixture checks and manifest syntax checking. The new source tests passed and mutated guards were rejected.

These are *producer source checks*, not an independent PCC verdict. They do not establish a Rust link/typecheck, disassembly, actual executed repetition, same-host pricing, or an ECDLP solve. Broader repository CI and owner PCC remain separately gated.

## Follow-up and acceptance boundary

1. On the **approved**, exact pinned native Rust release build, inspect optimized assembly or trace actual primitive call counts per iteration for each arm, with a zero-work but equally input/output-black-boxed placebo baseline. Preserve compiler version/flags, disassembly hash and release-binary hash.
2. Authenticate the 695/701 corpus and replay every one of the 48 public packets, all expected canonical results and 21 counters **before** using its 96 point operands. On mismatches, stop and preserve the failed case.
3. Only then measure `C169,C13a,C13b,N2_actual,D_padd` with same-host sham and randomized physical crossover, block-fixed effects and uncertainty, and complete identical-target cold rho/BSGS/IC/transfer solving. Charge initialization, admission, geometry, correction, norm, inversion, relation collection, LA, target recovery, verification, startup and memory; require independently signed PCC and `baseline/candidate > 1` for any complete speedup claim.

No paid compute, native run, protected merge, frozen-fixture edit or actual speedup occurred. No inference for the `2^31-1` target is possible from this `p=223` source-only instrument. **[pcc:unverified]**.
