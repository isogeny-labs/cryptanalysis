import Std

namespace SupportEncoding

/-- An at-least-one selector with every active selector bound to its row
represents exactly membership in the finite target-conditioned table. -/
theorem selectors_iff_row {α β : Type} {n : Nat}
    (rows : Fin n → α × β) (w : α) (code : β) :
    (∃ selected : Fin n → Prop,
       (∃ i, selected i) ∧
       (∀ i, selected i → rows i = (w, code))) ↔
    (∃ i, rows i = (w, code)) := by
  constructor
  · rintro ⟨selected, ⟨i, hi⟩, hbound⟩
    exact ⟨i, hbound i hi⟩
  · rintro ⟨i, hi⟩
    refine ⟨fun j => j = i, ⟨i, rfl⟩, ?_⟩
    intro j hj
    subst j
    exact hi

#print axioms SupportEncoding.selectors_iff_row

end SupportEncoding
