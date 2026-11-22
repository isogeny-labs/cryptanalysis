# Proof map

The new structural result is the exact common-root test for two finite families of characteristic-two quotient signatures. [FamilyResultant.lean](FamilyResultant.lean) contains `FamilyResultant.familyProduct_zero_iff_common`: for lists `as, bs` of field-element bit words and a multiplication operation satisfying `mul x y = 0 ↔ x = 0 ∨ y = 0`, their product of pairwise XOR differences vanishes exactly when the lists share an element. The theorem quantifies over both lists and the multiplication operation. `pairProduct_zero_iff` is its one-family induction step. The pinned Lean 4.34.1 build succeeded; `#print axioms` reports only `propext` and `Quot.sound`. There are no admitted claims or custom axioms. `lean4checker --fresh` is unavailable on this host.

For `F_a(Z)=∏_(r in a)(Z+r)`, the computed resultant `∏_(s in b)F_a(s)` is the same pairwise product in the commutative characteristic-two field. Its zero set is precisely common-root incidence by the Lean theorem and the field's no-zero-divisors property. The runner also checks that all 72 quartics are monic and vanish at their four enumerated roots; the readback repeats those checks.

| Mathematical or computational bridge | Verification and status |
| --- | --- |
| `GF(2^41)` multiplication has no zero divisors | Conditional hypothesis in the Lean theorem. The concrete modulus `t^41+t^3+1` and implementation are frozen; a Lean quotient-field construction and irreducibility bridge remain open. |
| Five independent Riemann–Roch rows give a two-dimensional quotient | The earlier quotient proof map records the written matrix proof and checked local kernel identities. Its full Lean matrix-rank bridge remains open. |
| Quotient signature equality means the six pair outputs sum to the public target | The earlier independent checked-Sage audit tests all 20,736 eligible group pairs by subtraction and finds exactly state pair `(12,122)`. The full elliptic-curve divisor theorem is not yet formalized in Lean. |
| Family polynomial roots and resultant zero set match the executable code | `run.py` constructs each quartic and evaluates every root; `verify.py` reconstructs the quotient keys independently and recomputes the 1,296 compatibility bits by finite-set intersection. |
| The linear hull cannot reject a family pair in this panel | `verify.py` checks that every four-root family has at least two distinct projective ratios, hence spans the two-dimensional quotient; any two full quotient spans have a dependent choice. |

The proof is complete for the abstract finite-family resultant criterion and partial for the concrete curve-to-field bridge. The bridge status does not change the independently replayed N41 finite panel.
