import Std
import Init.Grind.Ring.Field

namespace OutputFirst
open Lean.Grind

theorem pair_law_product {F : Type} [Field F]
    (H C p x : F) (hchar : ∀ z : F, z + z = 0)
    (hlaw : H * x * x + p * x + C = 0) :
    p * x = H * x * x + C := by
  have hA := hchar (H * x * x)
  have hC := hchar C
  grind

theorem product_from_output {F : Type} [Field F]
    (H C p x : F) (hx : x ≠ 0)
    (hp : p * x = H * x * x + C) :
    p = H * x + C / x := by
  have hcancel : (p * x) / x = p := by
    rw [Field.div_eq_mul_inv, Semiring.mul_assoc, Field.mul_inv_cancel hx,
        Semiring.mul_one]
  rw [← hcancel, hp, Field.div_eq_mul_inv, Semiring.right_distrib,
      Semiring.mul_assoc, Field.mul_inv_cancel hx, Semiring.mul_one,
      ← Field.div_eq_mul_inv]

/-- Once the source product map is injective, an output determines at most
one source code in the declared factor-base code space. -/
theorem unique_source_code {F Code : Type} [Field F]
    (encode : Code → F) (hinj : Function.Injective encode)
    (H C x : F) (hx : x ≠ 0) (c d : Code)
    (hc : encode c = H * x + C / x)
    (hd : encode d = H * x + C / x) : c = d := by
  apply hinj
  rw [hc, hd]

/-- The exact output formula follows from the characteristic-two pair law. -/
theorem recover_product {F : Type} [Field F]
    (H C p x : F) (hx : x ≠ 0)
    (hchar : ∀ z : F, z + z = 0)
    (hlaw : H * x * x + p * x + C = 0) :
    p = H * x + C / x := by
  exact product_from_output H C p x hx
    (pair_law_product H C p x hchar hlaw)

#print axioms unique_source_code
#print axioms recover_product
#print axioms pair_law_product
#print axioms product_from_output
end OutputFirst
