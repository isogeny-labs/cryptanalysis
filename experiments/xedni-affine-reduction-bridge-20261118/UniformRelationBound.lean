import AllSignedPublicRelations
import Mathlib.Tactic

/-!
Counting a fixed linear relation under independent uniform inputs.
The statement is conditional on a finite field and a nonzero second coefficient;
it does not assert any distributional property of a lift algorithm.
-/
namespace XedniUniformRelationBound

variable {F : Type*} [Field F] [Fintype F] [DecidableEq F]

private def partner (a b u : F) : F := -(a * u) / b

private theorem partner_relation (a b u : F) (hb : b ≠ 0) :
    a * u + b * partner a b u = 0 := by
  unfold partner
  field_simp [hb]
  ring

private theorem partner_unique (a b u v : F) (hb : b ≠ 0)
    (h : a * u + b * v = 0) : v = partner a b u := by
  have hv : b * v = -(a * u) := by linear_combination h
  have hp : b * partner a b u = -(a * u) := by
    unfold partner
    field_simp [hb]
  exact (mul_left_cancel₀ hb) (hv.trans hp.symm)

theorem unique_partner (a b u : F) (hb : b ≠ 0) :
    ∃! v : F, a * u + b * v = 0 := by
  refine ⟨partner a b u, partner_relation a b u hb, ?_⟩
  intro v hv
  exact partner_unique a b u v hb hv

noncomputable def relationEquiv (a b : F) (hb : b ≠ 0) :
    F ≃ {uv : F × F // a * uv.1 + b * uv.2 = 0} where
  toFun u := ⟨(u, partner a b u), partner_relation a b u hb⟩
  invFun uv := uv.1.1
  left_inv _ := rfl
  right_inv uv := by
    apply Subtype.ext
    apply Prod.ext
    · rfl
    · exact (partner_unique a b uv.1.1 uv.1.2 hb uv.2).symm

theorem relation_card (a b : F) (hb : b ≠ 0) :
    Fintype.card {uv : F × F // a * uv.1 + b * uv.2 = 0} = Fintype.card F := by
  exact Fintype.card_congr (relationEquiv a b hb).symm

/-- Under an independent uniform draw of an ordered pair, the exact fraction
satisfying one fixed nondegenerate relation is `1 / |F|`. -/
theorem relation_fraction (a b : F) (hb : b ≠ 0) :
    (Fintype.card {uv : F × F // a * uv.1 + b * uv.2 = 0} : ℚ) /
      (Fintype.card (F × F) : ℚ) = 1 / (Fintype.card F : ℚ) := by
  rw [relation_card a b hb, Fintype.card_prod]
  have hn : (Fintype.card F : ℚ) ≠ 0 := by
    exact_mod_cast Fintype.card_ne_zero
  field_simp
  norm_num [Nat.cast_mul]
  ring

theorem prime_field_relation_fraction (q : ℕ) [Fact (Nat.Prime q)]
    (a b : ZMod q) (hb : b ≠ 0) :
    (Fintype.card {uv : ZMod q × ZMod q // a * uv.1 + b * uv.2 = 0} : ℚ) /
      (Fintype.card (ZMod q × ZMod q) : ℚ) = 1 / (q : ℚ) := by
  simpa using relation_fraction a b hb

/-- A fixed family of coefficient pairs covers at most its size times the
field size among all ordered input pairs. The family is chosen independently
of the sampled input pair. -/
theorem relation_family_card_bound (S : Finset (F × F))
    (hb : ∀ ab ∈ S, ab.2 ≠ 0) :
    (S.biUnion fun ab =>
      (Finset.univ.filter fun uv : F × F => ab.1 * uv.1 + ab.2 * uv.2 = 0)).card
      ≤ S.card * Fintype.card F := by
  apply Finset.card_biUnion_le_card_mul
  intro ab hab
  rw [← Fintype.card_subtype]
  exact (relation_card ab.1 ab.2 (hb ab hab)).le

#print axioms unique_partner
#print axioms relationEquiv
#print axioms relation_card
#print axioms relation_fraction
#print axioms prime_field_relation_fraction
#print axioms relation_family_card_bound

end XedniUniformRelationBound
