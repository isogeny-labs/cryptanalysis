# Corrected suffix support proof map

The exact two-suffix residual identity is checked in
[SuffixSupport.lean](SuffixSupport.lean). The pinned toolchain is Lean 4.34.1
(`leanprover/lean4:v4.34.1`, commit
`5045d0056413266e57c625dcd7c365b10e377c52`). Only the bundled `Std`
and Lean `Init.Grind.Ring.Basic` are imported.

| Result | Lean declaration | Hypotheses | Status |
| --- | --- | --- | --- |
| A prefix sum plus two fixed signed suffix points equals the endpoint exactly when the prefix equals the endpoint minus their sum. | `SuffixSupport.residual_iff` | Any additive commutative group; exact group points and endpoint. | Built, `#print axioms` reports none. |

`lean SuffixSupport.lean` from this directory produced
[lean_check.log](lean_check.log). `lean4checker --fresh` was unavailable.
The theorem is about exact group points. The bridge to the archived N41
curve, 3,600 signed suffix choices, 3,577 finite reciprocal-phi masks, and
`partial8` XCNF variables 402–442 is checked separately in
[audit_sage.py](audit_sage.py). No claim that the concrete XCNF bridge is
formalized in Lean is made.
