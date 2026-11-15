import Mathlib

namespace XedniIntegralChord

/-- The two point equations and the tangent equation force the monic slope relation. -/
theorem monic_relation_of_tangent
    (x₁ y₁ x₂ y₂ a₁ a₂ a₃ a₄ a₆ m : ℚ)
    (hx : x₁ ≠ x₂)
    (hm : m * (x₁ - x₂) = y₁ - y₂)
    (hU : y₁ ^ 2 + a₁ * x₁ * y₁ + a₃ * y₁ -
      x₁ ^ 3 - a₂ * x₁ ^ 2 - a₄ * x₁ - a₆ = 0)
    (hV : y₂ ^ 2 + a₁ * x₂ * y₂ + a₃ * y₂ -
      x₂ ^ 3 - a₂ * x₂ ^ 2 - a₄ * x₂ - a₆ = 0)
    (htan : m * (2 * y₂ + a₁ * x₂ + a₃) -
      (3 * x₂ ^ 2 + 2 * a₂ * x₂ + a₄ - a₁ * y₂) = 0) :
    m ^ 2 + a₁ * m = a₂ + x₁ + 2 * x₂ := by
  have hy : y₁ = y₂ + m * (x₁ - x₂) := by linarith [hm]
  have hid : (x₁ - x₂) ^ 2 * (m ^ 2 + a₁ * m - a₂ - x₁ - 2 * x₂) =
      (y₁ ^ 2 + a₁ * x₁ * y₁ + a₃ * y₁ - x₁ ^ 3 - a₂ * x₁ ^ 2 - a₄ * x₁ - a₆) -
      (y₂ ^ 2 + a₁ * x₂ * y₂ + a₃ * y₂ - x₂ ^ 3 - a₂ * x₂ ^ 2 - a₄ * x₂ - a₆) -
      (x₁ - x₂) * (m * (2 * y₂ + a₁ * x₂ + a₃) -
        (3 * x₂ ^ 2 + 2 * a₂ * x₂ + a₄ - a₁ * y₂)) := by
    rw [hy]
    ring
  have hz : (x₁ - x₂) ^ 2 * (m ^ 2 + a₁ * m - a₂ - x₁ - 2 * x₂) = 0 := by
    rw [hid, hU, hV, htan]
    ring
  have hd : (x₁ - x₂) ^ 2 ≠ 0 := pow_ne_zero 2 (sub_ne_zero.mpr hx)
  have hr : m ^ 2 + a₁ * m - a₂ - x₁ - 2 * x₂ = 0 :=
    (mul_eq_zero.mp hz).resolve_left hd
  linarith

/-- A rational chord slope satisfying the integral monic relation is integral. -/
theorem integer_slope_of_monic_relation (m : ℚ) (a b : ℤ)
    (h : m ^ 2 + (a : ℚ) * m = (b : ℚ)) :
    ∃ z : ℤ, (z : ℚ) = m := by
  let f : Polynomial ℤ := Polynomial.X ^ 2 + (Polynomial.C a * Polynomial.X - Polynomial.C b)
  have hlinear : (Polynomial.C a * Polynomial.X).degree ≤ 1 := by
    simpa [pow_one] using (Polynomial.degree_C_mul_X_pow_le 1 a)
  have hdeg : (Polynomial.C a * Polynomial.X - Polynomial.C b).degree < 2 := by
    exact (Polynomial.degree_sub_le _ _).trans_lt
      ((max_le hlinear (Polynomial.degree_C_le.trans (by norm_num))).trans_lt
        (by norm_num))
  have hmonic : f.Monic := by
    change (Polynomial.X ^ 2 +
      (Polynomial.C a * Polynomial.X - Polynomial.C b)).Monic
    exact Polynomial.monic_X_pow_add hdeg
  have hroot : Polynomial.aeval m f = 0 := by
    simp [f]
    linarith [h]
  exact (IsIntegrallyClosed.isIntegral_iff.mp ⟨f, hmonic, hroot⟩)

/-- The algebraic tangent bridge plus integral first coefficients and x coordinates. -/
theorem integer_slope_of_tangent
    (x₁ y₁ x₂ y₂ a₁ a₂ : ℤ) (a₃ a₄ a₆ m : ℚ)
    (hx : x₁ ≠ x₂)
    (hm : m * ((x₁ : ℚ) - x₂) = (y₁ : ℚ) - y₂)
    (hU : (y₁ : ℚ) ^ 2 + a₁ * x₁ * y₁ + a₃ * y₁ -
      (x₁ : ℚ) ^ 3 - a₂ * x₁ ^ 2 - a₄ * x₁ - a₆ = 0)
    (hV : (y₂ : ℚ) ^ 2 + a₁ * x₂ * y₂ + a₃ * y₂ -
      (x₂ : ℚ) ^ 3 - a₂ * x₂ ^ 2 - a₄ * x₂ - a₆ = 0)
    (htan : m * (2 * (y₂ : ℚ) + a₁ * x₂ + a₃) -
      (3 * (x₂ : ℚ) ^ 2 + 2 * a₂ * x₂ + a₄ - a₁ * y₂) = 0) :
    ∃ z : ℤ, (z : ℚ) = m := by
  have hxc : (x₁ : ℚ) ≠ x₂ := by exact_mod_cast hx
  have hquad := monic_relation_of_tangent
    (x₁ : ℚ) y₁ x₂ y₂ a₁ a₂ a₃ a₄ a₆ m hxc hm hU hV htan
  exact integer_slope_of_monic_relation m a₁ (a₂ + x₁ + 2 * x₂)
    (by exact_mod_cast hquad)

#print axioms monic_relation_of_tangent
#print axioms integer_slope_of_monic_relation
#print axioms integer_slope_of_tangent

end XedniIntegralChord
