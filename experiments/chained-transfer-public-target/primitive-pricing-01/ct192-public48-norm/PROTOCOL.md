# CT192 — all-48 actual pre-norm target operand pricing (prospective)

2026-11-17 UTC · draft PR #1735 stacked on CT191 #1734 · **[pcc:unverified]**

## Scope and frozen source

This experiment closes CT191's five-forward-point input limitation without changing the CT125 optimized evaluator, CT172 original public fixture, CT189/190 physical crossover, historical CT126 proxy, or 695/701 raw corpus. It is a **native-eligible instrument, not an executed price or complete ECDLP**.

Source identities: original CT125 norm-reuse Rust `fixed-jacobian-chain-evaluator-02/derived/lib.rs` Git blob `b80eb91a39ae1e87f0fcde95e52ea3d3634558bc`; original selected 48 JSON `evidence/fixed-chain-norm-point-native-01/literal-selected-vectors.json` Git blob `9ac741668dd1ffa9632ff0d58e6f4dd9f2dd18c3`; CT172 native 48 replay `ct172-replay/src/main.rs` (see original standalone evidence and full 21 counters); CT191 exact-path comparison PR #1734. The source-prime model is the existing 223 toy parameter, not the user's 2^31-1 benchmark.

## Pre-registered method

1. Build an **isolated derivative** of the pinned CT125 Rust source via a guarded Python materializer. Its new public diagnostic method reuses CT125's **same** `admit -> halves[0] -> corrected_lift -> gamma` path and returns only the pre-`norm_point` elliptic point, for either direct 169 or retained 13/13. No source scalar is used in the arithmetic. It checks that recomputing the original full route returns the *same norm* and *identical 19-word target class* as the frozen public record. In particular, do not substitute a scalar-derived generator multiple or a public target norm for the pre-norm operand.
2. The existing public 48-vector object must validate 2 directions × 4 cofactor sectors × 6 external *labels*, 8 identity and 40 nonzero cases, exact model field tags, canonical 19-u32 keys, all 21 original counters and route output equality. A label `scalar_OUTSIDE_runtime` may appear only in the serialized audit metadata and roster keys, never in `pmul`, `generator`, `admit`, `gamma`, or any norm operand builder.
3. For every one of the 48 inputs and **both physical routes**, precompute the real target-point operand using the diagnostic method; verify `N2_actual(P)=descend_point(pmul(P,2)) == descend_point(padd(P,P))`. Revalidate original public input, both complete target outputs, all original native counters and same target norm. Preserve unusual infinity/torsion, both directions, every sector separately.
4. Compare `N2_actual` against `D_padd` with 4 warmup + 12 measurement blocks per operand, alternating ABBA/BAAB, 64 repetitions per treatment; both treatments consume the **same** precomputed operand. Keep raw per-block times in integer decimal nanoseconds, no statistic-only evidence. A/A and differential runtime-stability controls remain required in the separate external cold collector. This **warm** panel never by itself establishes a speedup. `black_box` results; record process setup, provenance, Linux VmHWM, immutable input hashes, route, direction and sector.
5. Guard exact original blob identities, exact allowed source injection, complete 48 roster, mutation cases (missing/duplicate rows, changed keys, scalar-as-secret use, changed norm call, changed path/dependency and unexpected source modification). Run Python normal and `-O` source tests only; no native Rust in CI. A materialization/build command is a plan until admitted via existing original CT141/owner budget rules.

## Interpretive boundaries and next gate

This source derivative is producer instrumentation and **not** independent arithmetic or signed PCC. It neither authenticates the original 695/701 object-store custody nor proves that a transfer reduces single-target ECDLP. Null, negative, exceptional and failed cases must remain explicit.

Next gates: native Rust typecheck/link, independently authenticated original corpus custody, complete 48-source exact-counter replay, authorized same-host randomized paired prices `C169,C13a,C13b,N2_actual,D_padd`, plus complete cold source-prime rho/BSGS/IC and transferred candidate on identical public targets. Charge startup, geometry, transfer, inverses, corrections, linear algebra, individual log recovery, full verification, peak memory and uncertainty; success needs independently signed PCC and reproducible baseline/candidate >1. Do not initiate any paid computation, protected merge, admission override, ledger rewrite or claim a measured advantage from these source files.

Sources checked: crypto #3877, #4215; cryptanalysis #1523, #1729 (CT189), #1732 (CT190), #1734 (CT191); CT172 Rust source, CT173 source-path audit, CT125 derivative and immutable selected vectors. Shared research-KB MCP, the autoresearcher lead-atlas CLI and authenticated corpus are inaccessible in this connector-only session; no novelty claim follows from that search limit.
