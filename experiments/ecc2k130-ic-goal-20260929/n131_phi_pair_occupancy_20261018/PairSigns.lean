import Std
import Init.Grind.Ring.Basic

namespace PairSigns
open Lean.Grind

/-- Simultaneously reversing two leaf signs negates their group sum. -/
theorem mirrored_sum {G : Type} [AddCommGroup G] (a b : G) :
    -(a + b) = (-a) + (-b) := by
  exact AddCommGroup.neg_add a b

#print axioms mirrored_sum

end PairSigns
