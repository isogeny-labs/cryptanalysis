import Mathlib.Tactic.FieldSimp
import Mathlib.Tactic.Ring

namespace ReciprocalLifts

/-- Clearing the inverse cubic with the square x^4 preserves affine lifts,
including zero right-hand sides. The parameter b covers both twist signs. -/
theorem inverse_cubic_lift {K : Type*} [Field K] (x a b : K) (hx : x ≠ 0) :
    (∃ y : K, y^2 = (x⁻¹)^3 + a*x⁻¹ + b) ↔
    (∃ z : K, z^2 = x + a*x^3 + b*x^4) := by
  constructor
  · rintro ⟨y, hy⟩
    refine ⟨y*x^2, ?_⟩
    rw [mul_pow, hy]
    field_simp
  · rintro ⟨z, hz⟩
    refine ⟨z/x^2, ?_⟩
    rw [div_pow, hz]
    field_simp

end ReciprocalLifts

#print axioms ReciprocalLifts.inverse_cubic_lift
