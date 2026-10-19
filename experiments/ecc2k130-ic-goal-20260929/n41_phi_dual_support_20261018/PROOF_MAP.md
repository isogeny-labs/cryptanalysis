# Dual-end pair support proof map

The generic support-enumeration statements are checked in
[PairSupport.lean](PairSupport.lean), under the pinned Lean 4.34.1 toolchain
(commit `5045d0056413266e57c625dcd7c365b10e377c52`). It imports only
the bundled `Std` and Lean `Init.Grind.Ring.Basic` modules.

| Result | Lean declaration | Hypotheses | Status |
| --- | --- | --- | --- |
| Every sum from the two listed domains occurs in the enumerated pair list. | `PairSupport.complete` | Arbitrary type with addition; memberships of both input points. | Built, no axioms. |
| Every enumerated sum has an input-pair witness. | `PairSupport.sound` | Same type and pair-list construction. | Built, no axioms. |

`lean PairSupport.lean` produced [lean_check.log](lean_check.log), which
contains the `#print axioms` output for both results. `lean4checker --fresh`
was unavailable. The concrete bridge to the N41 group, 3,600 signed input
pairs, six nonfinite outputs, 1,788 finite reciprocal-phi masks, and XCNF
variable positions is separately checked in [audit_sage.py](audit_sage.py).
The target-conditioned backward support uses the [prior proof and audit](/Volumes/SSD990/cryptanalysis/experiments/ecc2k130-ic-goal-20260929/n41_phi_suffix2_corrected_20261018/PROOF_MAP.md).
