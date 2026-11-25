import Mathlib.NumberTheory.LegendreSymbol.QuadraticChar.Basic
import Mathlib.Tactic

namespace M31.QuadraticClassTrace

variable {F : Type*} [Field F] [Fintype F] [DecidableEq F]

/-- Weighting the original cubic by the quadratic character of its
abscissa reuses the first cubic from the two-trace census. -/
theorem weighted_sum (a b : F) (hb : b ≠ 0) (hm : quadraticChar F (-1) = -1) :
    (∑ x : F, quadraticChar F x * quadraticChar F (x^3 + a*x + b)) =
      -(∑ u : F, quadraticChar F (u*(u+a)^2-b^2)) - 1 := by
  classical
  let h (u : F) := u*(u+a)^2-b^2
  let e := ((Equiv.inv F).trans (Equiv.mulLeft₀ (-b) (neg_ne_zero.mpr hb))).trans
    (Equiv.addRight (-a))
  have row (x : F) : quadraticChar F x * quadraticChar F (x^3+a*x+b) =
      -quadraticChar F (h (e x)) - (if x = 0 then 1 else 0) := by
    change _ = -quadraticChar F (h ((-b)*x⁻¹ + (-a))) - _
    by_cases hx : x = 0
    · subst x
      simp only [inv_zero, mul_zero, zero_add, h, neg_add_cancel, zero_pow (by decide : 2 ≠ 0),
        zero_sub, MulChar.map_zero, zero_mul, if_true]
      rw [← neg_one_mul (b^2), map_mul, hm, quadraticChar_sq_one' hb]
      norm_num
    · have alg : x*(x^3+a*x+b) = (-1) * (x^2/b)^2 * h ((-b)*x⁻¹+(-a)) := by
        dsimp [h]
        field_simp
        ring
      rw [← map_mul, alg, map_mul, map_mul, hm, quadraticChar_sq_one' (div_ne_zero (pow_ne_zero 2 hx) hb)]
      simp [hx]
  simp_rw [row]
  rw [Finset.sum_sub_distrib, Finset.sum_neg_distrib]
  have perm := Equiv.sum_comp e (fun u => quadraticChar F (h u))
  rw [perm]
  simp [h]

end M31.QuadraticClassTrace
