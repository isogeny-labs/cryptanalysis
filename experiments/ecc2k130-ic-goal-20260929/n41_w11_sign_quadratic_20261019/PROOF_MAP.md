# Proof map for the sign-quadratic five-pair screen

| Result | Lean declaration or exact evidence | Hypotheses and status |
| --- | --- | --- |
| A two-bit finite difference extracts a quadratic mixed coefficient | `SignQuadratic.pair_coefficient` in [SignQuadratic.lean](SignQuadratic.lean) | Any commutative ring with `1+1=0`. Checked Lean 4.34.1; `#print axioms` reports `propext`, `Classical.choice`, and `Quot.sound`. |
| A binary-linear functional separating the constant from all 15 nonconstant coefficients excludes every five-sign assignment | `SignQuadratic.certificate_nonzero` | Any additive commutative group `G`; `L:G→Bool` preserves addition as XOR and sends zero to false; `L(c₀)=true`, and `L` is false on each linear and pair coefficient. Checked Lean 4.34.1; `#print axioms` reports only `propext`. |
| The six-point determinant is quadratic in five pair-output sign bits | Written determinant proof in [RESULT.md](RESULT.md); all 10,272 tested assignments satisfy the 16-coefficient reconstruction in [result.json](result.json) and [code_box_result.json](code_box_result.json) | Binary curve inverse law `−(x,y)=(x,y+x)`; output x fixed within a sign family; determinant multilinear in rows; only the `y` and `xy` columns vary. The full six-by-six determinant and source-coordinate bridge has not been formalized in Lean. |
| Determinant zero exactly matches the five-pair target relation on the frozen panels | Direct determinant and group checks in the two worker results; independently rebuilt source/group replay in [audit_result.json](audit_result.json) | Six distinct finite x-coordinates, including `−Q`; basis `1,x,y,x²,xy,x³` of `L(6O)`; exact N41 curve and field. The Riemann–Roch divisor implication remains a written proof plus finite checked-Sage audit, rather than a single Lean declaration. |
| A full 41-bit variation span obstructs one shared coordinate-linear certificate | Earlier checked `AffineCertificate.full_span_obstruction` in [AffineCertificate.lean](../n41_rr_joint_box_rank_20261017/AffineCertificate.lean); [pool result](pool_result.json) and [independent rank replay](pool_audit_result.json) | Binary-additive functional on the concrete field-coordinate group. All nine boxes reached rank 41 after the third root tuple; every `C(32,4)` subset was independently classified. The concrete 41-bit matrix-to-field identification is checked computationally. |
| The selected rows use valid source points and distinct signed-Frobenius columns | [source/group audit](audit_result.json), [column audit](columns_result.json) | Seed 112, exact W11 code basis, rotations `(0,0,12,12,24)`, 400 selected signed states from 156 codes, and the frozen public point. Both checked-Sage jobs completed under one-worker caps. |

The pinned toolchain is `leanprover/lean4:v4.34.1`.
`lean SignQuadratic.lean` built the actual module, and
[lean.stdout](lean.stdout) contains `#print axioms` for both
theorems. The first failed proof attempt is preserved in
[lean_attempt1.stdout](lean_attempt1.stdout); the corrected build has
empty stderr and no `sorry`, `admit`, `sorryAx`, custom research
axiom, or native proof shortcut. `lean4checker --fresh` was
unavailable on this host. The central missing Lean bridge is a
formal six-point `L(6O)` determinant theorem instantiated with the
exact source pair outputs, signs, and N41 quotient field.
