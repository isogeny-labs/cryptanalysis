import UniformRelationBound
import Mathlib.Tactic

/-!
An adaptive coefficient choice can fit almost every observed field pair.
This identifies the fixed-family hypothesis needed by the uniform relation
counting theorem; it is an algebraic witness construction.
-/
namespace XedniAdaptiveCoefficientBoundary

variable {F : Type*} [Field F]

theorem adaptive_relation_iff (u v : F) :
    (∃ a b : F, b ≠ 0 ∧ a * u + b * v = 0) ↔ u ≠ 0 ∨ v = 0 := by
  constructor
  · rintro ⟨a, b, hb, hrel⟩
    by_cases hu : u = 0
    · right
      have hmul : b * v = 0 := by simpa [hu] using hrel
      exact (mul_eq_zero.mp hmul).resolve_left hb
    · exact Or.inl hu
  · rintro (hu | hv)
    · refine ⟨v, -u, neg_ne_zero.mpr hu, ?_⟩
      ring
    · refine ⟨0, 1, one_ne_zero, ?_⟩
      simp [hv]

theorem adaptive_witness_of_first_ne_zero (u v : F) (hu : u ≠ 0) :
    ∃ a b : F, b ≠ 0 ∧ a * u + b * v = 0 :=
  (adaptive_relation_iff u v).2 (Or.inl hu)

theorem no_adaptive_witness_when_first_zero_second_nonzero
    (v : F) (hv : v ≠ 0) :
    ¬ ∃ a b : F, b ≠ 0 ∧ a * 0 + b * v = 0 := by
  intro h
  obtain hu | hz := (adaptive_relation_iff (0 : F) v).1 h
  · exact hu rfl
  · exact hv hz

section Finite

variable [Fintype F] [DecidableEq F]

private def badEquiv :
    {uv : F × F // uv.1 = 0 ∧ uv.2 ≠ 0} ≃ {v : F // v ≠ 0} where
  toFun uv := ⟨uv.1.2, uv.2.2⟩
  invFun v := ⟨(0, v.1), ⟨rfl, v.2⟩⟩
  left_inv uv := by
    apply Subtype.ext
    apply Prod.ext
    · exact uv.2.1.symm
    · rfl
  right_inv _ := rfl

private def successEquiv :
    {uv : F × F // ∃ a b : F, b ≠ 0 ∧ a * uv.1 + b * uv.2 = 0} ≃
      {uv : F × F // ¬ (uv.1 = 0 ∧ uv.2 ≠ 0)} where
  toFun uv := ⟨uv.1, by
    have h := (adaptive_relation_iff uv.1.1 uv.1.2).1 uv.2
    tauto⟩
  invFun uv := ⟨uv.1, by
    apply (adaptive_relation_iff uv.1.1 uv.1.2).2
    by_cases hu : uv.1.1 = 0
    · right
      by_contra hv
      exact uv.2 ⟨hu, hv⟩
    · exact Or.inl hu⟩
  left_inv _ := rfl
  right_inv _ := rfl

theorem adaptive_relation_card :
    Fintype.card {uv : F × F // ∃ a b : F, b ≠ 0 ∧ a * uv.1 + b * uv.2 = 0} =
      Fintype.card F * Fintype.card F - (Fintype.card F - 1) := by
  rw [Fintype.card_congr successEquiv,
      Fintype.card_subtype_compl (fun uv : F × F => uv.1 = 0 ∧ uv.2 ≠ 0),
      Fintype.card_congr badEquiv, Fintype.card_prod]
  have hnonzero : Fintype.card {v : F // v ≠ 0} = Fintype.card F - 1 := by
    rw [Fintype.card_subtype_compl (fun v : F => v = 0)]
    simp
  rw [hnonzero]

#print axioms adaptive_relation_card

end Finite

#print axioms adaptive_relation_iff
#print axioms adaptive_witness_of_first_ne_zero
#print axioms no_adaptive_witness_when_first_zero_second_nonzero

end XedniAdaptiveCoefficientBoundary
