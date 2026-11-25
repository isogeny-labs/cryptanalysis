import Mathlib.LinearAlgebra.Dimension.Constructions

namespace M31FourCoverage.PrivatePivots

theorem single_loss {I : Type*} [DecidableEq I] {before after : Finset I}
    (hsub : after ⊆ before) (hcard : before.card = after.card + 1) :
    ∃! i, i ∈ before \ after := by
  apply Finset.card_eq_one_iff_existsUnique.mp
  rw [Finset.card_sdiff_of_subset hsub, hcard]
  omega

/-- One residual nonzero row needs no private coordinate. Evaluating a
linear combination at the private coordinates first kills all other weights. -/
theorem span_rank {I J K : Type*} [Fintype I] [Field K]
    (v : I → J → K) (p : I → J) (last : I) (nonzero : v last ≠ 0)
    (diagonal : ∀ i, i ≠ last → v i (p i) ≠ 0)
    (off : ∀ i j, i ≠ last → j ≠ i → v j (p i) = 0) :
    Module.finrank K (Submodule.span K (Set.range v)) = Fintype.card I := by
  classical
  apply finrank_span_eq_card
  apply Fintype.linearIndependent_iff.mpr
  intro g hg
  have vanish (i : I) (hi : i ≠ last) : g i = 0 := by
    have h := congrFun hg (p i)
    simp only [Finset.sum_apply, Pi.smul_apply, smul_eq_mul, Pi.zero_apply] at h
    rw [Finset.sum_eq_single i] at h
    · exact (mul_eq_zero.mp h).resolve_right (diagonal i hi)
    · intro j _ hji
      rw [off i j hi hji, mul_zero]
    · simp
  intro i
  by_cases hi : i = last
  · subst i
    rw [Finset.sum_eq_single last] at hg
    · exact (smul_eq_zero.mp hg).resolve_right nonzero
    · intro j _ hj
      rw [vanish j hj, zero_smul]
    · simp
  · exact vanish i hi

end M31FourCoverage.PrivatePivots
