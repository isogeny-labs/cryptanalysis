import Panel

namespace XedniPublicFirstLargeHoldout

/-- Ordered offset pairs with two nonidentity, distinct queried points. -/
def AdmissiblePair (F : Type*) [Field F] (w : F) :=
  {z : F × F // z.1 ≠ w ∧ z.2 ≠ w ∧ z.1 ≠ z.2}

noncomputable instance admissiblePairFintype (F : Type*) [Field F]
    [Fintype F] (w : F) : Fintype (AdmissiblePair F w) := by
  classical
  unfold AdmissiblePair
  infer_instance

/-- The query population has `(q−1)(q−2)` ordered pairs over a field of
cardinality `q`. -/
theorem admissible_pair_count (F : Type*) [Field F] [Fintype F] (w : F) :
    Fintype.card (AdmissiblePair F w) =
      (Fintype.card F - 1) * (Fintype.card F - 2) := by
  classical
  let s : Finset F := Finset.univ.erase w
  have hs : s.card = Fintype.card F - 1 := by simp [s]
  have hcard : Fintype.card (AdmissiblePair F w) = (Finset.offDiag s).card := by
    change Fintype.card {z : F × F // z.1 ≠ w ∧ z.2 ≠ w ∧ z.1 ≠ z.2} = _
    rw [Fintype.card_subtype]
    congr 1
    ext z
    simp [AdmissiblePair, s, Finset.mem_offDiag]
  rw [hcard, Finset.offDiag_card, hs]
  rw [← Nat.mul_sub_one, Nat.sub_sub]

/-- Integer cross product for the exact distinct-hit fraction. This keeps
the denominator visible without an implicit probability model. -/
theorem family_density_cross_mul {F ι : Type*} [Field F]
    [Fintype F] [Fintype ι] (v : ι → F × F) (w : F)
    (ha : ∀ i, (v i).1 ≠ 0) (hb : ∀ i, (v i).2 ≠ 0)
    (hs : ∀ i, (v i).1 + (v i).2 ≠ 0)
    (hd : ∀ i j, i ≠ j → (v i).1 * (v j).2 - (v i).2 * (v j).1 ≠ 0) :
    Fintype.card (FamilyHitPair v w) * (Fintype.card F - 2) =
      Fintype.card ι * Fintype.card (AdmissiblePair F w) := by
  rw [family_hit_pair_count v w ha hb hs hd, admissible_pair_count]
  ring

/-- Exact hit fraction when an admissible ordered offset pair is selected
uniformly. The field must contain at least three elements so the denominator
is positive. -/
theorem family_exact_fraction {F ι : Type*} [Field F]
    [Fintype F] [Fintype ι] (v : ι → F × F) (w : F)
    (hq : 3 ≤ Fintype.card F)
    (ha : ∀ i, (v i).1 ≠ 0) (hb : ∀ i, (v i).2 ≠ 0)
    (hs : ∀ i, (v i).1 + (v i).2 ≠ 0)
    (hd : ∀ i j, i ≠ j → (v i).1 * (v j).2 - (v i).2 * (v j).1 ≠ 0) :
    (Fintype.card (FamilyHitPair v w) : ℚ) /
        (Fintype.card (AdmissiblePair F w) : ℚ) =
      (Fintype.card ι : ℚ) / (Fintype.card F - 2 : ℕ) := by
  have hden : Fintype.card F - 2 ≠ 0 := by omega
  have hnum : Fintype.card F - 1 ≠ 0 := by omega
  have hspace : Fintype.card (AdmissiblePair F w) ≠ 0 := by
    rw [admissible_pair_count]
    exact mul_ne_zero hnum hden
  apply (div_eq_div_iff (by exact_mod_cast hspace) (by exact_mod_cast hden)).2
  exact_mod_cast family_density_cross_mul v w ha hb hs hd

/-- A fixed-size coefficient family has at most `|family|/N` exact hit
fraction whenever the field cardinality is at least `N+2`. -/
theorem family_fraction_bound {F ι : Type*} [Field F]
    [Fintype F] [Fintype ι] (v : ι → F × F) (w : F)
    (hq : 3 ≤ Fintype.card F)
    (ha : ∀ i, (v i).1 ≠ 0) (hb : ∀ i, (v i).2 ≠ 0)
    (hs : ∀ i, (v i).1 + (v i).2 ≠ 0)
    (hd : ∀ i j, i ≠ j → (v i).1 * (v j).2 - (v i).2 * (v j).1 ≠ 0)
    (N : ℕ) (hN : 0 < N) (hlarge : N ≤ Fintype.card F - 2) :
    (Fintype.card (FamilyHitPair v w) : ℚ) /
        (Fintype.card (AdmissiblePair F w) : ℚ) ≤
      (Fintype.card ι : ℚ) / N := by
  rw [family_exact_fraction v w hq ha hb hs hd]
  exact div_le_div_of_nonneg_left (by positivity)
    (by exact_mod_cast hN) (by exact_mod_cast hlarge)

#print axioms admissible_pair_count
#print axioms family_density_cross_mul
#print axioms family_exact_fraction
#print axioms family_fraction_bound

end XedniPublicFirstLargeHoldout
