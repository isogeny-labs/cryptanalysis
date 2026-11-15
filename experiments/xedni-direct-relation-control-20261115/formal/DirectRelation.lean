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

#print axioms relation_iff_linear
#print axioms relation_iff_recovery
#print axioms group_relation_iff
#print axioms relation_reduces

end XedniDirectRelation
