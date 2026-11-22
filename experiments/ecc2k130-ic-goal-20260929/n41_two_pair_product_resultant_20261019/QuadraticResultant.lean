import Std
import Init.Grind.Ring.Basic

namespace QuadraticResultant
open Lean.Grind

/-- The characteristic-two quadratic resultant vanishes on any common
    root. Leading coefficients may vanish; the statement is a necessary
    condition and keeps all exceptional coefficient cases. -/
theorem common_root_implies_zero {F : Type} [Field F]
    (charTwo : ∀ x : F, x+x=0)
    (A B C D E G z : F)
    (hf : A*z^2+B*z+C=0)
    (hg : D*z^2+E*z+G=0) :
    (A*G+C*D)^2+(A*E+B*D)*(B*G+C*E)=0 := by
  have hC := charTwo (A*z^2+B*z)
  have hG := charTwo (D*z^2+E*z)
  grind +ring

#print axioms common_root_implies_zero

end QuadraticResultant
