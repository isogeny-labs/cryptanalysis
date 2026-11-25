import Mathlib

namespace M31Round
variable {K I A B : Type*} [Field K] [Fintype A] [Fintype B]

theorem extend (old : A → I → K) (new : B → I → K) (pivot : B → I)
    (indep : LinearIndependent K old)
    (prior : ∀ a j, old a (pivot j) = 0)
    (diag : ∀ j, new j (pivot j) ≠ 0)
    (off : ∀ i j, i ≠ j → new i (pivot j) = 0) :
    LinearIndependent K (Sum.elim old new) := by
  classical
  apply Fintype.linearIndependent_iff.mpr
  intro c dep
  rw [Fintype.sum_sum_type] at dep
  simp only [Sum.elim_inl, Sum.elim_inr] at dep
  have hz (j : B) : c (Sum.inr j) = 0 := by
    have h := congrFun dep (pivot j)
    simp only [Pi.add_apply, Finset.sum_apply, Pi.smul_apply, smul_eq_mul, prior,
      mul_zero, Finset.sum_const_zero, zero_add, Pi.zero_apply] at h
    rw [Finset.sum_eq_single j] at h
    · exact (mul_eq_zero.mp h).resolve_right (diag j)
    · intro i _ hij
      simp [off i j hij]
    · simp
  simp only [hz, zero_smul, Finset.sum_const_zero, add_zero] at dep
  intro i
  cases i with
  | inl a => exact Fintype.linearIndependent_iff.mp indep _ dep a
  | inr b => exact hz b

theorem span_dimension (old : A → I → K) (new : B → I → K) (pivot : B → I)
    (indep : LinearIndependent K old) (prior : ∀ a j, old a (pivot j) = 0)
    (diag : ∀ j, new j (pivot j) ≠ 0)
    (off : ∀ i j, i ≠ j → new i (pivot j) = 0) :
    Module.finrank K (Submodule.span K (Set.range (Sum.elim old new))) =
      Fintype.card A + Fintype.card B := by
  rw [finrank_span_eq_card (extend old new pivot indep prior diag off), Fintype.card_sum]

/-- Aggregate existence certificates suffice: choose one admissible row for
each coordinate, then apply the dimension theorem to the combined family. -/
theorem exists_extension (old : A → I → K) (pivot : B → I)
    (admissible : B → (I → K) → Prop)
    (indep : LinearIndependent K old) (prior : ∀ a j, old a (pivot j) = 0)
    (witness : ∀ i, ∃ v, admissible i v ∧ v (pivot i) ≠ 0 ∧
      ∀ j, i ≠ j → v (pivot j) = 0) :
    ∃ new : B → I → K, (∀ i, admissible i (new i)) ∧
      LinearIndependent K (Sum.elim old new) ∧
      Module.finrank K (Submodule.span K (Set.range (Sum.elim old new))) =
        Fintype.card A + Fintype.card B := by
  choose new valid diag off using witness
  exact ⟨new, valid, extend old new pivot indep prior diag off,
    span_dimension old new pivot indep prior diag off⟩

/-- An ambient relation space can also contain rows outside the certified family. -/
theorem space_lower_bound {n m : ℕ} (old : Fin n → I → K) (pivot : Fin m → I)
    (space : Submodule K (I → K)) [FiniteDimensional K space]
    (indep : LinearIndependent K old) (inSpace : ∀ i, old i ∈ space)
    (prior : ∀ i j, old i (pivot j) = 0)
    (witness : ∀ i, ∃ v ∈ space, v (pivot i) ≠ 0 ∧ ∀ j, i ≠ j → v (pivot j) = 0) :
    n + m ≤ Module.finrank K space := by
  obtain ⟨new, valid, _, dim⟩ :=
    exists_extension old pivot (fun _ v => v ∈ space) indep prior witness
  have incl : Submodule.span K (Set.range (Sum.elim old new)) ≤ space := by
    apply Submodule.span_le.mpr
    rintro _ ⟨i, rfl⟩
    cases i with
    | inl a => exact inSpace a
    | inr b => exact valid b
  have bound := Submodule.finrank_mono incl
  simpa [dim] using bound

end M31Round
