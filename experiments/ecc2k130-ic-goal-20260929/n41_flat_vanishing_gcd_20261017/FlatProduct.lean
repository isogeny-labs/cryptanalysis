import Std
import Init.Grind.Ring.Basic
open Lean.Grind

namespace FlatProduct

theorem mul_zero_iff {F : Type} [Field F] (a b : F) :
    a * b = 0 ↔ a = 0 ∨ b = 0 := by
  grind

theorem sub_zero_iff {F : Type} [Field F] (a b : F) :
    a - b = 0 ↔ a = b := by
  grind

def vanishingValue {F : Type} [Field F] (xs : List F) (z : F) : F :=
  (xs.map fun x => z - x).prod

/-- A finite list of source values defines a polynomial value that vanishes
exactly at members of that list. Repeated source values are allowed. -/
theorem vanishingValue_eq_zero_iff_mem {F : Type} [Field F]
    (xs : List F) (z : F) : vanishingValue xs z = 0 ↔ z ∈ xs := by
  induction xs with
  | nil =>
      simp [vanishingValue]
      grind
  | cons x rest ih =>
      simp [vanishingValue, mul_zero_iff, sub_zero_iff] at ih ⊢
      simp only [ih]

#print axioms mul_zero_iff
#print axioms sub_zero_iff
#print axioms vanishingValue_eq_zero_iff_mem

end FlatProduct
