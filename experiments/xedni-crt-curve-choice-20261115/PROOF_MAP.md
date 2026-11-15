# Formalization map

| Result | Lean declaration | Exact hypotheses and status |
| --- | --- | --- |
| An integer relation among rational lifts maps to the same relation after reduction | `XedniObstruction.relation_reduces` in `experiments/xedni-lattice-obstruction-20261028/formal/XedniObstruction.lean` | General additive homomorphism and integer coefficient vector. Existing declaration; this experiment does not change it. |
| The displayed rational curve and points satisfy `Q₁+2Q₂=O` | `XedniCrtRationalWitness.rational_relation` | Exact Weierstrass curve over `ℚ` with coefficients `[-987,-1034,0,7660,-3997]`, points `(14,7)` and `(17,10)`, nonzero discriminant, and Mathlib affine point group law. Pinned Lean build passed; `#print axioms` lists only standard foundations. |
| The rational witness has the stated reductions and auxiliary curve orders | — | Exact Sage launcher and independent finite-field arithmetic in `audit.py`; Lean reduction and group-order bridge remain open. |
| If `(w-t₁)+2(w-t₂)=0` in `ZMod 43`, recover `w=(t₁+2t₂)/3` | `XedniCrtTargetRecovery.recover_of_relation` | Prime field `ZMod 43`, nonzero divisor 3 supplied by the field arithmetic. Pinned Lean build passed; `#print axioms` lists only `propext`, `Classical.choice`, `Quot.sound`. |
| The saved pairs `(29,11)` and `(5,23)` give scalar 17 | `XedniCrtTargetRecovery.recovered_scalar_29_11`, `recovered_scalar_5_23` | Exact `ZMod 43` arithmetic. Pinned Lean build passed with the same standard axiom list. |
| The fixed public input `G=(2,2)`, `Q=(26,8)` and rational relation rows instantiate the preceding algebra on elliptic curves | — | Checked by exhaustive Sage target replay and independent exact finite-field arithmetic in `audit.py`. A faithful Lean finite-curve bridge remains open. |
| Any full-field asymptotic bound for the original xedni curve-selection law | — | Requires a formalized height/discriminant premise and the actual coefficient/point selection distribution. Open. |

The current shared checkout's `xedni-lattice-obstruction-20261028/verify.py`
returns `AssertionError: XedniObstruction.lean` on its source hash. This
experiment therefore does not report a fresh Lean build for that imported
module. A formalization follow-up must use an isolated, pinned source
snapshot, build its actual theorem module, and audit `#print axioms` before
claiming a fresh result for that separate module.

The new `formal/TargetRecovery.lean` and `formal/RationalWitness.lean` use Lean
`leanprover/lean4:v4.35.0-rc4` and Mathlib
`021c46bdd042f67b538b9f9871d556a93713a9a9`. The actual
`lake build TargetRecovery RationalWitness` output, source hashes and all four
`#print axioms` results are retained in `formal/`; `verify_formal.py`
checks them. `lean4checker --fresh` is unavailable on this host.
