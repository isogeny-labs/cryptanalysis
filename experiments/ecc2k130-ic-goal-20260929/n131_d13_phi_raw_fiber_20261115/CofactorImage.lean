import Std
import Init.Grind.Ring.Basic

namespace CofactorImage
open Lean.Grind

/-- An additive subgroup-order projection of `P + tau(P)` doubles the
    torsion component when Frobenius fixes that component. -/
theorem projected_image_doubles {G : Type} [AddCommGroup G]
    (project : G → G) (P tauP : G)
    (additive : project (P + tauP) = project P + project tauP)
    (fixed : project tauP = project P) :
    project (P + tauP) = project P + project P := by
  rw [additive, fixed]

/-- The image of an order-four torsion class is an even class. -/
theorem image_class_even {G : Type} [AddCommGroup G]
    (project : G → G) (P tauP T : G)
    (additive : project (P + tauP) = project P + project tauP)
    (fixed : project tauP = project P)
    (order_four : (T + T) + (T + T) = 0)
    (source_class : project P = 0 ∨ project P = T ∨
                    project P = T + T ∨ project P = -T) :
    project (P + tauP) = 0 ∨ project (P + tauP) = T + T := by
  rw [projected_image_doubles project P tauP additive fixed]
  rcases source_class with h | h | h | h
  · left
    rw [h]
    exact AddCommMonoid.zero_add 0
  · right
    rw [h]
  · left
    rw [h, order_four]
  · right
    rw [h]
    have h2 : -(T + T) = T + T := by
      apply (AddCommGroup.add_left_inj (T + T)).mp
      rw [AddCommGroup.neg_add_cancel, order_four]
    calc
      -T + -T = -(T + T) := (AddCommGroup.neg_add T T).symm
      _ = T + T := h2

#print axioms projected_image_doubles
#print axioms image_class_even

end CofactorImage
