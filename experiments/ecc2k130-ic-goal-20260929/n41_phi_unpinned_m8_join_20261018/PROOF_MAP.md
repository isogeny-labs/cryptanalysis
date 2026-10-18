# Proof map

The mathematical group identities used by the exact join are formalized in
[EightJoin.lean](EightJoin.lean) with Lean 4.34.1 pinned by [lean-toolchain](lean-toolchain).
Run `lean EightJoin.lean` from this directory. The retained build and
`#print axioms` output are in [lean_check.log](lean_check.log).

| Result | Lean declaration | Hypotheses and status |
| --- | --- | --- |
| The left and right four-leaf sums equal the eight-leaf sum | `EightJoin.four_plus_four_is_eight` | Any additive commutative group and any eight elements; checked, standard `propext` only |
| Exact target lookup equivalence | `EightJoin.target_lookup` | Any additive commutative group and any left sum, right sum, target; checked, no axioms |

The Lean declarations prove the structural equality and lookup equivalence.
The concrete N41 field isomorphism, phi leaf set, curve operations, hit, and
projected relation are checked computationally by the pinned Sage exporter
and independent Sage audits. A full Lean formalization of the ONB field
representation and binary-curve group law is open; no theorem in this module
assumes or states those computational checks. `lean4checker --fresh` was not
available in this environment.
