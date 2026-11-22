import Std
import Init.Grind.Ring.Basic

namespace NegationQuotient
open Lean.Grind

/-- Negating each of three source pair sums negates their partial sum. -/
theorem tripleNegation {G : Type} [AddCommGroup G] (a b c : G) :
    ((-a) + (-b)) + (-c) = -((a + b) + c) := by
  simp [AddCommGroup.neg_add]

/-- The exact public-target lookup key for a right partial sum remains
target conditioned after the left index is quotiented by negation. -/
theorem lookupEitherSign {G : Type} [AddCommGroup G]
    (left right target : G) :
    (left + right = target ∨ (-left) + right = target) ↔
      (left = target - right ∨ -left = target - right) := by
  have lookup (x : G) : x + right = target ↔ x = target - right := by
    constructor
    · intro h
      calc
        x = (x + right) - right := AddCommGroup.add_sub_cancel.symm
        _ = target - right := by rw [h]
    · intro h
      calc
        x + right = (target - right) + right := by rw [h]
        _ = target := AddCommGroup.sub_add_cancel
  constructor
  · intro h
    rcases h with h | h
    · exact Or.inl ((lookup left).mp h)
    · exact Or.inr ((lookup (-left)).mp h)
  · intro h
    rcases h with h | h
    · exact Or.inl ((lookup left).mpr h)
    · exact Or.inr ((lookup (-left)).mpr h)

#print axioms tripleNegation
#print axioms lookupEitherSign

end NegationQuotient
