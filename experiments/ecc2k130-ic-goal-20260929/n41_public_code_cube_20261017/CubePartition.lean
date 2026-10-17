import Std

namespace CubePartition

/-- A seven-bit assignment surviving every forbidden-code clause belongs to
the allowed set and satisfies exactly one complete seven-bit cube. -/
theorem exactAllowedPartition
    (allowed : List (Fin 7 → Bool))
    (assignment : Fin 7 → Bool)
    (allForbiddenClauses :
      ∀ code : Fin 7 → Bool, code ∉ allowed →
        ∃ bit : Fin 7, assignment bit ≠ code bit) :
    ∃ code : Fin 7 → Bool,
      code ∈ allowed ∧
      (∀ bit : Fin 7, assignment bit = code bit) ∧
      (∀ other : Fin 7 → Bool, other ∈ allowed →
        (∀ bit : Fin 7, assignment bit = other bit) → other = code) := by
  classical
  have hAllowed : assignment ∈ allowed := Classical.byContradiction (fun hNot => by
    obtain ⟨bit, hDiff⟩ := allForbiddenClauses assignment hNot
    exact hDiff rfl)
  refine ⟨assignment, hAllowed, ?_, ?_⟩
  · intro bit
    rfl
  · intro other _ hOther
    exact funext (fun bit => (hOther bit).symm)

#print axioms exactAllowedPartition

end CubePartition
