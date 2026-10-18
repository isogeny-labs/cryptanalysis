# Frobenius collision proof map

The exact fixed-instance result is the exhaustive binary-linear
calculation in `audit_result.json`, followed by the source-validity
enumeration in `filter_result.json`. `verify_sage.py` independently
reconstructs the finite field, all 524 ranks and affine feasibility
decisions, every enumerated collision equality, and the complete
valid pair set.

| Result | Lean declaration | Hypotheses and scope | Status |
| --- | --- | --- | --- |
| Frobenius is additive in characteristic two | `FoldedCollision.frob_add` | Arbitrary characteristic-two field and nonnegative Frobenius power | Checked |
| Endpoint orbit collision is equivalent to one affine linear equation | `FoldedCollision.collision_linearized` | Arbitrary characteristic-two field, two source parameters, seed and endpoint coefficients | Checked |

The Lean module does not yet define the concrete 131-bit quotient field,
the 28-element source basis, or its 524 rank certificates. It also does
not define curve points and the halftrace x-coordinate map. Those are
the exact missing bridges for a full Lean theorem about the fixed W29
source; the independently replayed finite-field computation is the
current fixed-instance certificate. The written proof in `RESULT.md`
states the source-to-curve and linear-algebra implications explicitly.

`lean FoldedCollision.lean` passed under pinned Lean 4.34.1; see
`lean_check.log`, `lean_exit_code.txt`, and `lean_version.txt`.
`#print axioms` reports only `propext`, `Classical.choice`, and
`Quot.sound` for both theorems. `lean4checker --fresh` was unavailable.
