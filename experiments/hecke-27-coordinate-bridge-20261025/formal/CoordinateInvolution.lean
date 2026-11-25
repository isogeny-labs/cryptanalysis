import Mathlib.Tactic.Ring
import Mathlib.Tactic.FieldSimp
import Mathlib.Tactic.Linarith

/-! Rational addition by the cusp point (3,-5) on y²+y=x³-7. -/

namespace CoordinateInvolution

private def d (x : ℚ) : ℚ := x - 3
private def n (y : ℚ) : ℚ := 4 - y
private def A (x y : ℚ) : ℚ := n y ^ 2 - (x + 3) * d x ^ 2
private def B (x y : ℚ) : ℚ := n y * ((x + 6) * d x ^ 2 - n y ^ 2) + 4 * d x ^ 3

theorem numerator_identity (x y : ℚ) :
    B x y ^ 2 + B x y * d x ^ 3 - A x y ^ 3 + 7 * d x ^ 6 =
      -(d x ^ 3) * (x ^ 3 - 27*x - y ^ 2 + 8*y + 38) *
        (y ^ 2 + y - x ^ 3 + 7) := by
  unfold A B d n
  ring

theorem addition_coordinates (x y : ℚ) (hx : x ≠ 3) :
    A x y / d x ^ 2 = ((4-y)/(x-3)) ^ 2 - x - 3 ∧
    B x y / d x ^ 3 = ((4-y)/(x-3)) *
      (3 - A x y / d x ^ 2) + 4 := by
  have hd : x - 3 ≠ 0 := sub_ne_zero.mpr hx
  constructor
  · unfold A d n
    field_simp
    ring
  · unfold A B d n
    field_simp
    ring

theorem involution_preserves_curve (x y : ℚ)
    (hcurve : y ^ 2 + y = x ^ 3 - 7) (hx : x ≠ 3) :
    let xw := A x y / d x ^ 2
    let yw := B x y / d x ^ 3
    yw ^ 2 + yw = xw ^ 3 - 7 := by
  dsimp
  have hd : d x ≠ 0 := by
    unfold d
    exact sub_ne_zero.mpr hx
  have hnum : B x y ^ 2 + B x y * d x ^ 3 - A x y ^ 3 + 7 * d x ^ 6 = 0 := by
    rw [numerator_identity]
    have hc : y ^ 2 + y - x ^ 3 + 7 = 0 := by linarith
    rw [hc]
    ring
  have hformula :
      (B x y / d x ^ 3) ^ 2 + B x y / d x ^ 3 -
        (A x y / d x ^ 2) ^ 3 + 7 =
      (B x y ^ 2 + B x y * d x ^ 3 - A x y ^ 3 + 7 * d x ^ 6) /
        d x ^ 6 := by
    field_simp
  rw [hnum] at hformula
  simp only [zero_div] at hformula
  linarith

#print axioms numerator_identity
#print axioms addition_coordinates
#print axioms involution_preserves_curve

end CoordinateInvolution
