# CT244 — exact-source physical primitive instrumentation (preregistered 2026-11-19)

**Standing:** [pcc:unverified]. This file precedes CT244 implementation and all measurements. The sole purpose is to make the original 695-record Jacobian experiment's *actual* C169, directed C13, and target-norm doubling work measurable, without modifying its mathematical outputs, original pinned source, or existing CT125 derivative.

## Source custody

- Parent consumer: cryptanalysis PR #1533, head `9fe4f3683b16c3cf6e3f0805be16a234e0ec0f33`.
- Original `fixed-jacobian-chain-evaluator-01/src/lib.rs` must match Git blob `8016634385d76207b23a3eb3a4dae9b0366ac68d`.
- Reconstruct the already published CT125 derivative in memory using its pinned transformer. Copy the original package to a **new** sibling `fixed-jacobian-chain-priced-01`; do not edit the original, the CT125 sibling or frozen 695 / 701 records.
- Instrument the *real* elliptic rational-map `Rational6::eval` in `Runtime::gamma`, separately for all six directed pairs; instrument the *real* `curve::padd` for `[2]Z` inside `norm_from_target_point`. Use an opt-in `CT244_PRIMITIVE_TRACE=1` environment variable; off must leave output and control path unchanged except the guard.
- Track execution count, elapsed monotonic nanoseconds (not a generic cost unit), and exact primitive labels, with overflow-safe checked counters. Emit a separate `CT244_PRIMITIVE_TIMING` JSON line on each instrumented runtime teardown; it must not use the `N4_FIXED_CHAIN_` namespace or alter the full-population schema.
- Only include the timed map **evaluation expression** and actual point **doubling expression** in primitive measurements; quantify separately the omitted admit, descent, verification, correction, hashing and timer/dispatch costs. Do not relabel `C13`/ `C169` counts as true time prices before native measurement.

## Fixed negative controls

The source generator must reject (1) any altered original Git blob; (2) absent or duplicated anchor; (3) changed CT125 true norm and `check_final` assertion; (4) missing six directed-map slots or the seventh doubling slot; and (5) any change in counters to `norm_point_doubling`. A syntax/format gate is **not** a native solve or a timing result.

## Native measurement gate (not authorized by this protocol)

- Use exactly the original source/fixture and unfiltered full 695 event stream (and separately retain 701 if applicable). Preserve every failure and output, and compare with the uninstrumented original plus the CT125 optimized derivative using `compare_norm_reuse.py`, **all 695 ordered records**, including all 672 exceptional cases, 48 selected vectors and every correction.
- Bound any proposed original/optimized native attempts by the existing 900 s / 2 GiB rules. No EKS/Spot paid attempt unless explicitly admitted under existing budget and source custody rules. An offline source-only GHA check may run without such admission.
- A/A uninstrumented controls plus reversed-order A/B/B/A samples on the **same isolated host**. Record wall time, setup, high-water memory, primitive counters, directed C13a/C13b, C169, doubling D, and independently priced N2_actual. Separate timer perturbation and cache effects from primitive work; use replicate-level uncertainty, not just one sum of durations.
- Full *cold single-target ECDLP* costs still require transfer/IC setup, online relation generation, LA, target, verification, memory and matched best rho/BSGS/frontier IC on identical public logs.
- A qualified speedup requires independently replayed native raw arithmetic and signed PCC plus conservative baseline/candidate >1; a component count, physical timer improvement or synthetic test alone does not qualify.

## Decision branches

If exact-source generation or rustfmt fails, repair it without claiming compilation. If measured `C169 - 2*C13 - D` (and route-specific form) is nonpositive after measurement uncertainty, record **negative** and switch leads. If positive, proceed to the above complete cost comparator; do not promote to ECDLP advantage without the remaining gates.

**Sources checked:** crypto #3877 (merged); crypto #4215 (48-vector prospective inequality); cryptanalysis #1523 (merged), #1533 (native derivative), crypto #4178 (GPU IC gap), crypto #4715/CT243 (F103 complete cold negative), research queue crypto #3904. Shared research-KB was not accessible through available connectors; this is not a novelty claim.
