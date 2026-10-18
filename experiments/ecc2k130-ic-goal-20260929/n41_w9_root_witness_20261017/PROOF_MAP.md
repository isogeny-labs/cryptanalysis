# Proof map for the structured-root circuit

The circuit sets its normalized Bezout vector to `(1,w,w²,w³)` for one free
`w` in `GF(2^41)`. This specializes the already checked structural result;
there is no new algebraic theorem beyond that specialization.

| Result used | Checked declaration and exact hypotheses | Status |
| --- | --- | --- |
| A common root of arbitrary quartics gives all four Bezout row equations on `(1,w,w²,w³)` | [`KernelWitness.common_root_kernel`](../n41_w9_bezout_kernel_20261017/KernelWitness.lean), arbitrary commutative ring with `∀t, t+t=0`, both quartics zero at `w` | Checked by pinned Lean 4.34.1; four row identities are also checked by `row_tail_identity`. |
| Any normalized row solution makes the symmetric Bezout determinant zero | [`KernelWitness.normalized_kernel_implies_det_zero`](../n41_w9_bezout_kernel_20261017/KernelWitness.lean), same ring and characteristic hypothesis, all four row equations | Checked by pinned Lean 4.34.1. Substitute `u=w`, `v=w²`, `s=w³`; no additional algebraic assumption is needed. |
| A zero determinant gives a common field root for this final pair quartic | The [prior proof map](../n41_w9_bezout_kernel_20261017/PROOF_MAP.md) records the open Lean Bezout determinant/resultant bridge; [`SharedQuartic.gate_zero_iff_common_root`](../n41_w9_two_quartic_resultant_20261017/SharedQuartic.lean) covers the split-root criterion under its stated degree and factorization hypotheses | Classical determinant/resultant identity plus finite Sage split-root and 33-row checks; concrete Lean bridge remains open. |
| The N41 source and Boolean circuit implement the stated quartics | Frozen source hashes, prior all-code root audit, this circuit's 33 complete-assignment decisions and exact XCNF audit | Computationally checked; full curve/source-table Lean bridge remains open. |

The reused [Lean output](../n41_w9_bezout_kernel_20261017/lean_check.log)
reports only `propext`, `Classical.choice`, and `Quot.sound` for the four
declarations. The [prior proof map](../n41_w9_bezout_kernel_20261017/PROOF_MAP.md)
records the toolchain revision, build command and checker availability.
