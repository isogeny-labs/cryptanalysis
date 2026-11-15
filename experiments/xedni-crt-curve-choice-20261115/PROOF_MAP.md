# Formalization map

| Result | Lean declaration | Exact hypotheses and status |
| --- | --- | --- |
| An integer relation among rational lifts maps to the same relation after reduction | `XedniObstruction.relation_reduces` in `experiments/xedni-lattice-obstruction-20261028/formal/XedniObstruction.lean` | General additive homomorphism and integer coefficient vector. Existing declaration; this experiment does not change it. |
| The displayed rational curve and points satisfy `Q₁+2Q₂=O`, with compatible reductions and auxiliary group orders | — | Exact witness checked by the repository Sage launcher and independent rational/finite-field arithmetic in `audit.py`. A faithful Lean elliptic-curve instantiation and kernel-checked witness are open. |
| The fixed public input `G=(2,2)`, `Q=(26,8)` and the two relation rows recover scalar 17 | — | Checked by exhaustive Sage target replay and independent exact finite-field arithmetic in `audit.py`. The algebraic division step and faithful finite-curve witness remain open in Lean. |
| Any full-field asymptotic bound for the original xedni curve-selection law | — | Requires a formalized height/discriminant premise and the actual coefficient/point selection distribution. Open. |

The current shared checkout's `xedni-lattice-obstruction-20261028/verify.py`
returns `AssertionError: XedniObstruction.lean` on its source hash. This
experiment therefore does not report a fresh Lean build for that imported
module. A formalization follow-up must use an isolated, pinned source
snapshot, build its actual theorem module, and audit `#print axioms` before
claiming the elliptic-curve witness in Lean.
