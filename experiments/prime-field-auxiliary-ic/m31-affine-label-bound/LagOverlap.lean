import Mathlib

namespace M31LagOverlap
variable {G : Type*} [AddCommGroup G]

/-- A pair of eligible positions separated by a fixed displacement exists
exactly when that displacement is a difference of eligible positions. -/
theorem return_iff (A : Set G) (d : G) :
    (∃ x ∈ A, x+d ∈ A) ↔ ∃ y ∈ A, ∃ x ∈ A, y-x = d := by
  constructor
  · rintro ⟨x, hx, hnext⟩
    exact ⟨x+d, hnext, x, hx, by abel⟩
  · rintro ⟨y, hy, x, hx, rfl⟩
    exact ⟨x, hx, by simpa [add_comm] using hy⟩

/-- If no nontrivial lag in a fixed window is an eligible difference,
each start hits at most once. No hypothesis on randomness of steps is needed. -/
theorem unique_hit {I : Type*} (A : Set G) (offset : I → G)
    (separated : ∀ i j, i ≠ j → ¬ ∃ y ∈ A, ∃ x ∈ A, y-x = offset j-offset i)
    (start : G) (i j : I) (hi : start+offset i ∈ A) (hj : start+offset j ∈ A) : i = j := by
  by_contra ne
  exact separated i j ne ⟨_, hj, _, hi, by abel⟩

/-- The union bound for at most four comparisons per position in the
independent uniform reference model, at the fixed seed-one horizon. -/
theorem iidPairBudget :
    4*19300166*(578/2147505293 : ℚ)^2 < 56/10000000 := by norm_num

end M31LagOverlap
