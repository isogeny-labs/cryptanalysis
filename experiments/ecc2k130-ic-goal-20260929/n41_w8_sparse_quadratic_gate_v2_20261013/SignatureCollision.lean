import Std

/-! Pointwise soundness of the low-support truth-signature search. -/
namespace SignatureCollision

def bx (a b : Bool) : Bool := decide (a != b)

theorem pair_collision_implies_four_term_zero {α : Type}
    (f g h k : α → Bool)
    (equal_signatures : ∀ x, bx (f x) (g x) = bx (h x) (k x)) :
    ∀ x, bx (bx (bx (f x) (g x)) (h x)) (k x) = false := by
  intro x
  have hx := equal_signatures x
  cases hf : f x <;> cases hg : g x <;>
    cases hh : h x <;> cases hk : k x <;>
    simp [bx, hf, hg, hh, hk] at hx ⊢

theorem zero_coordinate_product {α : Type}
    (bit0 other : α → Bool)
    (trace_zero : ∀ x, bit0 x = false) :
    ∀ x, (bit0 x && other x) = false := by
  intro x
  rw [trace_zero x]
  rfl

#print axioms pair_collision_implies_four_term_zero
#print axioms zero_coordinate_product
end SignatureCollision
