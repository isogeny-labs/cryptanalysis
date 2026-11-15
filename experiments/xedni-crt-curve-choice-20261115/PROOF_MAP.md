# Formalization map

| Result | Lean declaration | Exact hypotheses and status |
| --- | --- | --- |
| An integer relation among rational lifts maps to the same relation after reduction | `XedniObstruction.relation_reduces` in `experiments/xedni-lattice-obstruction-20261028/formal/XedniObstruction.lean` | General additive homomorphism and integer coefficient vector. Existing declaration; this experiment does not change it. |
| The displayed rational curve and points satisfy `Q₁+2Q₂=O` | `XedniCrtRationalWitness.rational_relation` | Exact Weierstrass curve over `ℚ` with coefficients `[-987,-1034,0,7660,-3997]`, points `(14,7)` and `(17,10)`, nonzero discriminant, and Mathlib affine point group law. Pinned Lean build passed; `#print axioms` lists only standard foundations. |
| One integral Weierstrass model gives the rational curve and its mod-47 reduction | `XedniCrtRationalWitness.rational_model`, `reduced_model` | Maps the exact integer coefficient record to `ℚ` and `ZMod 47` by their integer cast ring homomorphisms. Both pinned Lean proofs pass with standard foundations. |
| The displayed points satisfy `P₁+2P₂=O` on `y²=x³−x−2` over `ZMod 47` | `XedniCrtRationalWitness.reduced_relation` | Exact finite-field Weierstrass curve and affine points `(14,7)`, `(17,10)`; pinned Lean build passed with the same standard axiom list. |
| The public points `G=(2,2)` and `Q=(26,8)` lie on the same finite-field curve | `XedniCrtRationalWitness.eqG`, `eqQ`; definitions `G`, `Q` | Exact `ZMod 47` point equations and affine point constructors. Pinned Lean build passed; `#print axioms` lists only standard foundations. |
| The rational witness has the stated point reductions and auxiliary curve orders | — | The two relation theorems use corresponding integer coordinates and the proven integral model. The point-reduction homomorphism and auxiliary group orders are checked by the Sage launcher and independent finite-field arithmetic in `audit.py`; their Lean bridge remains open. |
| If `(w-t₁)+2(w-t₂)=0` in `ZMod 43`, recover `w=(t₁+2t₂)/3` | `XedniCrtTargetRecovery.recover_of_relation` | Prime field `ZMod 43`, nonzero divisor 3 supplied by the field arithmetic. Pinned Lean build passed; `#print axioms` lists only `propext`, `Classical.choice`, `Quot.sound`. |
| The saved pairs `(29,11)` and `(5,23)` give scalar 17 | `XedniCrtTargetRecovery.recovered_scalar_29_11`, `recovered_scalar_5_23` | Exact `ZMod 43` arithmetic. Pinned Lean build passed with the same standard axiom list. |
| The fixed public input obeys `17 • G = Q` | `XedniCrtRationalWitness.public_scalar` | Exact Mathlib affine point group over `ZMod 47`. `decide +kernel` checks the finite computation in Lean's kernel; pinned build and `#print axioms` pass with standard foundations. The prior plain-`decide` failure is retained in `formal/public-scalar-attempt.txt`. |
| The rational relation rows recover scalar 17 from that public input | `XedniCrtTargetRecovery.recovered_scalar_29_11`, `recovered_scalar_5_23` | Lean checks the two `ZMod 43` arithmetic certificates; exhaustive Sage target replay and independent finite-field arithmetic in `audit.py` check the row-to-lift construction. A Lean row-to-lift bridge remains open. |
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
`lake build TargetRecovery RationalWitness` output, source hashes and all ten
`#print axioms` results are retained in `formal/`; `verify_formal.py`
checks them. `lean4checker --fresh` is unavailable on this host.
