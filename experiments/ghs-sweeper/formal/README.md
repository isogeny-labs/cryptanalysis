# Partial Lean certificate

Pinned Lean 4.34.1, no external dependencies. `lake build` checks
`CubicGluing.lean`; its five declarations print their foundations.
Only ordinary kernel-reduced `decide` is used, with no native evaluation,
claim axioms, or admitted proof.

| Written result | Declaration | Scope |
|---|---|---|
| Fixed q=3, M=diag(3,4) positive construction | `coefficient_injectivity`, `frobenius_stability`, `basis_isotropy`, `coordinate_transversality`, `determinant_binding` | exact Fin 5 coordinates; pending build receipt |
| General split-semisimple iff classification | none | not formalized |
| Elliptic torsion, polarization, arithmetic Torelli | none | not formalized |

The finite declarations prove a particular basis is independent, is preserved
by the specified Frobenius action, has pairwise-zero basis pairings, and
has trivial coordinate intersections. Missing bridges include general finite
fields and linear algebra, extension from basis pairings to a submodule's
polarization, conjugation, and the two negative cases. They are not replaced
by the fixed certificate. The full written theorem and geometric obligations
remain open for formalization.
