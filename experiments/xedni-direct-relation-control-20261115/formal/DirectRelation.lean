import Mathlib

namespace XedniDirectRelation

/-- The fixed two-point relation is exactly the public scalar equation. -/
theorem relation_iff_linear {R : Type*} [CommRing R] (w t₁ t₂ : R) :
    (w - t₁) + 2 * (w - t₂) = 0 ↔ 3 * w = t₁ + 2 * t₂ := by
  constructor
  · intro h
    linear_combination h
  · intro h
    linear_combination h

/-- In characteristic other than three, the first reduced relation recovers the scalar. -/
theorem relation_iff_recovery {F : Type*} [Field F]
    (w t₁ t₂ : F) (h₃ : (3 : F) ≠ 0) :
    (w - t₁) + 2 * (w - t₂) = 0 ↔ w = (t₁ + 2 * t₂) / 3 := by
  rw [relation_iff_linear]
  constructor
  · intro h
    apply (eq_div_iff h₃).2
    simpa only [mul_comm] using h
  · intro h
    have hh := (eq_div_iff h₃).1 h
    simpa only [mul_comm] using hh

/-- Substituting the public point and query offsets makes the group event explicit. -/
theorem group_relation_iff {A : Type*} [AddCommGroup A]
    (G : A) (w t₁ t₂ : ℤ) :
    ((w • G - t₁ • G) + (2 : ℤ) • (w • G - t₂ • G) = 0) ↔
      ((3 * w - t₁ - 2 * t₂) • G = 0) := by
  have heq : (w • G - t₁ • G) + (2 : ℤ) • (w • G - t₂ • G) =
      (3 * w - t₁ - 2 * t₂) • G := by
    simp only [sub_zsmul, mul_zsmul]
    abel
  rw [heq]

/-- An additive reduction map carries a rational-lift relation to its public group relation. -/
theorem relation_reduces {H A : Type*} [AddCommGroup H] [AddCommGroup A]
    (ρ : H →+ A) (L₁ L₂ : H)
    (h : L₁ + (2 : ℤ) • L₂ = 0) :
    ρ L₁ + (2 : ℤ) • ρ L₂ = 0 := by
  have hρ := congrArg ρ h
  simpa using hρ

/-- Every finite coefficient vector exposes its scalar dependence through its sum. -/
theorem finite_relation_iff {ι R : Type*} [CommRing R]
    (s : Finset ι) (c t : ι → R) (w : R) :
    (∑ i ∈ s, c i * (w - t i)) = 0 ↔
      (∑ i ∈ s, c i) * w = ∑ i ∈ s, c i * t i := by
  simp only [mul_sub, Finset.sum_sub_distrib, Finset.sum_mul, sub_eq_zero]

/-- A nonzero coefficient sum makes the reduced relation solve for the scalar. -/
theorem finite_relation_recovers {ι F : Type*} [Field F]
    (s : Finset ι) (c t : ι → F) (w : F)
    (hC : (∑ i ∈ s, c i) ≠ 0) :
    (∑ i ∈ s, c i * (w - t i)) = 0 ↔
      w = (∑ i ∈ s, c i * t i) / (∑ i ∈ s, c i) := by
  rw [finite_relation_iff]
  constructor
  · intro h
    apply (eq_div_iff hC).2
    simpa only [mul_comm] using h
  · intro h
    have hh := (eq_div_iff hC).1 h
    simpa only [mul_comm] using hh

/-- With zero coefficient sum, the reduced equation contains no target scalar. -/
theorem finite_zero_sum_relation {ι R : Type*} [CommRing R]
    (s : Finset ι) (c t : ι → R) (w : R)
    (hC : (∑ i ∈ s, c i) = 0) :
    (∑ i ∈ s, c i * (w - t i)) = 0 ↔
      (∑ i ∈ s, c i * t i) = 0 := by
  rw [finite_relation_iff, hC, zero_mul, eq_comm]

/-- The public-group identity for any finite integer coefficient vector. -/
theorem finite_group_identity {ι A : Type*} [AddCommGroup A]
    (s : Finset ι) (c t : ι → ℤ) (w : ℤ) (G : A) :
    (∑ i ∈ s, c i • (w • G - t i • G)) =
      ((∑ i ∈ s, c i) * w - ∑ i ∈ s, c i * t i) • G := by
  calc
    (∑ i ∈ s, c i • (w • G - t i • G)) =
        ∑ i ∈ s, (c i * w - c i * t i) • G := by
      apply Finset.sum_congr rfl
      intro i hi
      simp only [smul_sub, mul_zsmul, sub_zsmul]
      abel
    _ = (∑ i ∈ s, (c i * w - c i * t i)) • G := by
      rw [← Finset.sum_smul]
    _ = ((∑ i ∈ s, c i) * w - ∑ i ∈ s, c i * t i) • G := by
      simp only [Finset.sum_sub_distrib, Finset.sum_mul]

#print axioms relation_iff_linear
#print axioms relation_iff_recovery
#print axioms group_relation_iff
#print axioms relation_reduces
#print axioms finite_relation_iff
#print axioms finite_relation_recovers
#print axioms finite_zero_sum_relation
#print axioms finite_group_identity

end XedniDirectRelation
