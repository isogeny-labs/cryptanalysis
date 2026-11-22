# Proof map: four-axis quotient and N131 first-pair bridge

For N41, the coefficient ring has two exact product-code values on each of
four axes:

`R = GF(2^41)[p,q,r,w]/∏axis((axis+axis₀)(axis+axis₁))`.

It has dimension 16 over the field. The archived monic degree-eight
first-two-pair polynomial `H(p,q,U)` gives a 128-dimensional root quotient
`K=R[U]/H`. The fourth-code variable `w` indexes two exact pair product
values. For each of the four raw pair-state offsets, an affine polynomial
in `w` interpolates the target residual chart after subtracting that state
and the final three fixed pair states. Substituting each chart into the
previous third-pair norm gives `Q₀,...,Q₃`. Their product vanishes at a
specialized root exactly when at least one fourth-state branch has a
third-pair incidence. The zero-bit fingerprint of that product is an exact
zero test at each specialized root. A zero residue in `K` excludes every
branch in every family of the complete 2×2×2×2 code box.

| Result | Formal or finite check | Status and exact assumptions |
| --- | --- | --- |
| Zero quotient fingerprint excludes all four fourth-state branches at every specialized root in a complete four-axis box. | `FourCodeBox.zero_quotient_excludes_four_axis_box` in `BoxSound.lean` | Lean 4.34.1 checked. Assumes zero-preserving evaluation and the exact branch-indicator evaluation; `#print axioms` reports standard `propext` and `Quot.sound`. |
| Code-ring arithmetic, degree-eight H specialization, four residual interpolants, norm product, and four bit checkpoints agree on exact N41 roots. | `audit_sage.py` | Checked Sage evaluated 32 families, 256 roots, 288 H coefficients, and all four checkpoint residues. It independently recomputed all 160 target residual charts from curve points. |
| The full four-axis N41 point join enumerates all admissible quads and retains the ordinary witness. | `full_traversal_sage.py` and `verify.py` | Sage enumerated 1,386,816 admissible code quads via 2,715,648 first-three-state sums. The sole reported match was replayed exactly on the raw public point. The verifier checks frozen sources, totals, resource receipts, and the witness; it does not independently repeat the complete enumeration. |
| A degree-eight first-two-pair resultant exists in the N131 W23 standard `1/x` chart and vanishes on the archived constructed six-pair control. | `n131_h_bridge_sage_v2.py` and `audit_n131_h.py` | Sage derived 138 terms by two resultants; a separate binary-field implementation rechecked the two pair laws, S3, and all terms. This is a first-two-pair structural bridge only. |

The Lean module's full proof and `#print axioms` output are in
`BoxSound.lean` and `lean_check.log`. It was built with
`ELAN_TOOLCHAIN=leanprover/lean4:v4.34.1 lean BoxSound.lean`, using bundled
`Std` at Lean commit `5045d0056413266e57c625dcd7c365b10e377c52`.
`lean4checker --fresh` was unavailable. A full Lean finite-field polynomial
quotient model, root-specialization map, and N131 resultant derivation
remain open. The independent Sage and binary-field audits check the finite
instances that supply those bridges here.
