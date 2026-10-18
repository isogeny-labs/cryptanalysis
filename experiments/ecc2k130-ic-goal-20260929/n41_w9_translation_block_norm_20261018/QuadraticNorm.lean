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
    grind
  · intro hz
    grind

/-- Evaluating a polynomial Bézout certificate at a source x root gives a
    nonzero norm and excludes both signs. The concrete GCD computes this
    certificate in the polynomial ring. -/
theorem bezout_rejects_both_branches {F : Type} [Field F]
    (x z a b y f u v : F) (hchar : (2 : F) = 0)
    (hcurve : y*y + x*y = z) (hroot : f = 0)
    (hbezout : u*f + v*(a*a + a*b*x + b*b*z) = 1) :
    a + b*y ≠ 0 ∧ a + b*(y+x) ≠ 0 := by
  have hnorm : a*a + a*b*x + b*b*z ≠ 0 := by
    grind
  exact norm_nonzero_excludes_branches x z a b y hchar hcurve hnorm

#print axioms conjugate_product
#print axioms norm_nonzero_excludes_branches
#print axioms bezout_rejects_both_branches

end TranslationBlockNorm
