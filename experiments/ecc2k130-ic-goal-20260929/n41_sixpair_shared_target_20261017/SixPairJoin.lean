import Std
import Init.Grind.Ring.Basic

namespace SixPairJoin
open Lean.Grind

/-- The five links compute the sum of exactly the six pair points. -/
theorem balanced_six_sum {G : Type} [AddCommGroup G]
    (p₀ p₁ p₂ p₃ p₄ p₅ : G) :
    ((p₀ + p₁) + (p₂ + p₃)) + (p₄ + p₅) =
      (((((p₀ + p₁) + p₂) + p₃) + p₄) + p₅) := by
  calc
    ((p₀ + p₁) + (p₂ + p₃)) + (p₄ + p₅)
        = (((p₀ + p₁) + p₂) + p₃) + (p₄ + p₅) := by
          rw [← AddCommMonoid.add_assoc (p₀ + p₁) p₂ p₃]
    _ = (((((p₀ + p₁) + p₂) + p₃) + p₄) + p₅) := by
          rw [← AddCommMonoid.add_assoc]

/-- An exact right-triple match is equivalent to the target-conditioned
    left-table lookup used by the join. -/
theorem target_conditioned_lookup {G : Type} [AddCommGroup G]
    (left right target : G) :
    left + right = target ↔ left = target - right := by
  constructor
  · intro h
    calc
      left = (left + right) - right := AddCommGroup.add_sub_cancel.symm
      _ = target - right := by rw [h]
  · intro h
    calc
      left + right = (target - right) + right := by rw [h]
      _ = target := AddCommGroup.sub_add_cancel

#print axioms balanced_six_sum
#print axioms target_conditioned_lookup

end SixPairJoin
