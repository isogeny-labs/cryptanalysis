module

public import Mathlib.Algebra.BigOperators.Group.Finset.Basic
public import Mathlib.Data.Rat.Defs

/-! Exact local criterion used to interpret disjoint floor-pair supports. -/

namespace FloorIncidence

open scoped BigOperators

/-- If the pair supports are disjoint and cover every floor coordinate,
a cycle vector is in their span precisely when it is a scalar multiple
of each pair vector on that pair's support. -/
public theorem disjoint_pair_span_iff
    {I J : Type*} [Fintype I] [DecidableEq I]
    (pair : I → J → ℚ) (cycle : J → ℚ)
    (disjoint : ∀ i k j, i ≠ k → pair i j ≠ 0 → pair k j = 0)
    (cover : ∀ j, ∃ i, pair i j ≠ 0) :
    (∃ a : I → ℚ, ∀ j, cycle j = ∑ i, a i * pair i j) ↔
      (∃ a : I → ℚ, ∀ i j, pair i j ≠ 0 → cycle j = a i * pair i j) := by
  constructor
  · rintro ⟨a, ha⟩
    refine ⟨a, ?_⟩
    intro i j hij
    rw [ha j]
    apply Finset.sum_eq_single i
    · intro k _ hki
      simp [disjoint i k j (Ne.symm hki) hij]
    · simp
  · rintro ⟨a, ha⟩
    refine ⟨a, ?_⟩
    intro j
    obtain ⟨i, hij⟩ := cover j
    rw [ha i j hij]
    symm
    apply Finset.sum_eq_single i
    · intro k _ hki
      simp [disjoint i k j (Ne.symm hki) hij]
    · simp

end FloorIncidence

#print axioms FloorIncidence.disjoint_pair_span_iff
