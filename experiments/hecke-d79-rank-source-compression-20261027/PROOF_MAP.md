# Proof map

| Result | Lean declaration | Scope and status |
| --- | --- | --- |
| All 237 p63317 Hecke candidate source supports are distinct | `RankSourceCompression.all_supports_distinct` | Exact support list generated from hash-pinned `analysis.json`; kernel checked, no axioms |
| Every support has four strictly increasing indices | `RankSourceCompression.all_supports_strict` | Exact same catalog; kernel checked, no axioms |
| Selected quotient minor is 1617 and nonzero modulo 2531 | `RankSourceCompression.quotient_minor`, `quotient_minor_nonzero` | Concrete residual entries `(1620,922)` and `(2304,2320)`; kernel checked, no axioms |
| Baseline rank 37, full/selected rank 39 and anchored log replay | None yet | Exact 40-column matrices over (F_{2531}); independent Sage audit passes; full matrix formalization remains open |
| Selected rows are relations among the p63317 curve points | None yet | (y²+y=x³−x²−10x−20) over (F_{63317}); independent Sage group replay passes; Lean curve bridge remains open |

The readable proof of the catalog minimum combines the checked support facts with the Sage rank certificate. One catalog row uses four sources and can increase rank by at most one; distinct four-source supports require at least five sources for any pair. The selected pair reaches that bound and has nonzero quotient minor. The 40-column baseline rank and quotient construction are still Sage-checked assumptions in the Lean arithmetic certificate. The result is therefore a fully audited finite computation with partial Lean formalization of the matrix and curve bridge.

Lean 4 toolchain `v4.35.0-rc4` is pinned in `formal/lean-toolchain`. `cd formal && lake build` succeeds and `formal/build-output.txt` retains `#print axioms` output for every declaration. `lean4checker --fresh` was unavailable. The module uses `Init` with no `sorry`, `admit`, custom axioms or native evaluation.
