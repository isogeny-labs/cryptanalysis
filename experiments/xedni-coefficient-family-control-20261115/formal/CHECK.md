# Formal verification receipt

From this directory, `lake build CoefficientFamily` completed successfully
on the pinned `lean-toolchain` and `lake-manifest.json` revisions. The exact
output is in `build-output.txt`. All six reported theorems have `#print axioms`
audits showing only standard Lean foundations: `propext`,
`Classical.choice`, and `Quot.sound`. There is no `sorry`, `admit`, custom
axiom, or native-evaluation proof step. `lean4checker` was unavailable on
this host; the Lean kernel checked the declarations during the build.

The `admissible_hit_count` theorem is the finite-cardinality bridge for one
coefficient direction. The finite-family union arithmetic is recorded in
`PROOF_MAP.md` and checked by the exhaustive audit.
