import Mathlib.Algebra.Field.Defs
import Mathlib.Tactic.Ring
import Mathlib.Tactic.FieldSimp

namespace J1728QuarticLocalFactor

theorem square_scaled_iff_square
    {F : Type*} [Field F] (p u : F) (hp : p ≠ 0) :
    (∃ d : F, d ^ 2 = p ^ 2 * u) ↔ ∃ v : F, v ^ 2 = u := by
  constructor
  · rintro ⟨d, hd⟩
    refine ⟨d / p, ?_⟩
    calc
      (d / p) ^ 2 = d ^ 2 / p ^ 2 := by rw [div_pow]
      _ = u := by rw [hd]; field_simp [hp]
  · rintro ⟨v, hv⟩
    refine ⟨p * v, ?_⟩
    rw [mul_pow, hv]

theorem quadratic_split_iff_discriminant_square
    {F : Type*} [Field F] (b c : F) (two_ne_zero : (2 : F) ≠ 0) :
    (∃ x y : F, x + y = -b ∧ x * y = c) ↔
      ∃ s : F, s ^ 2 = b ^ 2 - 4 * c := by
  have four_ne_zero : (4 : F) ≠ 0 := by
    have h : (4 : F) = (2 : F) * (2 : F) := by ring
    rw [h]
    exact mul_ne_zero two_ne_zero two_ne_zero
  constructor
  · rintro ⟨x, y, hsum, hprod⟩
    refine ⟨x - y, ?_⟩
    calc
      (x - y) ^ 2 = (x + y) ^ 2 - 4 * (x * y) := by ring
      _ = b ^ 2 - 4 * c := by rw [hsum, hprod]; ring
  · rintro ⟨s, hs⟩
    refine ⟨(-b + s) / 2, (-b - s) / 2, ?_, ?_⟩
    · field_simp
      ring
    · calc
        ((-b + s) / 2) * ((-b - s) / 2) = (b ^ 2 - s ^ 2) / 4 := by
          field_simp [two_ne_zero, four_ne_zero]
          ring
        _ = c := by
          rw [hs]
          field_simp [two_ne_zero, four_ne_zero]
          ring

#print axioms square_scaled_iff_square
#print axioms quadratic_split_iff_discriminant_square

end J1728QuarticLocalFactor
