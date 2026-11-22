# Proof map

| Result | Lean declaration | Hypotheses | Status |
| --- | --- | --- | --- |
| Additive shift recovery | `X011Target.shift_recovery` in `ShiftRecovery.lean` | Any additive commutative group; integers `k,l`; `P=l•G`; `Q+k•G=P` | Built and axiom audited; `propext` only |
| HNF quotient has order 1020 and yields all 84 logs | none here | Saved p1009 row HNF and ordered fiber | Computational certificate plus independent Sage replay; Lean bridge remains open |
| Public point and four run answers | none here | Exact p1009 curve and frozen public point | Independently replayed by Sage; Lean curve-model bridge remains open |

The theorem does not assume the desired recovered scalar. Its two premises are precisely the prepared point-log identity and the verified group shift. `lean4checker --fresh` was unavailable; the actual module was built with the pinned Lean/mathlib project in `DEPENDENCIES.json`.
