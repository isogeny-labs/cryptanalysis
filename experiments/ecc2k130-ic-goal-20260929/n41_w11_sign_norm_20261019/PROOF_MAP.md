# Proof map

Toolchain: `leanprover/lean4:v4.34.1` in `lean-toolchain`; Lean executable version and commit are retained in `lean_version.txt`. The command used for the checked module was `lean SignNorm.lean` from this directory with that toolchain. `lean.stdout` and `lean.stderr` retain the build and `#print axioms` output. `lean4checker --fresh` was unavailable on this host.

| Mathematical step | Lean declaration | Hypotheses and status |
| --- | --- | --- |
| A nonzero product has only nonzero factors | `SignNorm.factor_nonzero_of_product_nonzero` | Any field, finite list, product nonzero; checked |
| A functional value of one on a sign product excludes each factor | `SignNorm.trace_norm_excludes_each_sign` | Any field; Boolean functional with `L 0 = false`; finite sign list; checked |
| One certificate per root tuple excludes every sign in a box | `SignNorm.trace_norm_excludes_box` | Any field; finite list of sign lists; same functional certifies each product; checked |

All three declarations have only standard Lean axioms `propext`, `Classical.choice`, and `Quot.sound` in `lean.stdout`. There is no `sorry`, `admit`, custom research axiom, or native evaluation in the module.

The finite N41 facts that each archived field product equals the determinant-factor product and that determinant zero matches the group relation are checked by the independent Sage replay, not formalized as Lean theorems. A complete formal bridge would define the characteristic-two curve, its group law, the six-point Riemann-Roch evaluation determinant, and prove the determinant criterion for these distinct-point hypotheses. That formalization remains open; the conditional exclusion theorem preserves the exact field-product implication.
