# Proof map

| Result | Declaration or replay | Hypotheses and scope | Status |
| --- | --- | --- | --- |
| Equal finite index completes a relation lattice | `X011RelationLattice.equals_relation_kernel_of_index` | Additive groups `A,B`, finite `B`, a surjective homomorphism `pointMap`, `rowLattice ≤ pointMap.ker`, and `rowLattice.index = Nat.card B` | Lean checked; standard foundations only |
| Saved Hermite arithmetic | `nonzero_entry_count`, `upper_triangular_entries`, `diagonal_product` in `HNFIndex.lean` | 281 saved nonzero entries of an `84 × 84` Hermite basis; diagonal product 1020 | Lean checked; no axioms |
| Exact row-lattice index | `run_sage.py` Smith factors and row-Hermite determinant; `audit.py` SymPy Smith factors and column-Hermite determinant | Frozen `596 × 84` integer matrix | Independent computational replay passed; Lean matrix-to-index bridge open |
| Row containment in the point-map kernel | Sage and independent pure-Python group-law checks | All 596 rows on the exact 84 ordered curve points | Independent computational replay passed; concrete group-law formalization open |
| Surjectivity and group order | Sage point order and curve cardinality; independent pure-Python point count and generator order | `P_0=(2,155)`, order 1020, `#E(F_1009)=1020` | Independent computational replay passed; concrete finite-curve formalization open |

`IndexEquality.lean` is built with Lean `v4.35.0-rc4` and mathlib revision `021c46bdd042f67b538b9f9871d556a93713a9a9` from the existing pinned project in `DEPENDENCIES.json`. `HNFIndex.lean` uses Lean core under the same toolchain. Their build-output files retain `#print axioms`. Neither module contains `sorry`, `admit`, custom research axioms, or a kernel bypass. The computational inputs and their exact identities are pinned in the protocol, post-run digest, and audit rather than assumed by the Lean theorem.
