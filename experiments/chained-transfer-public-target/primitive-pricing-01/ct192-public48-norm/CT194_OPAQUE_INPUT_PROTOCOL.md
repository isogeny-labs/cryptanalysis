# CT194 — input-opaque repeated primitive pricing (prospective)

2026-11-17 UTC · draft [cryptanalysis #1738](https://github.com/isogeny-labs/cryptanalysis/pull/1738), stacked on CT193 #1737 / CT192 #1735 · **[pcc:unverified]**.

## Threat to valid native primitive prices

The CT192 Rust driver iterates 64 times over the **same** public `point` and applies `std::hint::black_box` only to the *computed output*. In particular, `curve::padd(&target.f, &target.curve, &point, &point)` is a pure computation of an invariant input. Source structure alone does not prevent an optimizing compiler from moving that calculation out of the repetition loop and feeding the resulting value repeatedly to the output `black_box`. `N2_actual` also has a counter side effect and may optimize differently. A measured difference could therefore contain a compiler-optimization artifact. This is a **prospective confounder**, not an observed hoist: no optimized/native assembly or timing evidence exists.

## Exact proposed change

For **both** `N2_actual` and `D_padd`, perform `let measured_operand = black_box(point);` inside the inner repetition loop, immediately before the treatment dispatch. Every invocation then uses `measured_operand`, and every result remains passed through `black_box`. Keep fixed public 48 packets, two physical transfer routes, exact full-class and native 21-counter preflight, original CT125/CT192 constants/fixtures, 4 warmup + 12 measured ABBA/BAAB blocks, 64 repetitions/slot, 4,608 scheduled measured slots, and the admission boundary unchanged. Source scalar labels remain audit metadata only.

Require source tests that reject removing the input barrier, putting it outside the 64-iteration loop, or using the opaque operand in only one arm. Require normal and optimized Python source guard tests and generated Rust parsing, while retaining original source SHA/provenance constraints. A future *native* disassembly/assembly review must establish that the actual math executes every iteration under the precise release profile. Input `black_box` has nonzero overhead, which must be characterized with an identically structured placebo control, not silently subtracted.

## Failure and scope

No native compile or compute is authorized by this change. A test pass only demonstrates guarded source text, not that an optimizer was hoisting, not a native arithmetic replay, and not a timing result. Keep all failures. Cold same-host measurement must include source hashes, host/affinity, sham/randomized physical arm and block-fixed-effect controls (CT187/188/190), and independently authenticated 695/701 custody. Only actual `C169,C13a,C13b,N2_actual,D_padd` pricing plus identical-target complete rho/BSGS/IC/transfer solves with all setup, LA, memory and confidence/PCC may justify a complete advantage claim.

## Source inspection

Original CT125 `fixed-jacobian-chain-evaluator-02/derived/lib.rs` (Git blob `b80eb91a39ae1e87f0fcde95e52ea3d3634558bc`); CT192 driver `ct192-public48-norm/src/main.rs`; CT193 class-binding guard #1737; [cost frontier crypto #4215](https://github.com/isogeny-labs/crypto/pull/4215). Shared research-KB and locked source corpus unavailable in this tool environment. No novelty or benchmark claim. **[pcc:unverified]**.
