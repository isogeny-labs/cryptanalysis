import Mathlib

namespace XedniChordOrigin

/-- Translating the identity to `O` translates every point class by `-O`. -/
theorem shifted_relation_identity {ι A : Type*} [AddCommGroup A]
    (s : Finset ι) (c : ι → ℤ) (point : ι → A) (origin : A) :
    (∑ i ∈ s, c i • (point i - origin)) =
      (∑ i ∈ s, c i • point i) - (∑ i ∈ s, c i) • origin := by
  simp only [smul_sub, Finset.sum_sub_distrib, Finset.sum_smul]

/-- If the origin is the third chord point through `m_j G,m_k G`, its source
    scalar is `-(m_j+m_k)` and every shifted point has scalar
    `m_i+m_j+m_k`. -/
theorem chord_origin_scalar_identity {ι A : Type*} [AddCommGroup A]
    (s : Finset ι) (c m : ι → ℤ) (j k : ι) (G : A) :
    (∑ i ∈ s, c i • (m i • G - (-(m j + m k)) • G)) =
      (∑ i ∈ s, c i * (m i + m j + m k)) • G := by
  calc
    (∑ i ∈ s, c i • (m i • G - (-(m j + m k)) • G)) =
        ∑ i ∈ s, (c i * (m i + m j + m k)) • G := by
      apply Finset.sum_congr rfl
      intro i hi
      simp only [mul_zsmul, neg_zsmul, sub_neg_eq_add, add_zsmul]
      abel
    _ = (∑ i ∈ s, c i * (m i + m j + m k)) • G := by
      rw [← Finset.sum_smul]

/-- The shifted scalar equation isolates the one unknown multiplier. -/
theorem shifted_target_linear {R : Type*} [CommRing R]
    (coefficient target known origin : R) :
    coefficient * (target - origin) + known = 0 ↔
      coefficient * target = coefficient * origin - known := by
  constructor <;> intro h <;> linear_combination h

/-- An invertible target coefficient recovers the unknown source multiplier. -/
theorem shifted_target_recovers {F : Type*} [Field F]
    (coefficient target known origin : F) (h : coefficient ≠ 0) :
    coefficient * (target - origin) + known = 0 ↔
      target = origin - known / coefficient := by
  rw [shifted_target_linear]
  constructor
  · intro equation
    field_simp [h]
    linear_combination equation
  · intro equation
    field_simp [h] at equation
    linear_combination equation

#print axioms shifted_relation_identity
#print axioms chord_origin_scalar_identity
#print axioms shifted_target_linear
#print axioms shifted_target_recovers

end XedniChordOrigin
