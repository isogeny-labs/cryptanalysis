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

#print axioms admissible_pair_count
#print axioms family_density_cross_mul

end XedniPublicFirstLargeHoldout
