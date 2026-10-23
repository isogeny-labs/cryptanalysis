module

public import Mathlib.Tactic.Ring
public import Mathlib.Tactic.NormNum
public import Mathlib.Tactic.Linarith
public import Mathlib.Algebra.Ring.Rat

/-! Exact regularization of the j-function on X₀(11) at (16,60). -/
namespace RegularBranch

public def a0 (x : ℚ) : ℚ := (-65571886394223652 : ℚ) * x ^ 0 + (91576505827906298 : ℚ) * x ^ 1 + (84887294145843033 : ℚ) * x ^ 2 + (6419026712245052 : ℚ) * x ^ 3 + (-15124441025165095 : ℚ) * x ^ 4 + (-2179206296697095 : ℚ) * x ^ 5 + (558818644494837 : ℚ) * x ^ 6 + (81898270819143 : ℚ) * x ^ 7 + (2535876517772 : ℚ) * x ^ 8 + (19161808636 : ℚ) * x ^ 9 + (21559873 : ℚ) * x ^ 10 + (743 : ℚ) * x ^ 11
public def a1 (x : ℚ) : ℚ := (-26395208710078913 : ℚ) * x ^ 0 + (-16583607774597939 : ℚ) * x ^ 1 + (10293966016026733 : ℚ) * x ^ 2 + (5999011646737623 : ℚ) * x ^ 3 + (-579172383588254 : ℚ) * x ^ 4 + (-283597926046359 : ℚ) * x ^ 5 + (-17218222665169 : ℚ) * x ^ 6 + (-267091946884 : ℚ) * x ^ 7 + (-873240811 : ℚ) * x ^ 8 + (-196707 : ℚ) * x ^ 9 + (-1 : ℚ) * x ^ 10
public def curveRhs (x : ℚ) : ℚ := x ^ 3 - x ^ 2 - 10 * x - 20
public def quartic (x : ℚ) : ℚ := (9789217 : ℚ) * x ^ 0 + (4971236 : ℚ) * x ^ 1 + (1333262 : ℚ) * x ^ 2 + (-52820 : ℚ) * x ^ 3 + (1 : ℚ) * x ^ 4
public def extendedJ (x y : ℚ) : ℚ :=
  -(quartic x) ^ 3 / (a0 x + a1 x * (-1-y))

/-- Norm of the j-numerator under the elliptic-curve involution. -/
public theorem norm_identity (x : ℚ) :
    a0 x ^ 2 - a0 x * a1 x - a1 x ^ 2 * curveRhs x =
      -((x-16) ^ 11) * quartic x ^ 3 := by
  unfold a0 a1 curveRhs quartic
  ring

/-- The conjugate numerator stays nonzero at the regular point. -/
public theorem conjugate_nonzero : a0 16 + a1 16 * (-61) ≠ 0 := by
  norm_num [a0, a1]

/-- Both x=16 branches lie on the stated elliptic-curve model. -/
public theorem regular_point_on_curve :
    (60 : ℚ) ^ 2 + 60 = curveRhs 16 := by
  norm_num [curveRhs]

public theorem cusp_point_on_curve :
    (-61 : ℚ) ^ 2 - 61 = curveRhs 16 := by
  norm_num [curveRhs]

/-- The rational extension has the exact value -121 at (16,60). -/
public theorem regular_value : extendedJ 16 60 = -121 := by
  norm_num [extendedJ, quartic, a0, a1]

/-- Away from x=16, the extension agrees with the original j quotient on
the curve whenever its conjugate denominator is nonzero. -/
public theorem matches_original (x y : ℚ)
    (hcurve : y ^ 2 + y = curveRhs x) (hx : x ≠ 16)
    (hconj : a0 x + a1 x * (-1-y) ≠ 0) :
    (a0 x + a1 x * y) / (x-16) ^ 11 = extendedJ x y := by
  have hprod : (a0 x + a1 x * y) * (a0 x + a1 x * (-1-y)) =
      -((x-16) ^ 11) * quartic x ^ 3 := by
    calc
      _ = a0 x ^ 2 - a0 x * a1 x - a1 x ^ 2 * (y ^ 2 + y) := by ring
      _ = a0 x ^ 2 - a0 x * a1 x - a1 x ^ 2 * curveRhs x := by rw [hcurve]
      _ = -((x-16) ^ 11) * quartic x ^ 3 := norm_identity x
  unfold extendedJ
  have hpow : (x-16) ^ 11 ≠ 0 := pow_ne_zero _ (sub_ne_zero.mpr hx)
  apply (div_eq_div_iff hpow hconj).2
  nlinarith [hprod]

end RegularBranch

#print axioms RegularBranch.norm_identity
#print axioms RegularBranch.conjugate_nonzero
#print axioms RegularBranch.regular_point_on_curve
#print axioms RegularBranch.cusp_point_on_curve
#print axioms RegularBranch.regular_value
#print axioms RegularBranch.matches_original
