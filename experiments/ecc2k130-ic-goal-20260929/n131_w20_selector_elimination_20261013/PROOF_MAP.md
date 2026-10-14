# Proof map

| Statement | Evidence | Scope |
| --- | --- | --- |
| A left inverse gives exact product-image membership by `encode(decode(p)) = p` | `SelectorProjection.projector_eq_iff_range` in `SelectorProjection.lean` | Lean 4.34.1, no axioms reported; abstract functions with `decode(encode(s))=s` |
| A product satisfying that projector has a unique source selector | `SelectorProjection.unique_selector_of_projector` | Lean 4.34.1, no axioms reported, same hypothesis |
| The concrete 19-bit W20 product map is injective and the decoder/projector match all source codes | `basis_result.json` from exhaustive 524,288-code check | Finite arithmetic check; concrete field and matrix are not imported into Lean |
| The eliminated circuit admits the frozen constructed relation | `control_result.json`, `control.xcnf`, `control_run_result.json` | Complete assignment satisfies all XCNF clauses and native XOR rows; no ordinary relation search is inferred |

The missing formal bridge is a Lean representation of the pinned `GF(2^131)` product basis and its 19-by-19 decoder, followed by an exact correspondence between the Boolean circuit rows and the abstract projector. The readable argument is linear algebra: the pivot minor is invertible, hence its decoder is a left inverse; any product fixed by `encode ∘ decode` lies in the product image and has that decoded selector uniquely.
