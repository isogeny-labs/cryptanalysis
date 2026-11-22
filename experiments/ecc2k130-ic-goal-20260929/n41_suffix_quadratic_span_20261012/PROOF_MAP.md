# Proof map: degree-two exact-suffix feature rank

| Result | Formalization / receipt | Status |
| --- | --- | --- |
| A linear test on feature vectors that vanishes on a spanning sample vanishes on every feature vector | `ResidualSpan.no_additional_linear_test` in the parent `n41_output_first_inverse_20261012/ResidualSpan.lean` | Lean 4.34.1 checked the XOR-span implication; `#print axioms` lists only `propext`. The present 821-bit feature vectors instantiate its abstract bit-vector law. |
| 3,544 four-column-compatible exact suffix sums contain 821 independent degree-two feature rows | `valid_result.json`, `valid_audit.json` | Frozen Python pivot elimination and independent checked-Sage matrix rank agree. The source-to-feature encoding and finite rank certificate are not yet formalized in Lean; the full concrete theorem remains open there. |
| Polynomial consequence: no nonzero degree-at-most-two equality on the trace kernel vanishes on all exact suffix sums | Readable proof in `RESULT.md`; previous Lean XOR-span lemma supplies the structural implication | Conditional Lean theorem checked; concrete source/rank bridge partial. The 41-to-40 coordinate substitution is explained mathematically but not yet formalized. |

Lean toolchain and dependency are pinned by the parent experiment's
`lean-toolchain` and immutable commit `ffd53b98b`; the parent `lean_check.txt`
records the actual build and `#print axioms`. `lean4checker --fresh` was
unavailable on this host. This proof map distinguishes the checked abstract
implication from the independently audited concrete rank computation.
