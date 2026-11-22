import SelectorRelationBound
import SharedTargetRelation
import Mathlib.Tactic

/-! A public-pair-dependent lift selector cannot increase the number of
shared-target scalars hit by a fixed relation family and fixed offsets. -/
namespace XedniSharedTargetSelectorBound

variable (q : ℕ) [Fact (Nat.Prime q)]
variable (L : ZMod q × ZMod q → Type*)
variable [∀ uv, AddCommGroup (L uv)] [∀ uv, DecidableEq (L uv)]

private def targetRoot (t₁ t₂ : ZMod q) (ab : ℤ × ℤ) : ZMod q :=
  ((ab.1 : ZMod q) * t₁ + (ab.2 : ZMod q) * t₂) /
    ((ab.1 : ZMod q) + (ab.2 : ZMod q))

/-- For one fixed offset pair, each precommitted coefficient vector with
nonzero sum accounts for at most one shared-target scalar, even when the
rational lift selector depends on the public pair. -/
theorem selected_shared_target_card_bound
    (S : Finset (ℤ × ℤ))
    (hsum : ∀ ab ∈ S, (ab.1 : ZMod q) + (ab.2 : ZMod q) ≠ 0)
    (t₁ t₂ : ZMod q)
    (reduce : ∀ uv, L uv →+ ZMod q)
    (select : ∀ uv, L uv × L uv)
    (hselect : ∀ uv, reduce uv (select uv).1 = uv.1 ∧
      reduce uv (select uv).2 = uv.2) :
    (Finset.univ.filter fun w : ZMod q =>
      ∃ ab ∈ S, ab.1 • (select (w - t₁, w - t₂)).1 +
        ab.2 • (select (w - t₁, w - t₂)).2 = 0).card ≤ S.card := by
  classical
  have hsub :
      (Finset.univ.filter fun w : ZMod q =>
        ∃ ab ∈ S, ab.1 • (select (w - t₁, w - t₂)).1 +
          ab.2 • (select (w - t₁, w - t₂)).2 = 0) ⊆
        S.image (targetRoot q t₁ t₂) := by
    intro w hw
    rcases Finset.mem_filter.mp hw with ⟨_, ab, hab, hrel⟩
    have hpub := XedniSelectorRelationBound.selected_relation_implies_public
      q L reduce select hselect (w - t₁, w - t₂) ab.1 ab.2 hrel
    have heq := (XedniSharedTargetRelation.relation_iff_linear_equation
      (ab.1 : ZMod q) (ab.2 : ZMod q) t₁ t₂ w).mp hpub
    have hroot : w = targetRoot q t₁ t₂ ab := by
      unfold targetRoot
      apply (eq_div_iff (hsum ab hab)).2
      simpa only [mul_comm] using heq
    exact Finset.mem_image.mpr ⟨ab, hab, hroot.symm⟩
  exact (Finset.card_le_card hsub).trans Finset.card_image_le

/-- Across precommitted offset pairs, a fixed coefficient family accounts
for at most the product of the two family sizes among target scalars. -/
theorem precommitted_offsets_card_bound
    (S : Finset (ℤ × ℤ))
    (hsum : ∀ ab ∈ S, (ab.1 : ZMod q) + (ab.2 : ZMod q) ≠ 0)
    (T : Finset (ZMod q × ZMod q))
    (reduce : ∀ uv, L uv →+ ZMod q)
    (select : ∀ uv, L uv × L uv)
    (hselect : ∀ uv, reduce uv (select uv).1 = uv.1 ∧
      reduce uv (select uv).2 = uv.2) :
    (Finset.univ.filter fun w : ZMod q =>
      ∃ t ∈ T, ∃ ab ∈ S,
        ab.1 • (select (w - t.1, w - t.2)).1 +
          ab.2 • (select (w - t.1, w - t.2)).2 = 0).card
      ≤ T.card * S.card := by
  classical
  have hsub :
      (Finset.univ.filter fun w : ZMod q =>
        ∃ t ∈ T, ∃ ab ∈ S,
          ab.1 • (select (w - t.1, w - t.2)).1 +
            ab.2 • (select (w - t.1, w - t.2)).2 = 0) ⊆
        T.biUnion (fun t => Finset.univ.filter fun w : ZMod q =>
          ∃ ab ∈ S,
            ab.1 • (select (w - t.1, w - t.2)).1 +
              ab.2 • (select (w - t.1, w - t.2)).2 = 0) := by
    intro w hw
    rcases Finset.mem_filter.mp hw with ⟨_, t, ht, ab, hab, hrel⟩
    apply Finset.mem_biUnion.mpr
    exact ⟨t, ht, Finset.mem_filter.mpr ⟨Finset.mem_univ _, ⟨ab, hab, hrel⟩⟩⟩
  calc
    _ ≤ (T.biUnion (fun t => Finset.univ.filter fun w : ZMod q =>
          ∃ ab ∈ S,
            ab.1 • (select (w - t.1, w - t.2)).1 +
              ab.2 • (select (w - t.1, w - t.2)).2 = 0)).card :=
        Finset.card_le_card hsub
    _ ≤ ∑ t ∈ T, (Finset.univ.filter fun w : ZMod q =>
          ∃ ab ∈ S,
            ab.1 • (select (w - t.1, w - t.2)).1 +
              ab.2 • (select (w - t.1, w - t.2)).2 = 0).card :=
        Finset.card_biUnion_le
    _ ≤ ∑ _t ∈ T, S.card := by
      apply Finset.sum_le_sum
      intro t ht
      exact selected_shared_target_card_bound q L S hsum t.1 t.2 reduce select hselect
    _ = T.card * S.card := by simp

/-- Restricting to nonzero public targets preserves the capacity bound. -/
theorem precommitted_nonzero_card_bound
    (S : Finset (ℤ × ℤ))
    (hsum : ∀ ab ∈ S, (ab.1 : ZMod q) + (ab.2 : ZMod q) ≠ 0)
    (T : Finset (ZMod q × ZMod q))
    (reduce : ∀ uv, L uv →+ ZMod q)
    (select : ∀ uv, L uv × L uv)
    (hselect : ∀ uv, reduce uv (select uv).1 = uv.1 ∧
      reduce uv (select uv).2 = uv.2) :
    (Finset.univ.filter fun w : ZMod q => w ≠ 0 ∧
      ∃ t ∈ T, ∃ ab ∈ S,
        ab.1 • (select (w - t.1, w - t.2)).1 +
          ab.2 • (select (w - t.1, w - t.2)).2 = 0).card
      ≤ T.card * S.card := by
  classical
  have hsub :
      (Finset.univ.filter fun w : ZMod q => w ≠ 0 ∧
        ∃ t ∈ T, ∃ ab ∈ S,
          ab.1 • (select (w - t.1, w - t.2)).1 +
            ab.2 • (select (w - t.1, w - t.2)).2 = 0) ⊆
      (Finset.univ.filter fun w : ZMod q =>
        ∃ t ∈ T, ∃ ab ∈ S,
          ab.1 • (select (w - t.1, w - t.2)).1 +
            ab.2 • (select (w - t.1, w - t.2)).2 = 0) := by
    intro w hw
    exact Finset.mem_filter.mpr ⟨Finset.mem_univ _, (Finset.mem_filter.mp hw).2.2⟩
  exact (Finset.card_le_card hsub).trans
    (precommitted_offsets_card_bound q L S hsum T reduce select hselect)

#print axioms selected_shared_target_card_bound
#print axioms precommitted_offsets_card_bound
#print axioms precommitted_nonzero_card_bound

end XedniSharedTargetSelectorBound
