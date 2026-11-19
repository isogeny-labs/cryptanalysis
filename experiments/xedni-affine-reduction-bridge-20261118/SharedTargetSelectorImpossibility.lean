import SharedTargetSelectorBound
import Mathlib.Tactic

/-! A precommitted coefficient-offset family with fewer than `q-1` pairs
cannot supply an exact selected lift relation for every nonzero target scalar. -/
namespace XedniSharedTargetSelectorImpossibility

variable (q : ℕ) [Fact (Nat.Prime q)]
variable (L : ZMod q × ZMod q → Type*)
variable [∀ uv, AddCommGroup (L uv)] [∀ uv, DecidableEq (L uv)]

/-- If every nonzero target is hit, the coefficient and offset families
must contain at least `q-1` ordered combinations. The selector may depend
arbitrarily on each public pair while preserving its reduction. -/
theorem full_nonzero_coverage_requires_linear_family
    (S : Finset (ℤ × ℤ))
    (hsum : ∀ ab ∈ S, (ab.1 : ZMod q) + (ab.2 : ZMod q) ≠ 0)
    (T : Finset (ZMod q × ZMod q))
    (reduce : ∀ uv, L uv →+ ZMod q)
    (select : ∀ uv, L uv × L uv)
    (hselect : ∀ uv, reduce uv (select uv).1 = uv.1 ∧
      reduce uv (select uv).2 = uv.2)
    (hcover : ∀ w : ZMod q, w ≠ 0 →
      ∃ t ∈ T, ∃ ab ∈ S,
        ab.1 • (select (w - t.1, w - t.2)).1 +
          ab.2 • (select (w - t.1, w - t.2)).2 = 0) :
    q - 1 ≤ T.card * S.card := by
  classical
  let H : Finset (ZMod q) := Finset.univ.filter fun w : ZMod q =>
    w ≠ 0 ∧ ∃ t ∈ T, ∃ ab ∈ S,
      ab.1 • (select (w - t.1, w - t.2)).1 +
        ab.2 • (select (w - t.1, w - t.2)).2 = 0
  have hH : H = Finset.univ.erase (0 : ZMod q) := by
    ext w
    simp only [H, Finset.mem_filter, Finset.mem_univ, true_and,
      Finset.mem_erase]
    constructor
    · intro hw
      exact ⟨hw.1, trivial⟩
    · intro hw
      exact ⟨hw.1, hcover w hw.1⟩
  have hcard : H.card = q - 1 := by
    rw [hH, Finset.card_erase_of_mem (Finset.mem_univ (0 : ZMod q))]
    simp
  have hbound : H.card ≤ T.card * S.card :=
    XedniSharedTargetSelectorBound.precommitted_nonzero_card_bound
      q L S hsum T reduce select hselect
  omega

/-- Below the linear family-size threshold there is a nonzero target with
no exact selected relation among the precommitted coefficients and offsets. -/
theorem exists_nonzero_target_without_selected_relation
    (S : Finset (ℤ × ℤ))
    (hsum : ∀ ab ∈ S, (ab.1 : ZMod q) + (ab.2 : ZMod q) ≠ 0)
    (T : Finset (ZMod q × ZMod q))
    (reduce : ∀ uv, L uv →+ ZMod q)
    (select : ∀ uv, L uv × L uv)
    (hselect : ∀ uv, reduce uv (select uv).1 = uv.1 ∧
      reduce uv (select uv).2 = uv.2)
    (hbudget : T.card * S.card < q - 1) :
    ∃ w : ZMod q, w ≠ 0 ∧
      ¬∃ t ∈ T, ∃ ab ∈ S,
        ab.1 • (select (w - t.1, w - t.2)).1 +
          ab.2 • (select (w - t.1, w - t.2)).2 = 0 := by
  classical
  by_contra hnone
  have hcover : ∀ w : ZMod q, w ≠ 0 →
      ∃ t ∈ T, ∃ ab ∈ S,
        ab.1 • (select (w - t.1, w - t.2)).1 +
          ab.2 • (select (w - t.1, w - t.2)).2 = 0 := by
    intro w hw
    by_contra hmiss
    exact hnone ⟨w, hw, hmiss⟩
  have hlinear := full_nonzero_coverage_requires_linear_family
    q L S hsum T reduce select hselect hcover
  omega

/-- Among nonzero targets, at least `q-1-|T|·|S|` are missed by the
precommitted relation family. The subtraction is truncated in `ℕ`. -/
theorem missed_nonzero_target_count_lower_bound
    (S : Finset (ℤ × ℤ))
    (hsum : ∀ ab ∈ S, (ab.1 : ZMod q) + (ab.2 : ZMod q) ≠ 0)
    (T : Finset (ZMod q × ZMod q))
    (reduce : ∀ uv, L uv →+ ZMod q)
    (select : ∀ uv, L uv × L uv)
    (hselect : ∀ uv, reduce uv (select uv).1 = uv.1 ∧
      reduce uv (select uv).2 = uv.2) :
    q - 1 - T.card * S.card ≤
      ((Finset.univ.erase (0 : ZMod q)) \
        (Finset.univ.filter fun w : ZMod q =>
          w ≠ 0 ∧ ∃ t ∈ T, ∃ ab ∈ S,
            ab.1 • (select (w - t.1, w - t.2)).1 +
              ab.2 • (select (w - t.1, w - t.2)).2 = 0)).card := by
  classical
  let U : Finset (ZMod q) := Finset.univ.erase 0
  let H : Finset (ZMod q) := Finset.univ.filter fun w : ZMod q =>
    w ≠ 0 ∧ ∃ t ∈ T, ∃ ab ∈ S,
      ab.1 • (select (w - t.1, w - t.2)).1 +
        ab.2 • (select (w - t.1, w - t.2)).2 = 0
  have hsub : H ⊆ U := by
    intro w hw
    have hn := (Finset.mem_filter.mp hw).2.1
    simpa [U] using hn
  have hcardU : U.card = q - 1 := by
    simp [U]
  have hbound : H.card ≤ T.card * S.card :=
    XedniSharedTargetSelectorBound.precommitted_nonzero_card_bound
      q L S hsum T reduce select hselect
  have hdiff : (U \ H).card = U.card - H.card :=
    Finset.card_sdiff_of_subset hsub
  change q - 1 - T.card * S.card ≤ (U \ H).card
  omega

#print axioms full_nonzero_coverage_requires_linear_family
#print axioms exists_nonzero_target_without_selected_relation
#print axioms missed_nonzero_target_count_lower_bound

end XedniSharedTargetSelectorImpossibility
