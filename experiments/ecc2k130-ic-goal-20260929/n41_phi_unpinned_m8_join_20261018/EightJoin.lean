import Std
import Init.Grind.Ring.Basic

namespace EightJoin
open Lean.Grind

/-- The two four-leaf sums used by the table cover all eight leaf points. -/
theorem four_plus_four_is_eight {G : Type} [AddCommGroup G]
    (p₀ p₁ p₂ p₃ p₄ p₅ p₆ p₇ : G) :
    ((p₀ + p₁) + (p₂ + p₃)) + ((p₄ + p₅) + (p₆ + p₇)) =
      (((((((p₀ + p₁) + p₂) + p₃) + p₄) + p₅) + p₆) + p₇) := by
  simp only [AddCommMonoid.add_assoc]

/-- The exact target-conditioned lookup key of the right four-leaf sum. -/
theorem target_lookup {G : Type} [AddCommGroup G]
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

#print axioms four_plus_four_is_eight
#print axioms target_lookup

end EightJoin
