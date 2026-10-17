import Std

namespace PrefixGate

/-- An exact common group point remains common after any coordinate summary. -/
theorem shared_prefix_of_exact_match {α β : Type} (prefix : α → β)
    (left right : List α) (point : α)
    (hl : point ∈ left) (hr : point ∈ right) :
    ∃ key, key ∈ left.map prefix ∧ key ∈ right.map prefix := by
  exact ⟨prefix point, List.mem_map.mpr ⟨point, hl, rfl⟩,
    List.mem_map.mpr ⟨point, hr, rfl⟩⟩

/-- Disjoint summary sets certify that no exact group point is shared. -/
theorem no_exact_match_of_disjoint_prefix {α β : Type} (prefix : α → β)
    (left right : List α)
    (h : ¬ ∃ key, key ∈ left.map prefix ∧ key ∈ right.map prefix) :
    ¬ ∃ point, point ∈ left ∧ point ∈ right := by
  rintro ⟨point, hl, hr⟩
  exact h (shared_prefix_of_exact_match prefix left right point hl hr)

#print axioms PrefixGate.shared_prefix_of_exact_match
#print axioms PrefixGate.no_exact_match_of_disjoint_prefix

end PrefixGate
