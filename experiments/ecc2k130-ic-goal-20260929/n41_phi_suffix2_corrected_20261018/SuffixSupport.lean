import Std
import Init.Grind.Ring.Basic

namespace SuffixSupport
open Lean.Grind

/-- The exact residual for a fixed signed two-point suffix. -/
theorem residual_iff {G : Type} [AddCommGroup G]
    (preSum p10 p11 endpoint : G) :
    (preSum + p10) + p11 = endpoint ↔
      preSum = endpoint - (p10 + p11) := by
  constructor
  · intro h
    have hsum : preSum + (p10 + p11) = endpoint := by
      rw [← AddCommMonoid.add_assoc]
      exact h
    calc
      preSum = (preSum + (p10 + p11)) - (p10 + p11) :=
        AddCommGroup.add_sub_cancel.symm
      _ = endpoint - (p10 + p11) := by rw [hsum]
  · intro h
    calc
      (preSum + p10) + p11 = preSum + (p10 + p11) := by
        rw [AddCommMonoid.add_assoc]
      _ = (endpoint - (p10 + p11)) + (p10 + p11) := by rw [h]
      _ = endpoint := AddCommGroup.sub_add_cancel

#print axioms residual_iff

end SuffixSupport
