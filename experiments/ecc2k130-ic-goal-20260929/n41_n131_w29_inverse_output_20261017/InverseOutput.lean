import Std
import Init.Grind.Ring.Basic

namespace InverseOutput
open Lean.Grind

/-- Over a characteristic-two commutative ring, the fixed-seed pair
    quadratic and a nonzero output give the linear product formula used
    to decode the source mask from the output and its inverse. -/
theorem product_from_output_inverse {F : Type} [CommRing F]
    (C H p z q : F)
    (two_zero : ∀ x : F, x + x = 0)
    (inverse : z * q = 1)
    (quadratic : C * z * z + p * z + H = 0) :
    p = C * z + H * q := by
  have multiplied : (C * z * z + p * z + H) * q = 0 := by
    calc
      (C * z * z + p * z + H) * q = 0 * q := by rw [quadratic]
      _ = 0 := by grind +ring
  have cancel : p + (C * z + H * q) = 0 := by grind +ring
  have doubled := two_zero (C * z + H * q)
  grind

/-- The linear product formula together with zq=1 reconstructs the exact
    fixed-seed quadratic, so the replacement does not drop a pair root. -/
theorem quadratic_from_output_inverse {F : Type} [CommRing F]
    (C H p z q : F)
    (two_zero : ∀ x : F, x + x = 0)
    (inverse : z * q = 1)
    (product : p = C * z + H * q) :
    C * z * z + p * z + H = 0 := by
  have h := two_zero (C * z * z)
  have h' := two_zero H
  grind +ring

#print axioms product_from_output_inverse
#print axioms quadratic_from_output_inverse

end InverseOutput
