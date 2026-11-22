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

def reverseBatch {F : Type} [Field F] (xs : List F) (q : F) : List F :=
  match xs with
  | [] => []
  | x :: tail => (q * tail.prod) :: reverseBatch tail (q * x)

theorem nonzero_prod {F : Type} [Field F]
    (xs : List F) (h : ∀ x ∈ xs, x ≠ 0) : xs.prod ≠ 0 := by
  induction xs with
  | nil =>
    intro heq
    exact Field.zero_ne_one heq.symm
  | cons x tail ih =>
    have hx : x ≠ 0 := h x (by simp)
    have ht : tail.prod ≠ 0 := ih (by
      intro y hy
      exact h y (by simp [hy]))
    intro heq
    have hz := Field.of_mul_eq_zero heq
    cases hz with
    | inl hz => exact hx hz
    | inr hz => exact ht hz

theorem reverseBatch_correct {F : Type} [Field F]
    (xs : List F) (h : ∀ x ∈ xs, x ≠ 0) :
    reverseBatch xs (xs.prod)⁻¹ = xs.map (·⁻¹) := by
  induction xs with
  | nil => simp [reverseBatch]
  | cons x tail ih =>
    have hx : x ≠ 0 := h x (by simp)
    have ht : tail.prod ≠ 0 := nonzero_prod tail (by
      intro y hy
      exact h y (by simp [hy]))
    have htail : ∀ y ∈ tail, y ≠ 0 := by
      intro y hy
      exact h y (by simp [hy])
    simp only [reverseBatch, List.prod_cons, List.map_cons]
    rw [inverse_first_from_product x tail.prod ht,
        inverse_last_from_product x tail.prod hx, ih htail]

#print axioms reverseBatch_correct
#print axioms nonzero_prod
#print axioms reverseBatch
#print axioms inverse_first_from_product
#print axioms inverse_last_from_product
end BatchOutput
