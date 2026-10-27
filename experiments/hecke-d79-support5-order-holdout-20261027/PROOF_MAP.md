# Proof map

The exact finite statements concern integer matrices with 40 columns assembled from the frozen relation rows. `GateDirectZero` checks an invertible 40-by-40 minor modulo 3 among the 419 support-four and 154 direct support-five rows. `GateAscendingBase` and `GatePriorityBase` check nonzero integer right-kernel vectors at the preceding source prefixes and invertible minors modulo 3 at the first-hit prefixes.

| Rank statement | Lean module | Certificate | Formal status |
| --- | --- | --- | --- |
| Direct-support-five baseline rank 40 at zero Hecke sources | `GateDirectZero` | Inverse of a 40-by-40 minor modulo 3 | Finite arithmetic checked; structural and geometric bridge open |
| Ascending support-four first hit at 26 | `GateAscendingBase` | Nonzero integer kernel at 25; inverse modulo 3 at 26 | Finite arithmetic checked; structural and geometric bridge open |
| Projection round-robin support-four first hit at 29 | `GatePriorityBase` | Nonzero integer kernel at 28; inverse modulo 3 at 29 | Finite arithmetic checked; structural and geometric bridge open |

The mathematical proof uses two standard rank facts. An integer vector that is nonzero and orthogonal to every preceding row gives a nontrivial rational right kernel, so the preceding matrix has rank at most 39. A 40-by-40 minor with an inverse modulo 3 has determinant nonzero modulo 3, hence nonzero over the integers and rationals, so the first-hit matrix has rank 40. Prefix matrices only add rows, establishing first-hit minimality. The independent auditor verifies that the displayed rows belong to the correct frozen prefix matrices and recomputes every intermediate rank.

The Lean modules check all displayed integer dot products, kernel nonzero status, and inverse identities with kernel-checked `by decide` proofs. Full formalization is **partial**: Lean does not yet define the elliptic-curve trace relation constructor, prove selected-row membership in the geometric matrices, or derive the rank theorems from the arithmetic certificates. Those are the open proof obligations. No `sorry`, `admit`, `sorryAx`, custom research axiom, or native-evaluation bypass is used.

The toolchain is pinned to `leanprover/lean4:v4.35.0-rc4`; there are no external Lean dependencies. Run `cd formal && lake build`. The retained build output includes `#print axioms` for each reported theorem and uses only standard Lean foundations (`propext`, `Classical.choice`, `Quot.sound` where needed). `lean4checker --fresh` was unavailable on this host.
