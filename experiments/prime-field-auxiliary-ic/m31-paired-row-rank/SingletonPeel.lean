import Mathlib.LinearAlgebra.FiniteDimensional.Lemmas

namespace PublicRowRank

/-- Adding a row with a private nonzero column increases row rank by one. -/
theorem singleton_column_rank {K C : Type*} [Field K] [Fintype C]
    (rows : Set (C → K)) (pivot : C → K) (col : C)
    (privateCol : ∀ r ∈ rows, r col = 0) (nonzero : pivot col ≠ 0) :
    Module.finrank K (Submodule.span K (insert pivot rows)) =
      Module.finrank K (Submodule.span K rows) + 1 := by
  let S := Submodule.span K rows
  have vanishes : S ≤ LinearMap.ker (LinearMap.proj col : (C → K) →ₗ[K] K) :=
    Submodule.span_le.mpr privateCol
  have outside : pivot ∉ S := fun h => nonzero (vanishes h)
  have pivot_ne : pivot ≠ 0 := fun h => outside (h ▸ S.zero_mem)
  have disj := Submodule.disjoint_span_singleton_of_notMem outside
  have dim := Submodule.finrank_sup_add_finrank_inf_eq S (Submodule.span K {pivot})
  rw [disj.eq_bot, finrank_bot, add_zero, finrank_span_singleton pivot_ne] at dim
  rw [Submodule.span_insert, sup_comm]
  exact dim

end PublicRowRank
