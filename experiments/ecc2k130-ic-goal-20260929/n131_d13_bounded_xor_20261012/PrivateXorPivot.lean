import Std

/-! A single GF(2) pivot step used by the bounded-fill XCNF projector. -/

namespace PrivateXorPivot

theorem row_addition (a b p q x : Bool) :
    (x.xor a = p ∧ x.xor b = q) ↔
      (x.xor a = p ∧ a.xor b = p.xor q) := by
  cases a <;> cases b <;> cases p <;> cases q <;> cases x <;> decide

theorem elimination (a b p q : Bool) :
    (∃ x : Bool, x.xor a = p ∧ x.xor b = q) ↔
      a.xor b = p.xor q := by
  cases a <;> cases b <;> cases p <;> cases q <;> decide

theorem elimination_list (a p : Bool) (equations : List (Bool × Bool)) :
    (∃ x : Bool, x.xor a = p ∧
      ∀ equation ∈ equations, x.xor equation.1 = equation.2) ↔
    (∀ equation ∈ equations, a.xor equation.1 = p.xor equation.2) := by
  constructor
  · rintro ⟨x, hx, rest⟩ equation member
    exact ((row_addition a equation.1 p equation.2 x).mp
      ⟨hx, rest equation member⟩).2
  · intro rest
    let x := p.xor a
    have hx : x.xor a = p := by
      cases a <;> cases p <;> decide
    refine ⟨x, hx, ?_⟩
    intro equation member
    exact ((row_addition a equation.1 p equation.2 x).mpr
      ⟨hx, rest equation member⟩).2

#print axioms PrivateXorPivot.row_addition
#print axioms PrivateXorPivot.elimination
#print axioms PrivateXorPivot.elimination_list

end PrivateXorPivot
