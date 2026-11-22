# Proof map

The 40-column result uses the exact point order and relation rows pinned by
`protocol.json`, `pre-run.json`, `archived-inputs.json`, and
`direct-rows.jsonl.gz`.

| Result | Lean declaration | Exact check | Status |
| --- | --- | --- | --- |
| Every 144 direct rows annihilates the order-61 coordinate vector | `CompleteRankP317.all_rows_annihilate_projection` | Finite row-dot products modulo 61 | checked |
| The coordinate vector is nonzero | `CompleteRankP317.projection_nonzero` | 40-coordinate list inequality | checked |
| Direct rows have a 39×39 invertible minor mod 61 | `mod61_minor_matches`, `mod61_inverse_certificate` | Selected rows, pivot columns, inverse product | checked |
| Direct rows have a 40×40 invertible minor mod 2 | `mod2_minor_matches`, `mod2_inverse_certificate` | Selected rows, pivot columns, inverse product | checked |

The written rank proof is: row annihilation by a nonzero vector bounds
F61 rank by 39; the 39×39 inverse raises it to 39. The 40×40 inverse
modulo 2 makes the corresponding integer determinant odd, so Q rank is 40.
The generator [replays](generate.py) the selected rows, pivot columns and
inverse identities from the frozen ledger before emitting Lean source.
`lake build CompleteRankP317` compiled the module, and `#print axioms`
reported no axioms for the row-annihilation and nonzero-vector lemmas, and
only standard `propext` for the finite inverse checks.

The abstract matrix-rank implications, the curve/group-law validity of
each producer row, and the map from archived receipt coordinates to the
formal lists remain written mathematical and independently Sage-checked
bridges. The Lean formalization is partial for the full curve-rank theorem;
the finite arithmetic certificates are fully checked. No `sorry`, `admit`,
custom research axiom, or native-evaluation proof appears in the module.
`lean4checker --fresh` was unavailable on this host.
