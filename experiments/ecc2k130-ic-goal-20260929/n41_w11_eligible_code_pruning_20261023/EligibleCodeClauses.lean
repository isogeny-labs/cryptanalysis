import Std

namespace EligibleCodeClauses

/-- A generated ten-literal clause says that at least one source-code bit
differs from this forbidden code. -/
def forbids (bits code : Fin 10 → Bool) : Prop :=
  ∃ i : Fin 10, bits i ≠ code i

theorem forbids_iff_ne (bits code : Fin 10 → Bool) :
    forbids bits code ↔ bits ≠ code := by
  constructor
  · rintro ⟨i, hi⟩ heq
    exact hi (congrFun heq i)
  · intro h
    by_cases hn : forbids bits code
    · exact hn
    · have heq : bits = code := by
        funext i
        by_cases hi : bits i = code i
        · exact hi
        · exact False.elim (hn ⟨i, hi⟩)
      exact False.elim (h heq)

/-- Forbidding every code outside an exact eligible set accepts precisely
the members of that set. This is the logical basis for the four SAT slots. -/
theorem all_forbidden_iff_eligible
    (eligible : List (Fin 10 → Bool)) (bits : Fin 10 → Bool) :
    (∀ code, code ∉ eligible → forbids bits code) ↔ bits ∈ eligible := by
  classical
  constructor
  · intro h
    by_cases hb : bits ∈ eligible
    · exact hb
    · obtain ⟨i, hi⟩ := h bits hb
      exact False.elim (hi rfl)
  · intro hb code hc
    apply (forbids_iff_ne bits code).2
    intro heq
    subst code
    exact hc hb

theorem four_slots_iff_eligible
    (eligible : List (Fin 10 → Bool))
    (slots : Fin 4 → Fin 10 → Bool) :
    (∀ slot code, code ∉ eligible → forbids (slots slot) code) ↔
      (∀ slot, slots slot ∈ eligible) := by
  constructor
  · intro h slot
    exact (all_forbidden_iff_eligible eligible (slots slot)).1 (h slot)
  · intro h slot
    exact (all_forbidden_iff_eligible eligible (slots slot)).2 (h slot)

#print axioms forbids_iff_ne
#print axioms all_forbidden_iff_eligible
#print axioms four_slots_iff_eligible

end EligibleCodeClauses
