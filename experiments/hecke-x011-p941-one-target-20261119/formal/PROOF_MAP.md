# Proof map

| Result | Lean declaration | Hypotheses | Status |
| --- | --- | --- | --- |
| Pair-coordinate shift recovery | `X011NoncyclicTarget.pair_shift_recovery` in `CoordinateRecovery.lean` | Additive commutative group; integers `k,a,b`; `P=a•G+b•H`; `Q+k•G=P` | Built and axiom audited; `propext` only |
| Row-HNF quotient has 900 cosets and yields 112 fiber coordinates | none here | Frozen p941 HNF and ordered trace-18 fiber | Computed from lattice, independently replayed with Sage; Lean concrete bridge open |
| Public point and four run answers | none here | Exact p941 curve, order-180 subgroup and frozen public point | Independently replayed with Sage; Lean concrete curve bridge open |

The theorem exposes both coordinate premises and does not assume the recovered answer. The recorded program checks the finite premises and the separate audit checks them again in Sage. `lean4checker --fresh` was unavailable on this host.
