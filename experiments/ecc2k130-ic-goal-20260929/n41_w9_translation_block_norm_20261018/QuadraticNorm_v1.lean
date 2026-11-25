import Std
import Init.Grind.Ring.Basic

namespace TranslationBlockNorm
open Lean.Grind

/-- The two binary-curve y branches have product equal to the quadratic
    norm used by the block gate. The curve equation is `y²+xy=z`. -/
theorem conjugate_product {F : Type} [Field F]
    (x z a b y : F) (hchar : (2 : F) = 0)
    (hcurve : y*y + x*y = z) :
    (a + b*y) * (a + b*(y+x)) =
      a*a + a*b*x + b*b*z := by
  grind +ring

/-- A nonzero norm excludes both possible signs at a fixed x coordinate. -/
theorem norm_nonzero_excludes_branches {F : Type} [Field F]
    (x z a b y : F) (hchar : (2 : F) = 0)
    (hcurve : y*y + x*y = z)
    (hnorm : a*a + a*b*x + b*b*z ≠ 0) :
    a + b*y ≠ 0 ∧ a + b*(y+x) ≠ 0 := by
  have hproduct := conjugate_product x z a b y hchar hcurve
  constructor
  · intro hz
    rw [hz] at hproduct
    simp at hproduct
    exact hnorm hproduct.symm
  · intro hz
    rw [hz] at hproduct
    simp at hproduct
    exact hnorm hproduct.symm

#print axioms conjugate_product
#print axioms norm_nonzero_excludes_branches

end TranslationBlockNorm
