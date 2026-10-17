# Proof map

| Result | Lean status | Concrete evidence and open bridge |
| --- | --- | --- |
| A constant in the XOR span of two charts' nonconstant coefficients cannot be selected by one trace annihilating both charts | `CertificateCoverage.pair_span_obstructs_shared_trace`, with arbitrary vector type, XOR operation and Boolean-linear trace, builds under pinned Lean 4.34.1. `#print axioms` reports only standard `propext`. | `result.json` gives all 35 N41 chart coefficients and 595 pair ranks. A faithful Lean theorem for those 595 concrete rank certificates would require a checked binary-field representation and generated elimination witnesses; that finite bridge remains open. |
| All 595 distinct lower-root chart pairs have rank 41 | Structural implication above; concrete finite result is computationally checked. | `audit_sage.py` independently rebuilds every determinant and computes GF(2) matrix ranks. `audit_result.json` records exact agreement. |
| Both roots of every one of the 35 codes have rank 41 | Same structural implication; concrete finite result is computationally checked. | `audit_fullroot_sage.py` independently rebuilds the second root's determinant coefficients and its rank with the previously audited lower root. `audit_fullroot_result.json` records exact agreement. |
| Determinant zero represents the six-point group-sum condition in the distinct-x chart | Earlier `SignDegree.lean` proves a support bound only. | Every selected chart has seven distinct x coordinates and satisfies the declared curve equation in the Sage audits. The full Riemann–Roch determinant/group-law equivalence is a separate Lean proof obligation. |

`lean-toolchain` pins `leanprover/lean4:v4.34.1`; `CertificateCoverage.lean` imports `Std` and has no `sorry`, custom axioms or native-evaluation proof. The actual build and `#print axioms` output are in `lean.stdout.txt`, and `lean.stderr.txt` is empty. `lean4checker --fresh` was unavailable.
