import Std
import Init.Grind.Ring.Basic

namespace TwoPlusOneJoin
open Lean.Grind

/-- Looking up a target-conditioned two-point sum preserves exactly the
    five-point relations for the declared two-plus-one-versus-two tree. -/
theorem exact_pair_lookup {G : Type} [AddCommGroup G]
    (left third right target : G) :
    (left + third) + right = target ↔
      left = target - (third + right) := by
  constructor
  · intro h
    have hsum : left + (third + right) = target := by
      rw [← AddCommMonoid.add_assoc]
      exact h
    calc
      left = (left + (third + right)) - (third + right) :=
        AddCommGroup.add_sub_cancel.symm
      _ = target - (third + right) := by rw [hsum]
  · intro h
    calc
      (left + third) + right = left + (third + right) := by
        rw [AddCommMonoid.add_assoc]
      _ = (target - (third + right)) + (third + right) := by rw [h]
      _ = target := AddCommGroup.sub_add_cancel

#print axioms exact_pair_lookup

end TwoPlusOneJoin
