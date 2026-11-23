import Std
import Init.Grind.Ring.Basic

open Lean.Grind

namespace NormRoot

/-- Polynomial division, evaluated at a root of the divisor, preserves the
value of a product. The division identity is the explicit input. -/
theorem reduced_product_value {R : Type} [CommRing R]
    (factors : List R) (remainder divisorValue quotient : R)
    (division : factors.prod = remainder + divisorValue * quotient)
    (root : divisorValue = 0) :
    remainder = factors.prod := by
  have h : factors.prod = remainder := by
    simpa only [root, Semiring.zero_mul, Semiring.add_zero] using division
  exact h.symm

theorem reduced_product_zero_iff {R : Type} [CommRing R]
    (factors : List R) (remainder divisorValue quotient : R)
    (division : factors.prod = remainder + divisorValue * quotient)
    (root : divisorValue = 0) :
    remainder = 0 ↔ factors.prod = 0 := by
  rw [reduced_product_value factors remainder divisorValue quotient division root]

/-- The characteristic-two linearized-annihilator update keeps every old
root and also kills the new basis value. -/
theorem annihilator_update_old_root {R : Type} [CommRing R]
    (oldValue alpha : R) (h : oldValue = 0) :
    oldValue * oldValue + alpha * oldValue = 0 := by
  simp only [h, Semiring.mul_zero, Semiring.add_zero]

theorem annihilator_update_new_basis {R : Type} [CommRing R]
    (alpha : R) (charTwo : alpha + alpha = 0) :
    alpha * alpha + alpha * alpha = 0 := by
  calc
    alpha * alpha + alpha * alpha = (alpha + alpha) * alpha := by grind
    _ = 0 := by simp only [charTwo, Semiring.zero_mul]

#print axioms reduced_product_value
#print axioms reduced_product_zero_iff
#print axioms annihilator_update_old_root
#print axioms annihilator_update_new_basis

end NormRoot
