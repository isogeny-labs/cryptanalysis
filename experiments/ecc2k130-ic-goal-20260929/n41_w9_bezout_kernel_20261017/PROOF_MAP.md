# Proof map

| Result | Lean declaration | Exact hypotheses and status |
| --- | --- | --- |
| Each quartic Bezout row dotted with `(1,w,w²,w³)` equals a combination of the two quartics evaluated at `w` | `KernelWitness.row_tail_identity` | Arbitrary commutative ring, explicit `∀t, t+t=0`, arbitrary quartic coefficients and `w`. Checked. |
| A common field root provides a normalized Bezout kernel witness | `KernelWitness.common_root_kernel` | Same ring and characteristic hypothesis, plus both quartics vanish at `w`. Checked. Normalizing the first coordinate to one preserves every common-root witness. |
| A symmetric four-by-four determinant is the first-column cofactor sum of the four normalized kernel row equations | `KernelWitness.det_as_kernel_rows` | Arbitrary commutative ring, explicit characteristic-two hypothesis, arbitrary symmetric matrix entries and three free kernel coordinates. Checked. |
| A normalized kernel witness forces the Bezout determinant to vanish | `KernelWitness.normalized_kernel_implies_det_zero` | Same matrix and ring assumptions, plus all four displayed row equations. Checked. |
| The quartic Bezout determinant equals the resultant | Open formal bridge | Requires a Lean polynomial/resultant or Sylvester matrix definition and the general Bezout determinant theorem under degree assumptions. The preceding `n41_w9_two_quartic_circuit_20261017` proof map records this same bridge. The [classical identity](https://epubs.siam.org/eprint/3RADN6DUV6MDWSDXSKBP/full) and the frozen Sage resultant check provide the written mathematical and concrete evidence. |
| The frozen N41 source maps each signed pair state to the stated quartic root and target group relation | Open concrete bridge | The prior all-code root audit and the present 33-row Sage kernel audit check the finite instance. A faithful Lean model of the curve, field, and complete source table is unfinished. |

Build: `lean KernelWitness.lean > lean_check.log` from this directory with pinned `leanprover/lean4:v4.34.1` (`5045d0056413266e57c625dcd7c365b10e377c52`). `#print axioms` reports only `propext`, `Classical.choice`, and `Quot.sound`. The current environment has no `lean4checker`; no separate fresh-checker result is reported. No `sorry`, `admit`, `sorryAx`, custom research axiom or native evaluation occurs in the checked module.
