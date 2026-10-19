import Std
import Init.Grind.Ring.Basic

namespace QuadraticNorm
open Lean.Grind

/-- The norm in the quadratic coordinate algebra of a binary elliptic
    curve. The curve equation is exposed as a hypothesis. -/
theorem norm_identity {F : Type} [Field F]
    (charTwo : ∀ t : F, t+t=0)
    (X Y U V D : F) (hcurve : Y^2+X*Y=D) :
    (U+V*Y)*(U+V*(Y+X)) = U^2+U*V*X+V^2*D := by
  have hcross := charTwo (U*V*Y)
  grind +ring

#print axioms norm_identity

/-- A zero norm finds one of the two actual y-branches over the same x.
    This is the exactness property used before the final point check. -/
theorem norm_zero_iff_branch {F : Type} [Field F]
    (charTwo : ∀ t : F, t+t=0)
    (X Y U V D : F) (hcurve : Y^2+X*Y=D) :
    U^2+U*V*X+V^2*D=0 ↔
      U+V*Y=0 ∨ U+V*(Y+X)=0 := by
  have hnorm := norm_identity charTwo X Y U V D hcurve
  constructor
  · intro hz
    have hmul : (U+V*Y)*(U+V*(Y+X))=0 := by
      rw [hnorm]
      exact hz
    exact Field.of_mul_eq_zero hmul
  · intro hbranch
    have hmul : (U+V*Y)*(U+V*(Y+X))=0 := by
      rcases hbranch with hleft | hright
      · rw [hleft]
        grind +ring
      · rw [hright]
        grind +ring
    rw [hnorm] at hmul
    exact hmul

#print axioms norm_zero_iff_branch

end QuadraticNorm
