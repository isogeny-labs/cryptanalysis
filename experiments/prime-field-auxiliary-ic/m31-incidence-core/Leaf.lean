import Mathlib

namespace ArchivedIncidence

/-- In a homogeneous row dependence, a column occupied by only one of the
remaining rows forces that row's weight to vanish. Previously removed rows
may still have entries in the column, provided their weights are zero. -/
theorem leafWeight {F I : Type*} [Field F] [DecidableEq I]
    (rows : Finset I) (w column : I → F) (leaf : I) (hmem : leaf ∈ rows)
    (hn : column leaf ≠ 0)
    (outside : ∀ i ∈ rows, i ≠ leaf → w i = 0 ∨ column i = 0)
    (dependency : ∑ i ∈ rows, w i * column i = 0) : w leaf = 0 := by
  have h : ∑ i ∈ rows, w i * column i = w leaf * column leaf := by
    apply Finset.sum_eq_single_of_mem leaf hmem
    intro i hi hne
    exact mul_eq_zero.mpr (outside i hi hne)
  exact (mul_eq_zero.mp (h.symm.trans dependency)).resolve_right hn

/-- If the preceding rows admit only the zero relation, every nonzero
dependence after adding one row must use that row. -/
theorem lastWeight {F I V : Type*} [Field F] [AddCommGroup V] [Module F V]
    [DecidableEq I] (prior : Finset I) (last : I) (fresh : last ∉ prior)
    (rows : I → V) (w : I → F)
    (independent : ∀ c : I → F, ∑ i ∈ prior, c i • rows i = 0 →
      ∀ i ∈ prior, c i = 0)
    (dependency : ∑ i ∈ insert last prior, w i • rows i = 0)
    (nonzero : ∃ i ∈ insert last prior, w i ≠ 0) : w last ≠ 0 := by
  intro hz
  rw [Finset.sum_insert fresh, hz, zero_smul, zero_add] at dependency
  obtain ⟨i, hi, hn⟩ := nonzero
  rcases Finset.mem_insert.mp hi with rfl | hi
  · exact hn hz
  · exact hn (independent w dependency i hi)

end ArchivedIncidence
