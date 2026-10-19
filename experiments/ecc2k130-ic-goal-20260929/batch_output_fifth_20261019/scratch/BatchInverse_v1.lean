import Std
import Init.Grind.Ring.Field

namespace BatchOutput
open Lean.Grind

/-- From the inverse of a product, recover the inverse of its first factor. -/
theorem inverse_first_from_product {F : Type} [Field F]
    (a tail : F) (ht : tail ≠ 0) :
    (a * tail)⁻¹ * tail = a⁻¹ := by
  rw [Field.inv_mul, Semiring.mul_assoc, CommSemiring.mul_comm tail⁻¹ tail,
      Field.mul_inv_cancel ht, Semiring.mul_one]

/-- From the inverse of a product, recover the inverse of its last factor. -/
theorem inverse_last_from_product {F : Type} [Field F]
    (head b : F) (hh : head ≠ 0) :
    (head * b)⁻¹ * head = b⁻¹ := by
  rw [Field.inv_mul, Semiring.mul_assoc, CommSemiring.mul_comm b⁻¹ head,
      ← Semiring.mul_assoc, CommSemiring.mul_comm head⁻¹ head,
      Field.mul_inv_cancel hh, Semiring.one_mul]

#print axioms inverse_first_from_product
#print axioms inverse_last_from_product
end BatchOutput
