import Std
import Init.Grind.Ring.Basic

namespace XPairLookup
open Lean.Grind

/-- If the key identifies a group point up to sign, one stored pair witness
    gives an exact witness for either point in that key's fiber. -/
theorem lift_sign {G X : Type} [AddCommGroup G]
    (key : G → X)
    (fiber : ∀ u v : G, key u = key v → u = v ∨ u = -v)
    (a b target : G) (h : key (a + b) = key target) :
    (a + b = target) ∨ ((-a) + (-b) = target) := by
  rcases fiber (a + b) target h with same | opposite
  · exact Or.inl same
  · right
    calc
      (-a) + (-b) = -(a + b) := (AddCommGroup.neg_add a b).symm
      _ = -(-target) := by rw [opposite]
      _ = target := AddCommGroup.neg_neg target

#print axioms lift_sign

end XPairLookup
