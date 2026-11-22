import Std
import Init.Grind.Ring.Basic

namespace FoldedJoin
open Lean.Grind

/-- Reuse one triple sum when three right states are pointwise images of
    the corresponding left states under an additive Frobenius map. -/
theorem right_triple_from_left {G : Type} [AddCommGroup G]
    (f : G → G) (hf : ∀ x y, f (x + y) = f x + f y)
    (a b c a' b' c' : G)
    (ha : a' = f a) (hb : b' = f b) (hc : c' = f c) :
    (a' + b') + c' = f ((a + b) + c) := by
  rw [ha, hb, hc, hf, hf]

/-- The folded right sum has the same exact public-target lookup law. -/
theorem folded_target_lookup {G : Type} [AddCommGroup G]
    (f : G → G) (left a b c target : G) :
    left + f ((a + b) + c) = target ↔
      left = target - f ((a + b) + c) := by
  constructor
  · intro h
    calc
      left = (left + f ((a + b) + c)) - f ((a + b) + c) :=
        AddCommGroup.add_sub_cancel.symm
      _ = target - f ((a + b) + c) := by rw [h]
  · intro h
    rw [h]
    exact AddCommGroup.sub_add_cancel

#print axioms right_triple_from_left
#print axioms folded_target_lookup
end FoldedJoin
