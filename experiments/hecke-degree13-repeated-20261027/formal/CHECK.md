# Formal repeated-root check

The project pins `leanprover/lean4:v4.35.0-rc4` and has no external dependencies. `lake build RepeatedRoot` completed successfully; see [build-output.txt](build-output.txt). `#print axioms rational_y_roots` and `#print axioms unique_unordered_pair` both reported no axioms. The proofs use kernel-checked `decide` over the 83 field residues and unordered residue pairs.

The module proves that the only rational y-coordinates above x=4 on `11a1/F_83` are 38 and 44, and that their unordered pair is the unique one with the saved y-sum 82. It does not define the extension-field Hecke correspondence, solve the fourteen moment equations, or formalize the F_83 group law. Those concrete bridges are checked by the bounded Sage producer and independent pure-Python group replay.
