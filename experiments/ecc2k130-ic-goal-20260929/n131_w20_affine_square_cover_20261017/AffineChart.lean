import Std
import Init.Grind.Ring.Basic

namespace AffineChart
open Lean.Grind

/-- An additive source map stays affine in the two selector bits of a
four-code parallelogram, regardless of which two independent directions
were selected. -/
theorem map_two_bit_chart {G H : Type} [AddCommGroup G] [AddCommGroup H]
    (f : G → H) (hadd : ∀ x y, f (x + y) = f x + f y)
    (hzero : f 0 = 0) (a d₁ d₂ : G) (u v : Bool) :
    f (a + (if u then d₁ else 0) + (if v then d₂ else 0)) =
      f a + (if u then f d₁ else 0) + (if v then f d₂ else 0) := by
  cases u <;> cases v <;> simp [hadd, hzero]

/-- The fixed-seed pair product `x * (x + s)` is additive in a
characteristic-two source coordinate. -/
theorem pair_product_add {R : Type} [CommRing R]
    (s x y : R) (charTwo : ∀ z : R, z + z = 0) :
    (x + y) * (x + y + s) = x * (x + s) + y * (y + s) := by
  have hxy := charTwo (x * y)
  grind

#print axioms map_two_bit_chart
#print axioms pair_product_add

end AffineChart
