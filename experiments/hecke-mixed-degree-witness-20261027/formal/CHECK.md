# Formal check

`lake build MixedDegreeWitness` completed successfully with the pinned Lean 4 toolchain and Mathlib revision in `lean-toolchain`, `lakefile.toml`, and `lake-manifest.json`. The saved [build output](build-output.txt) ends with `Build completed successfully (802 jobs).`

`#print axioms exact_identity` reported only `propext`, `Classical.choice`, and `Quot.sound`. The module contains no `sorry`, `admit`, custom research axiom, native evaluation, or kernel bypass. `lean4checker --fresh` was unavailable on this host.

The theorem proves the 32 coordinate equalities for the exact frozen integer rows. Its bridge to the Hecke class points is the independently checked input/row reconstruction in the producer and `verify.py`; Lean does not define the elliptic curve or modular correspondence here.
