# Proof map: ten-pair public-point control

| Result | Proof or evidence | Status |
| --- | --- | --- |
| A sum of source pairs transports through an additive endomorphism and cofactor map | `NinePairOrbit.relation_pullback` in `../n131_w18_ninepair_orbit_20261012/OrbitTransport.lean`; its proof is list-length independent | Checked in pinned Lean 4.34.1; the parent's `lean_check.txt` reports only `propext` and `Quot.sound`. The theorem is an abstract transport implication, not the concrete N41 curve claim. |
| Ten selected signed W8 pair points are source-valid, have distinct folded edges, and sum to the frozen raw public preimage | `audit_sage.py`, `audit_result.json` | Independently checked Sage reconstructs every source point and group operation. The exact binary-field curve group and source encoder are not represented in Lean, so the full concrete statement remains open there. |
| The cofactor-four relation has 20 nonzero folded columns and raises the prior two-row rank to three | `audit_sage.py`, `audit_result.json` | Checked Sage verifies the quotient coefficients and group equation; 12 new columns give rank three. A faithful Lean concrete quotient/rank bridge remains open. |

The N41 control uses the repository's checked Sage runtime saved in
`sage_runtime_info.json`. The abstract Lean proof's toolchain, command, and
axiom audit remain frozen in the referenced module. No custom axiom or
unchecked native evaluation is counted as a Lean proof of the concrete
source or curve relation.
