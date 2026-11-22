import UniformRelationBound
import Mathlib.Tactic

/-! A fixed coefficient family bounds exact relations for any public-pair-dependent lift selector. -/
namespace XedniSelectorRelationBound

variable (q : ℕ) [Fact (Nat.Prime q)]
variable (L : ZMod q × ZMod q → Type*)
variable [∀ uv, AddCommGroup (L uv)] [∀ uv, DecidableEq (L uv)]

private def coefficients (ab : ℤ × ℤ) : ZMod q × ZMod q :=
  ((ab.1 : ZMod q), (ab.2 : ZMod q))

/-- An exact selected relation maps to the matching public relation. -/
theorem selected_relation_implies_public
    (reduce : ∀ uv, L uv →+ ZMod q)
    (select : ∀ uv, L uv × L uv)
    (hselect : ∀ uv, reduce uv (select uv).1 = uv.1 ∧ reduce uv (select uv).2 = uv.2)
    (uv : ZMod q × ZMod q) (a b : ℤ)
    (h : a • (select uv).1 + b • (select uv).2 = 0) :
    (a : ZMod q) * uv.1 + (b : ZMod q) * uv.2 = 0 := by
  have hm := congrArg (reduce uv) h
  simpa [map_add, map_zsmul, zsmul_eq_mul, (hselect uv).1,
    (hselect uv).2] using hm

/-- A selector may depend on the public pair, while the coefficient family is
fixed before that pair is sampled. The bound counts successful public pairs. -/
theorem selected_relation_card_bound
    (S : Finset (ℤ × ℤ))
    (hb : ∀ ab ∈ S, (ab.2 : ZMod q) ≠ 0)
    (reduce : ∀ uv, L uv →+ ZMod q)
    (select : ∀ uv, L uv × L uv)
    (hselect : ∀ uv, reduce uv (select uv).1 = uv.1 ∧ reduce uv (select uv).2 = uv.2) :
    (Finset.univ.filter fun uv : ZMod q × ZMod q =>
      ∃ ab ∈ S, ab.1 • (select uv).1 + ab.2 • (select uv).2 = 0).card
      ≤ S.card * q := by
  let T : Finset (ZMod q × ZMod q) := S.image (coefficients q)
  have hT : ∀ ab ∈ T, ab.2 ≠ 0 := by
    intro ab hab
    obtain ⟨cd, hcd, rfl⟩ := Finset.mem_image.mp hab
    exact hb cd hcd
  have hsub :
      (Finset.univ.filter fun uv : ZMod q × ZMod q =>
        ∃ ab ∈ S, ab.1 • (select uv).1 + ab.2 • (select uv).2 = 0) ⊆
      T.biUnion (fun ab => Finset.univ.filter fun uv : ZMod q × ZMod q =>
        ab.1 * uv.1 + ab.2 * uv.2 = 0) := by
    intro uv huv
    rcases Finset.mem_filter.mp huv with ⟨_, cd, hcd, hrel⟩
    apply Finset.mem_biUnion.mpr
    refine ⟨coefficients q cd, Finset.mem_image.mpr ⟨cd, hcd, rfl⟩, ?_⟩
    apply Finset.mem_filter.mpr
    exact ⟨Finset.mem_univ _, selected_relation_implies_public q L reduce select hselect uv cd.1 cd.2 hrel⟩
  calc
    _ ≤ (T.biUnion fun ab => Finset.univ.filter fun uv : ZMod q × ZMod q =>
      ab.1 * uv.1 + ab.2 * uv.2 = 0).card := Finset.card_le_card hsub
    _ ≤ T.card * Fintype.card (ZMod q) :=
      XedniUniformRelationBound.relation_family_card_bound T hT
    _ ≤ S.card * q := by
      simpa using Nat.mul_le_mul_right q (Finset.card_image_le : T.card ≤ S.card)

#print axioms selected_relation_implies_public
#print axioms selected_relation_card_bound

end XedniSelectorRelationBound
