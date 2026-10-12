import Std

/-! The group-level justification for looking up a left sum by its x coordinate.
The binary-curve x-fiber property and the concrete state-ID sign pairing are
checked separately in the source and Sage replay. -/
namespace N41XQuotient

universe u v

theorem target_x_match
    {G : Type u} {X : Type v}
    (add : G → G → G) (neg : G → G) (sub : G → G → G)
    (subAdd : ∀ a b : G, add (sub a b) b = a)
    (x : G → X)
    (xFiber : ∀ a b : G, x a = x b → a = b ∨ neg a = b)
    (left right target : G)
    (hit : x left = x (sub target right)) :
    add left right = target ∨ add (neg left) right = target := by
  rcases xFiber left (sub target right) hit with h | h
  · left
    rw [h]
    exact subAdd target right
  · right
    rw [h]
    exact subAdd target right

theorem target_x_complete
    {G : Type u} {X : Type v}
    (add : G → G → G) (neg : G → G) (sub : G → G → G)
    (addSub : ∀ a b : G, sub (add a b) b = a)
    (x : G → X)
    (xNeg : ∀ a : G, x (neg a) = x a)
    (left right target : G)
    (hit : add left right = target ∨ add (neg left) right = target) :
    x left = x (sub target right) := by
  rcases hit with h | h
  · have hneed : sub target right = left := by
      rw [← h]
      exact addSub left right
    rw [hneed]
  · have hneed : sub target right = neg left := by
      rw [← h]
      exact addSub (neg left) right
    rw [hneed, xNeg]

#print axioms N41XQuotient.target_x_match
#print axioms N41XQuotient.target_x_complete

end N41XQuotient
