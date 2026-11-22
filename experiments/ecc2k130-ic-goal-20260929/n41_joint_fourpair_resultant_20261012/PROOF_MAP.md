# Proof map

| Result | Lean declaration | Hypotheses and status |
| --- | --- | --- |
| A finite product vanishes iff one listed factor vanishes | `JointNorm.product_zero_iff` | Arbitrary type `K` with zero, one and multiplication; explicit `1≠0` and no-zero-divisors equivalence. Checked in Lean 4.34.1. |
| Two nested finite products vanish iff one left/right root pair satisfies the upper condition | `JointNorm.joint_zero_iff` | Same explicit algebraic hypotheses; arbitrary finite root lists and upper function. Checked in Lean 4.34.1. |
| Polynomial resultant equals leading-coefficient powers times the product over field roots, including multiplicity | Open bridge | Requires polynomial/resultant definitions over the concrete `GF(2^41)` and split-degree hypotheses. Sage verifies this identity per panel family; the full formal theorem is open. |
| The specialized 266-term polynomial equals the elimination of the two reciprocal pair equations and the four-atom Semaev equation | Open bridge to archived universal polynomial | The source resultant and its separate exact checks are in the linked prior experiment; not formalized in this module. |
| Reciprocal x roots correspond to the signed diagonal source points on the nonexceptional chart | Open bridge | The group-law audit supplies all 8,448 concrete checks, while a general Lean curve-law proof remains open. |

Build: `lean JointNorm.lean` from this directory, with the pinned `lean-toolchain`. The output is in `lean_check.log`, the compiler version in `lean_version.txt`, and `#print axioms` is part of the source. The available environment did not provide `lean4checker`; no fresh-checker result is reported. The checked structural lemmas do not stand in for the three open bridges above.
