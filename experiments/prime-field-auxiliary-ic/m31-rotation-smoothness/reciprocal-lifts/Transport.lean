import Mathlib.Tactic.FieldSimp
import Mathlib.Tactic.Ring

namespace ReciprocalLifts

/-- Inversion transports affine lifts on y² = x³ + x. -/
theorem transport {K : Type*} [Field K] (x y : K) (hx : x ≠ 0)
    (hy : y^2 = x^3 + x) : (y / x^2)^2 = (x⁻¹)^3 + x⁻¹ := by
  rw [div_pow, hy]
  field_simp
  ring

theorem lift_iff {K : Type*} [Field K] (x : K) (hx : x ≠ 0) :
    (∃ y : K, y^2 = x^3 + x) ↔ (∃ z : K, z^2 = (x⁻¹)^3 + x⁻¹) := by
  constructor
  · rintro ⟨y,hy⟩
    exact ⟨_, transport x y hx hy⟩
  · rintro ⟨z,hz⟩
    exact ⟨_, by simpa using transport x⁻¹ z (inv_ne_zero hx) hz⟩

end ReciprocalLifts
