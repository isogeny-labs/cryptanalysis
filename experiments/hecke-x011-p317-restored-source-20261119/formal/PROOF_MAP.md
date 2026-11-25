# Proof map for the restored source Hecke row

The mathematical row is obtained from the degree-2 Hecke identity
`Q1+Q2+Q3=a2 P39` with `a2=-2`, after the independently replayed
neighbors match class columns 15, 17 and 36. Group-law verification gives
`P15+P17+P36+2P39=0` on `E11a1(F317)`.

| Result | Lean declaration | Check | Status |
| --- | --- | --- | --- |
| All 104 archived-plus-new rows annihilate the nonzero order-61 projection vector | `RestoredHeckeRankP317.all_rows_annihilate_projection`, `projection_nonzero` | Complete finite row list | checked |
| A 39×39 submatrix is invertible modulo 61 | `mod61_minor_matches`, `mod61_inverse_certificate` | Selected rows, columns and inverse | checked |
| A 40×40 submatrix is invertible modulo 3 | `mod3_minor_matches`, `mod3_inverse_certificate` | Selected rows, columns and inverse | checked |

The nonzero right-kernel vector bounds F61 rank by 39; the inverse minor
gives the matching lower bound. The 40×40 minor has determinant nonzero
modulo 3, so its integer determinant is nonzero and the Q rank is 40.
`generate.py` binds the archived input, new result and audit receipts before
emitting the Lean lists. `lake build RestoredHeckeRankP317` succeeds;
`#print axioms` reports no axioms for annihilation/nonzero and only
standard `propext` for inverse identities. There is no `sorry`, `admit`,
custom research axiom or native-evaluation proof.

The curve, q-expansion Hecke functions, fresh neighbor reconstruction, and
the bridge from verified group rows to the formal integer lists are
independently Sage-checked and written here, but are not themselves
formalized in this Lean module. The formalization is partial for that
full structural statement. `lean4checker --fresh` was unavailable.
