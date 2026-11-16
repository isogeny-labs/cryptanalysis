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

#print axioms family_event_count

end XedniPublicFirstLargeHoldout
