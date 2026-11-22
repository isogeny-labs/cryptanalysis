# Proof map

| Result | Lean declaration or replay | Exact scope | Status |
| --- | --- | --- | --- |
| Per-source quartic root counts | `X011P1009Degree3.exact_root_counts` | 84 pinned quartics evaluated at all residues modulo 1009 | Lean checked; no axioms |
| 56 one-root and 28 four-root quartics | `X011P1009Degree3.root_count_histogram` | Histogram of the preceding ordered root-count list | Lean checked; no axioms |
| Nonzero mod-17 null vector | `projection_nonzero`, `every_relation_annihilates_projection` | Explicit 84-entry vector against all 596 pinned sparse rows | Lean checked; standard `propext` only for the row-list proposition |
| Rational direct-row null and rank-gain witness | `qq_kernel_nonzero`, `all_direct_rows_annihilate_qq_kernel`, `degree3_row_breaks_qq_kernel` | Explicit vector annihilates all 568 direct rows; one degree-three row has dot product 5 | Lean checked; see build output |
| Quartics, reconstructed neighbors, and point identities | `audit_sage.py` | Corrected X011 ledger and archived degree-three Hecke source | Independent Sage replay passed; formal implementation bridge open |
| Exact matrix ranks | `audit_sage.py` | 84 columns, `QQ` and `F_17`, each row family and combined | Independent Sage replay passed; formal rank derivation open |

`Degree3RootCounts.lean` and `ProjectionKernel.lean` are generated from the digest-bound result and audit artifacts. Build each with `lean <module>.lean` in this directory. `lean-toolchain` pins `leanprover/lean4:v4.34.1`; no third-party Lean package is loaded. The two build-output files contain the `#print axioms` audit. The written group-homomorphism argument is that `P ↦ 60P` maps into the order-17 subgroup and every verified integer group relation maps to zero. Since the recorded vector is nonzero, it is a right-null vector over `F_17`; rank 83 is the maximal value compatible with it. The certificate's exact Sage-to-Lean row binding is in the generator scripts and audited digests.
