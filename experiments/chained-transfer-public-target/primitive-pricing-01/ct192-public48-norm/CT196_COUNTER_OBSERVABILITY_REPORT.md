# CT196 — Timed CT125 norm-counter observability report

Date: 2026-11-17 (America/Denver). Standing: **[pcc:unverified]**. Draft [cryptanalysis PR #1743](https://github.com/isogeny-labs/cryptanalysis/pull/1743), stacked on CT195 [#1740](https://github.com/isogeny-labs/cryptanalysis/pull/1740).

## Concrete source finding and correction

The CT195 native-eligible instrument checked `Cell<Calls>.transported_norm_doubling` exactly before timing, but made no post-timing read. Rust may eliminate unobserved bookkeeping writes or change how they are performed even when arithmetic outputs are opaque. This is a possible benchmark confounder, not an observed native compiler behavior. The original CT125 method is unchanged and continues to update this `u64` via `Cell<Calls>`.

CT196 adds **three observations per route operand** around the existing 16-block original and 16-block counter-control panels. Each is `black_box(runtime.calls())` *outside* the timed slots. Full 21-counter equality must hold against the prior observation with exactly +2,048 transported norm doublings per panel and zero changes to all other counters. Checked integer arithmetic refuses overflow or regression. Each raw operand JSON record includes both separately observed deltas, with a fail-closed aggregate 393,216 actual norm invocations across 96 route operands. The output schema is deliberately versioned `ct196-public48-observed-norm-counters/v1`, avoiding misclassification as CT195 v1.

**Expected counts are structural arithmetic, not empirical measurements:** 16 blocks × 2 actual-norm slots × 64 calls = 2,048 each panel; 2 panels × 96 operands = 393,216. The original 4,608 + 4,608 planned **recorded** timing slots and all warmups remain untouched; no slots were run in this session.

## Checked scope

The guarded source tests and negative mutations were extended, retaining previous exact Git-blob checks for CT125 (`b80eb91a39ae1e87f0fcde95e52ea3d3634558bc`) and original selected 48 fixture (`9ac741668dd1ffa9632ff0d58e6f4dd9f2dd18c3`). Three additional test cases require correct observation points, precise 2,048-call expectations, full counter assertions and non-silent evidence fields.

At implementation head `b0a7ef23debc7e3062af84bc032322186e4f2bf7`, [CT192 source-only workflow 44219444122](https://github.com/isogeny-labs/cryptanalysis/actions/runs/44219444122) passed: 23/23 normal Python and 23/23 optimized Python tests, with normal hosted parsing/fixture checks. This is **producer source validation only**, not independent native arithmetic or PCC.

The shared KB MCP and local native Rust/Cargo were unavailable; source fallback was CT125/192/194/195 repo files and [Rust's `black_box` official reference](https://doc.rust-lang.org/std/hint/fn.black_box.html). Its best-effort semantics expressly do not certify per-iteration machine instructions; a native release build and disassembly are mandatory before interpreting a timing ratio. No claim of a compiler defect in an executed binary is made.

## Blockers and exact next decision

- Authenticate original 695/701-record custody from its independently signed source and validate 48/48 packet/counter/class parity in actual released native Rust, after the correct owner/provider admission. Do not infer it from the selected 48 fixture alone.
- Inspect release disassembly to confirm the actual norm bookkeeping is executed in the priced code; verify the newly observed +2,048/+2,048 live `Calls` deltas for every source packet and direction. Compare paired same-host C169, C13a, C13b, N2_actual and D with a separate controlled A/A arm and physical crossover. Retain negative and null findings, with confidence intervals.
- Compare **complete cold single-target ECDLP** on identical targets against the strongest optimized rho, BSGS and available IC, counting all setup, transfer, linear algebra, recovery, verification and peak RSS. A ratio above one is not a result until independently reproduced and PCC-signed. Do not extrapolate the p=223 fixture to prime p=2^31−1.
- Leave PR draft while full CI, PCC and native correctness/compute gates are unresolved. CT195's extra benchmark panel needs its own prior compute approval. No paid EKS/Spot, merge or gate bypass.

Conclusion: **source-level benchmark-accounting integrity improved; native performance sign, complete ECDLP advantage and PCC remain unknown [pcc:unverified].**
