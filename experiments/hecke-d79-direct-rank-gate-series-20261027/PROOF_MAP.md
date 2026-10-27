# Result verification and formalization map

| Result | Lean declaration | Current verification |
| --- | --- | --- |
| Exactly one of the four audited rank pairs is a false reject under threshold 37 and rank goal 39 | `DirectRankGateSeries.one_false_reject` | Kernel checked on the exact four rank pairs; no axioms |
| `(35,39)` meets the false-reject predicate | `DirectRankGateSeries.p103357_gate_counterexample` | Kernel checked; no axioms |
| The other three audited pairs are correct rejects | `DirectRankGateSeries.three_correct_rejections` | Kernel checked; no axioms |
| The four direct and full-source matrix ranks are 32→34, 35→39, 31→34 and 32→35 | None yet | Independent Sage enumeration and finite-field rank checks; Lean row-matrix certificates remain open |
| The p103357 rank-39 system plus one anchor recovers 40 projected class logs | None yet | Independent Sage solve and 40 pointwise scalar replays; Lean curve and subgroup bridge remains open |

The Lean theorem establishes the logical counterexample **conditional on the audited rank table**. The matrix rank and group-log claims are separate obligations. A faithful full formalization needs the four curve instances, their degree-13 source equations, relation rows, finite-field row-echelon certificates and the p103357 subgroup scalar action. These are retained as machine-readable evidence but have not been encoded in Lean. Lean 4 `v4.35.0-rc4` is pinned in `formal/lean-toolchain`; `lake build` passes, and `#print axioms` reports no axioms for the three declarations. `lean4checker --fresh` is unavailable in this environment.
