import Mathlib.Algebra.BigOperators.Group.Finset.Basic
import Mathlib.Algebra.Ring.Defs

namespace DisjointRows

variable {F I J A B : Type*} [Semiring F] [Fintype I] [Fintype J]

/-- Row families on disjoint coordinate sets, extended by zero. -/
def leftRow (u : A → F) : A ⊕ B → F := Sum.elim u (fun _ => 0)
def rightRow (v : B → F) : A ⊕ B → F := Sum.elim (fun _ => 0) v

/-- At any prefix, a weighted dependency among unmixed rows restricts
to a dependency in each block, using its original coefficients. -/
theorem cancel_iff (u : I → A → F) (v : J → B → F) (c : I → F) (d : J → F) :
    (∀ x : A ⊕ B, (∑ i, c i * leftRow (u i) x) +
      (∑ j, d j * rightRow (v j) x) = 0) ↔
    (∀ a, (∑ i, c i * u i a) = 0) ∧ (∀ b, (∑ j, d j * v j b) = 0) := by
  constructor
  · intro h
    exact ⟨fun a => by simpa [leftRow, rightRow] using h (.inl a),
           fun b => by simpa [leftRow, rightRow] using h (.inr b)⟩
  · rintro ⟨hl, hr⟩ (a | b)
    · simpa [leftRow, rightRow] using hl a
    · simpa [leftRow, rightRow] using hr b

#print axioms cancel_iff
end DisjointRows
