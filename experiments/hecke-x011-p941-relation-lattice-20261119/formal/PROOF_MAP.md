# Proof map

| Result | Lean declaration or replay | Exact scope | Status |
| --- | --- | --- | --- |
| Equal finite indices complete a relation lattice | `X011RelationLattice.equals_relation_kernel_of_index` in the stacked p1009 `IndexEquality.lean` | An additive-group point map onto a finite group, row lattice inside its kernel, and equal index | Lean checked under pinned mathlib; standard foundations only |
| Saved p941 Hermite arithmetic | `nonzero_entry_count`, `upper_triangular_entries`, `diagonal_product` in local `HNFIndex.lean` | 461 saved nonzero entries of a `112 × 112` Hermite basis; product 900 | Lean checked, no axioms |
| Exact p941 row-lattice index | `run_sage.py` Smith and row-Hermite; `audit.py` SymPy/FLINT Smith and FLINT Hermite | Frozen `1,585 × 112` integer matrix | Independent replay passed; concrete matrix-to-index Lean bridge open |
| Row containment in point-map kernel | Checked Sage and independent pure-Python group law | All 1,585 saved rows on the exact ordered p941 points | Independent replay passed; concrete group-law formalization open |
| Surjectivity and group order | Sage and independent pure-Python count and pair span | Curve order 900; `P_3=(32,685)`, `P_4=(43,695)` span 900 points | Independent replay passed; concrete finite-curve formalization open |

`generate_hnf_formal.py` binds the local Lean arithmetic certificate to the frozen result and saved basis digests. The core toolchain is pinned in `lean-toolchain`; the reused generic theorem's mathlib revision and build command are recorded in the stacked p1009 proof map. `build-output.txt` retains `#print axioms`. The censored SymPy Hermite attempt is preserved separately from the passing FLINT-backed audit.
