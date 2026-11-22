# Proof map: exact two-plus-one-versus-two target lookup

| Result | Lean declaration | Hypotheses and verification | Concrete bridge |
| --- | --- | --- | --- |
| A five-point sum equals the target exactly when the two-point left sum equals the target minus the third point and right pair | `TwoPlusOneJoin.exact_pair_lookup` | Arbitrary `AddCommGroup G`; `leanprover/lean4:v4.34.1`; checked by `lean TwoPlusOneJoin.lean`; `#print axioms` reports no axioms | The native worker computes both group sides and checks every candidate hit with point addition; independent checked Sage rebuilds all ten leaves, signed pairs, target Frobenius transport, subgroup point, and distinct folded columns. |

`lean.stdout` and `lean.stderr` preserve the actual module build. The theorem
uses standard Lean group foundations; it contains no custom axioms, `sorry`,
`admit`, or native-evaluation proof. `lean4checker --fresh` was unavailable on
this host. The finite-field/curve implementation and source-table bridges are
checked by the native input validation and independent Sage replay; they are
not formalized in this module.
