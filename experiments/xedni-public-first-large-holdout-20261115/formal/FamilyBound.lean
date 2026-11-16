import AdmissiblePairs

namespace XedniPublicFirstLargeHoldout

/-- Allow repeated or overlapping coefficient directions: the number of
distinct public hit pairs is at most the number of indexed events. -/
theorem family_hit_card_le {F ι : Type*} [Field F]
    [Fintype F] [Fintype ι] (v : ι → F × F) (w : F)
    (ha : ∀ i, (v i).1 ≠ 0) (hb : ∀ i, (v i).2 ≠ 0)
    (hs : ∀ i, (v i).1 + (v i).2 ≠ 0) :
    Fintype.card (FamilyHitPair v w) ≤
      Fintype.card ι * (Fintype.card F - 1) := by
  classical
  have hsurj : Function.Surjective (eventToHitPair v w) := by
    rintro ⟨z, e, he⟩
    exact ⟨e, Subtype.ext he⟩
  calc
    Fintype.card (FamilyHitPair v w) ≤ Fintype.card (FamilyEvent v w) :=
      Fintype.card_le_of_surjective (eventToHitPair v w) hsurj
    _ = Fintype.card ι * (Fintype.card F - 1) :=
      family_event_count v w ha hb hs

/-- Uniform admissible-pair hit fraction is bounded by the number of
coefficient vectors divided by `q−2`, even with overlapping directions. -/
theorem family_fraction_le {F ι : Type*} [Field F]
    [Fintype F] [Fintype ι] (v : ι → F × F) (w : F)
    (hq : 3 ≤ Fintype.card F)
    (ha : ∀ i, (v i).1 ≠ 0) (hb : ∀ i, (v i).2 ≠ 0)
    (hs : ∀ i, (v i).1 + (v i).2 ≠ 0) :
    (Fintype.card (FamilyHitPair v w) : ℚ) /
        (Fintype.card (AdmissiblePair F w) : ℚ) ≤
      (Fintype.card ι : ℚ) / (Fintype.card F - 2 : ℕ) := by
  have hden : 0 < Fintype.card F - 2 := by omega
  have hspace : 0 < Fintype.card (AdmissiblePair F w) := by
    rw [admissible_pair_count]
    exact Nat.mul_pos (by omega) hden
  apply (div_le_div_iff₀ (by exact_mod_cast hspace) (by exact_mod_cast hden)).2
  have hcard := family_hit_card_le v w ha hb hs
  rw [admissible_pair_count]
  have hmul := Nat.mul_le_mul_right (Fintype.card F - 2) hcard
  have hnat :
      Fintype.card (FamilyHitPair v w) * (Fintype.card F - 2) ≤
        Fintype.card ι * ((Fintype.card F - 1) * (Fintype.card F - 2)) := by
    calc
      _ ≤ (Fintype.card ι * (Fintype.card F - 1)) *
          (Fintype.card F - 2) := hmul
      _ = _ := by ring
  exact_mod_cast hnat

/-- A desired one-query hit fraction `δ` requires at least `δ(q−2)`
indexed coefficient vectors, regardless of overlap among their directions. -/
theorem family_size_needed {F ι : Type*} [Field F]
    [Fintype F] [Fintype ι] (v : ι → F × F) (w : F)
    (hq : 3 ≤ Fintype.card F)
    (ha : ∀ i, (v i).1 ≠ 0) (hb : ∀ i, (v i).2 ≠ 0)
    (hs : ∀ i, (v i).1 + (v i).2 ≠ 0)
    (δ : ℚ)
    (hδ : δ ≤ (Fintype.card (FamilyHitPair v w) : ℚ) /
      (Fintype.card (AdmissiblePair F w) : ℚ)) :
    δ * (Fintype.card F - 2 : ℕ) ≤ (Fintype.card ι : ℚ) := by
  have hpos : (0 : ℚ) < (Fintype.card F - 2 : ℕ) := by
    exact_mod_cast (show 0 < Fintype.card F - 2 by omega)
  exact (le_div_iff₀ hpos).mp
    (le_trans hδ (family_fraction_le v w hq ha hb hs))

#print axioms family_hit_card_le
#print axioms family_fraction_le
#print axioms family_size_needed

end XedniPublicFirstLargeHoldout
