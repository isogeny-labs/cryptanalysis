import Mathlib.NumberTheory.LegendreSymbol.QuadraticChar.Basic
import Mathlib.Tactic

namespace M31.TwistQuotients

variable {F : Type*} [Field F] [Fintype F] [DecidableEq F]

private theorem square_sum (hF : ringChar F ≠ 2) (f : F → ℤ) :
    ∑ x : F, f (x^2) = ∑ u : F, (quadraticChar F u + 1) * f u := by
  classical
  calc
    _ = ∑ x : F, ∑ u : F, if x^2 = u then f u else 0 := by simp
    _ = ∑ u : F, ∑ x : F, if x^2 = u then f u else 0 := Finset.sum_comm
    _ = _ := by
      apply Finset.sum_congr rfl
      intro u _
      rw [← quadraticChar_card_sqrts hF u, ← Finset.sum_filter]
      simp [Set.toFinset_setOf]

private def cubic (u : F) := u^3 + 4*u^2 + 4*u - 196
private def reciprocal (v : F) := 1 + 4*v + 4*v^2 - 196*v^3

private theorem swap (u : F) :
    quadraticChar F u * quadraticChar F (cubic u) =
    quadraticChar F (reciprocal u⁻¹) - (if u = 0 then 1 else 0) := by
  by_cases hu : u = 0
  · simp [hu, reciprocal]
  · have h : u * cubic u = (u^2)^2 * reciprocal u⁻¹ := by
      unfold cubic reciprocal
      field_simp
    rw [← map_mul, h, map_mul, quadraticChar_sq_one' (pow_ne_zero 2 hu)]
    simp [hu]

/-- Character correlation for the two cubics x³ + 2x ± 14, in odd characteristic. -/
theorem correlation (hF : ringChar F ≠ 2) :
    ∑ x : F, quadraticChar F ((x^3 + 2*x + 14)*(x^3 + 2*x - 14)) =
      (∑ u : F, quadraticChar F (u^3 + 4*u^2 + 4*u - 196)) +
      (∑ v : F, quadraticChar F (1 + 4*v + 4*v^2 - 196*v^3)) - 1 := by
  classical
  have h (x : F) : (x^3+2*x+14)*(x^3+2*x-14) = cubic (x^2) := by unfold cubic; ring
  simp_rw [h]
  rw [square_sum hF (fun u => quadraticChar F (cubic u))]
  simp_rw [add_mul, one_mul, swap]
  rw [Finset.sum_add_distrib, Finset.sum_sub_distrib]
  have invsum := Equiv.sum_comp (Equiv.inv F) (fun v => quadraticChar F (reciprocal v))
  change (∑ v : F, quadraticChar F (reciprocal v⁻¹)) = _ at invsum
  rw [invsum]
  simp [reciprocal, cubic]
  ring

end M31.TwistQuotients
