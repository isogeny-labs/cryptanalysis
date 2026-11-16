import CoefficientFamily

namespace XedniPublicFirstLargeHoldout

open XedniCoefficientFamily

/-- The relation events for an indexed coefficient family retain their vector
index, even before proving that different vectors have disjoint hit sets. -/
def FamilyEvent {F ι : Type*} [Field F] (v : ι → F × F) (w : F) :=
  (i : ι) × AdmissibleHit (v i).1 (v i).2 w

noncomputable instance familyEventFintype {F ι : Type*} [Field F]
    [Fintype F] [Fintype ι] (v : ι → F × F) (w : F) :
    Fintype (FamilyEvent v w) := by
  unfold FamilyEvent
  infer_instance

/-- If every coefficient pair is nonzero with nonzero sum, the exact number
of indexed relation events is the family size times the line size. -/
theorem family_event_count {F ι : Type*} [Field F] [Fintype F]
    [Fintype ι] (v : ι → F × F) (w : F)
    (ha : ∀ i, (v i).1 ≠ 0) (hb : ∀ i, (v i).2 ≠ 0)
    (hs : ∀ i, (v i).1 + (v i).2 ≠ 0) :
    Fintype.card (FamilyEvent v w) = Fintype.card ι * (Fintype.card F - 1) := by
  classical
  unfold FamilyEvent
  rw [Fintype.card_sigma]
  simp_rw [show ∀ i, Fintype.card (AdmissibleHit (v i).1 (v i).2 w) =
      Fintype.card F - 1 from fun i =>
    admissible_hit_count (v i).1 (v i).2 w (ha i) (hb i) (hs i)]
  simp

/-- Public offset pairs hit by at least one vector in the family. -/
def FamilyHitPair {F ι : Type*} [Field F] (v : ι → F × F) (w : F) :=
  {z : F × F // ∃ e : FamilyEvent v w, e.2.val = z}

noncomputable instance familyHitPairFintype {F ι : Type*} [Field F]
    [Fintype F] [Fintype ι] (v : ι → F × F) (w : F) :
    Fintype (FamilyHitPair v w) := by
  classical
  unfold FamilyHitPair
  infer_instance

def eventToHitPair {F ι : Type*} [Field F] (v : ι → F × F) (w : F)
    (e : FamilyEvent v w) : FamilyHitPair v w := ⟨e.2.val, ⟨e, rfl⟩⟩

/-- Distinct coefficient directions make the public offset-pair map injective. -/
theorem eventToHitPair_injective {F ι : Type*} [Field F]
    (v : ι → F × F) (w : F)
    (hd : ∀ i j, i ≠ j → (v i).1 * (v j).2 - (v i).2 * (v j).1 ≠ 0) :
    Function.Injective (eventToHitPair v w) := by
  intro e e' heq
  have hpair : e.2.val = e'.2.val := congrArg Subtype.val heq
  rcases e with ⟨i, hi⟩
  rcases e' with ⟨j, hj⟩
  by_cases hij : i = j
  · subst j
    have hp : hi = hj := Subtype.ext hpair
    subst hj
    rfl
  · have hrel₂ : (v j).1 * (w - hi.val.1) + (v j).2 * (w - hi.val.2) = 0 := by
      rw [hpair]
      exact hj.property.2.2.2
    have hzero := distinct_directions_force_zero
      (v i).1 (v i).2 (v j).1 (v j).2
      (w - hi.val.1) (w - hi.val.2)
      (hd i j hij) hi.property.2.2.2 hrel₂
    exact False.elim (hi.property.1 (sub_eq_zero.mp hzero.1).symm)

/-- Under nonzero pairwise determinants, indexed events and distinct public
hit pairs have the same exact cardinality. -/
theorem family_hit_pair_count {F ι : Type*} [Field F] [Fintype F]
    [Fintype ι] (v : ι → F × F) (w : F)
    (ha : ∀ i, (v i).1 ≠ 0) (hb : ∀ i, (v i).2 ≠ 0)
    (hs : ∀ i, (v i).1 + (v i).2 ≠ 0)
    (hd : ∀ i j, i ≠ j → (v i).1 * (v j).2 - (v i).2 * (v j).1 ≠ 0) :
    Fintype.card (FamilyHitPair v w) = Fintype.card ι * (Fintype.card F - 1) := by
  classical
  have hsurj : Function.Surjective (eventToHitPair v w) := by
    rintro ⟨z, e, he⟩
    exact ⟨e, Subtype.ext he⟩
  let equiv := Equiv.ofBijective (eventToHitPair v w)
    ⟨eventToHitPair_injective v w hd, hsurj⟩
  rw [← Fintype.card_congr equiv]
  exact family_event_count v w ha hb hs

#print axioms family_event_count
#print axioms eventToHitPair_injective
#print axioms family_hit_pair_count

end XedniPublicFirstLargeHoldout
