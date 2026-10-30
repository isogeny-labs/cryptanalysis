# Proof map

The four first-hit claims concern the rank of the exact 40-column integer relation matrices assembled from the pinned support-four rows, optional direct support-five rows, and Hecke support-five rows whose five source indices lie in each prefix.

| Result | Lean module | Exact certificate | Status |
| --- | --- | --- | --- |
| Ascending, support-four: first hit 28 | `GateAscendingBase` | Nonzero integer kernel at 27; inverse of selected 40-by-40 minor modulo 11 at 28 | Arithmetic certificates checked; structural bridge open |
| Ascending, plus direct: first hit 16 | `GateAscendingDirect` | Nonzero integer kernel at 15; inverse modulo 11 at 16 | Arithmetic certificates checked; structural bridge open |
| Priority, support-four: first hit 24 | `GatePriorityBase` | Nonzero integer kernel at 23; inverse modulo 11 at 24 | Arithmetic certificates checked; structural bridge open |
| Priority, plus direct: first hit 20 | `GatePriorityDirect` | Nonzero integer kernel at 19; inverse modulo 11 at 20 | Arithmetic certificates checked; structural bridge open |

The readable proof is linear algebra. A nonzero vector annihilated by all preceding rows gives a nontrivial right kernel, hence rational rank at most 39. At the next prefix, the selected 40 rows form a square minor. Its displayed modular inverse proves that its determinant is nonzero modulo 11, hence nonzero over the integers and rationals, giving rank at least 40. There are exactly 40 columns, so rank equals 40. Rank cannot decrease as prefix rows are added. The auditor checks that the selected rows come from the specified prefix and recomputes every intermediate rank.

Lean checks the integer dot products for all preceding rows in chunks, the nonzero kernel vector, and each modular inverse identity. The central arithmetic certificates are therefore kernel checked. Full formalization remains **partial**: the Lean modules do not yet define the elliptic-curve trace construction, prove that each selected row belongs to the geometric prefix matrix, or formalize the structural rank implications above for those exact lists. Those are the precise remaining proof obligations; the Python auditor and the written proof provide the present bridge.

The Lean toolchain is pinned to `leanprover/lean4:v4.35.0-rc4` in `formal/lean-toolchain`, with no external Lean dependencies. Reproduce with `cd formal && lake build`. `formal/build-output.txt` records the successful build and `#print axioms` audit for every reported theorem. The reported axioms are standard Lean foundations (`propext`, `Classical.choice`, `Quot.sound` where used). `lean4checker --fresh` was unavailable on this host.
