import FamilyBound

namespace XedniPublicFirstLargeHoldout

/-- Integer coefficients from `-H` through `H`, including endpoints. -/
def CoeffBox (H : ℕ) := Set.Icc (-(H : ℤ)) (H : ℤ)

noncomputable instance coeffBoxFintype (H : ℕ) : Fintype (CoeffBox H) := by
  unfold CoeffBox
  infer_instance

theorem coeff_box_card (H : ℕ) : Fintype.card (CoeffBox H) = 2 * H + 1 := by
  have h := Int.card_fintype_Icc_of_le
    (a := -(H : ℤ)) (b := (H : ℤ)) (by omega)
  change (Fintype.card (CoeffBox H) : ℤ) = _ at h
  have h' : (Fintype.card (CoeffBox H) : ℤ) = (2 * H + 1 : ℕ) := by
    convert h using 1 <;> norm_num <;> ring
  exact_mod_cast h'

/-- All valid modular coefficient pairs represented in the integer box. -/
def BoundedVector (F : Type*) [Field F] (H : ℕ) :=
  {ab : CoeffBox H × CoeffBox H //
    (ab.1.val : F) ≠ 0 ∧ (ab.2.val : F) ≠ 0 ∧
      (ab.1.val : F) + (ab.2.val : F) ≠ 0}

noncomputable instance boundedVectorFintype (F : Type*) [Field F]
    (H : ℕ) : Fintype (BoundedVector F H) := by
  classical
  unfold BoundedVector
  infer_instance

def boundedVectorMap (F : Type*) [Field F] (H : ℕ) :
    BoundedVector F H → F × F :=
  fun ab => ((ab.val.1.val : F), (ab.val.2.val : F))

theorem bounded_vector_card_le (F : Type*) [Field F] (H : ℕ) :
    Fintype.card (BoundedVector F H) ≤ (2 * H + 1) ^ 2 := by
  classical
  calc
    Fintype.card (BoundedVector F H) ≤
        Fintype.card (CoeffBox H × CoeffBox H) := by
      unfold BoundedVector
      exact Fintype.card_subtype_le _
    _ = (2 * H + 1) ^ 2 := by
      rw [Fintype.card_prod, coeff_box_card, pow_two]

theorem bounded_vector_fraction_le (F : Type*) [Field F]
    [Fintype F] (H : ℕ) (w : F) (hq : 3 ≤ Fintype.card F) :
    (Fintype.card (FamilyHitPair (boundedVectorMap F H) w) : ℚ) /
        (Fintype.card (AdmissiblePair F w) : ℚ) ≤
      ((2 * H + 1) ^ 2 : ℕ) / (Fintype.card F - 2 : ℕ) := by
  have ha : ∀ i : BoundedVector F H, (boundedVectorMap F H i).1 ≠ 0 :=
    fun i => i.property.1
  have hb : ∀ i : BoundedVector F H, (boundedVectorMap F H i).2 ≠ 0 :=
    fun i => i.property.2.1
  have hs : ∀ i : BoundedVector F H,
      (boundedVectorMap F H i).1 + (boundedVectorMap F H i).2 ≠ 0 :=
    fun i => i.property.2.2
  have hbase := family_fraction_le (boundedVectorMap F H) w hq ha hb hs
  have hden : (0 : ℚ) < (Fintype.card F - 2 : ℕ) := by
    exact_mod_cast (show 0 < Fintype.card F - 2 by omega)
  exact le_trans hbase <|
    (div_le_div_iff₀ hden hden).2 (by
      exact_mod_cast Nat.mul_le_mul_right (Fintype.card F - 2)
        (bounded_vector_card_le F H))

/-- To achieve uniform one-query hit fraction at least `δ` using every
valid coefficient pair in `[-H,H]²`, the box must satisfy this quadratic
height budget. -/
theorem coefficient_height_needed (F : Type*) [Field F]
    [Fintype F] (H : ℕ) (w : F) (hq : 3 ≤ Fintype.card F)
    (δ : ℚ)
    (hδ : δ ≤
      (Fintype.card (FamilyHitPair (boundedVectorMap F H) w) : ℚ) /
        (Fintype.card (AdmissiblePair F w) : ℚ)) :
    δ * (Fintype.card F - 2 : ℕ) ≤ (((2 * H + 1) ^ 2 : ℕ) : ℚ) := by
  have hpos : (0 : ℚ) < (Fintype.card F - 2 : ℕ) := by
    exact_mod_cast (show 0 < Fintype.card F - 2 by omega)
  exact (le_div_iff₀ hpos).mp
    (le_trans hδ (bounded_vector_fraction_le F H w hq))

#print axioms coeff_box_card
#print axioms bounded_vector_card_le
#print axioms bounded_vector_fraction_le
#print axioms coefficient_height_needed

end XedniPublicFirstLargeHoldout
