import Std
import Init.Grind.Ring.Basic

namespace DirectProductLaw
open Lean.Grind

/-- Given `z=1/x`, the pair quadratic determines its product coefficient
from the residual point's x-coordinate in characteristic two. -/
theorem product_from_residual {F : Type} [Field F]
    (h2 : (2 : F) = 0) (x z C H q : F) (hx : x*z = 1) :
    C*z*z + q*z + H = 0 ↔ q = C*z + H*x := by
  constructor
  · intro h
    have hqz : q*z = (C*z + H*x)*z := by grind +ring
    have hzx : z*x = 1 := by grind +ring
    have hq : q = q*z*x := by grind +ring
    rw [hq, hqz]
    grind +ring
  · intro h
    rw [h]
    grind +ring

#print axioms product_from_residual

end DirectProductLaw
