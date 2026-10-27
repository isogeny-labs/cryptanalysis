# Formal rank-separator check

The project pins `leanprover/lean4:v4.35.0-rc4` with no external dependencies. `python3 generate.py` checked that [RankWitness.lean](RankWitness.lean) matches the hashed matrix inputs and saved degree-13 result. `lake build RankWitness` completed successfully; see [build-output.txt](build-output.txt).

`#print axioms baseline_annihilated` and `#print axioms new_row_separated` both reported no axioms. The proofs use kernel-checked `decide`, not native evaluation. The first theorem checks that one explicit 20-coordinate F_5 vector annihilates all 20 preceding rows. The second checks its dot product with the new source-3 row is 3 modulo 5.

Formalization is partial for the full result. The Lean module does not define the elliptic curve, extension-field Hecke correspondence, or rational matrix rank. Those bridges are checked by the Sage producer and the separate F_83 group-law and rational/F_5 rank validator. The F_5 separator establishes that source 3 is outside the preceding F_5 row span once the usual linearity of the dot product is applied.
