# Lean check

The module uses Lean `v4.35.0-rc4` and Mathlib revision
`021c46bdd042f67b538b9f9871d556a93713a9a9`, pinned by
`lean-toolchain`, `lakefile.toml`, and `lake-manifest.json`.

From this directory, `lake env lean HeckeCommutator.lean` exited 0 and
saved `build-output.txt`. `lake build HeckeCommutator` exited 0 and
saved `lake-build.txt`. Both declarations were audited with
`#print axioms`; each lists only `propext`, `Classical.choice`, and
`Quot.sound`. The source contains no `sorry`, `admit`, custom axiom,
or native evaluation. `lean4checker --fresh` was unavailable on this
host.

`PROOF_MAP.json` records the exact hypotheses and the finite bridge
checked by the Sage producer and independent integer validator.
