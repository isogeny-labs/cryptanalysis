# Formal verification receipt

From this directory, `lake build CoefficientFamily` completed successfully
on the pinned `lean-toolchain` and `lake-manifest.json` revisions. The exact
output is in `build-output.txt`. Both declarations have `#print axioms`
audits showing only standard Lean foundations: `propext`,
`Classical.choice`, and `Quot.sound`. There is no `sorry`, `admit`, custom
axiom, or native-evaluation proof step. `lean4checker` was unavailable on
this host; the Lean kernel checked the declarations during the build.

The finite-cardinality line count in `RESULT.md` has a written proof and
independent exhaustive audit but is not yet a Lean theorem; see
`PROOF_MAP.md` for the exact remaining bridge.
