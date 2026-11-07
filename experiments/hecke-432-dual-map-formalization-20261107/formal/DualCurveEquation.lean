import Mathlib.Tactic

/-!
  Algebraic part of the archived level-432 dual-map formula.  This file proves
  only that the displayed rational coordinates satisfy the target Weierstrass
  equation when the input satisfies the source equation and `x ≠ 0`.
  It does not construct a morphism at the exceptional points, prove a group
  homomorphism or degree, or identify either modular parametrization.
-/

namespace Hecke432DualCurve

theorem numerator_identity {R : Type*} [CommRing R] (x : R) :
    (x ^ 3 - 16) * (x ^ 3 + 128) ^ 2 - (x ^ 3 - 64) ^ 3 = 432 * x ^ 6 := by
  ring

theorem curve_equation {K : Type*} [Field K]
    (x y : K) (hx : x ≠ 0) (hB : y ^ 2 = x ^ 3 - 16) :
    (y * (x ^ 3 + 128) / x ^ 3) ^ 2 =
      ((x ^ 3 - 64) / x ^ 2) ^ 3 + 432 := by
  calc
    (y * (x ^ 3 + 128) / x ^ 3) ^ 2 =
        y ^ 2 * (x ^ 3 + 128) ^ 2 / x ^ 6 := by ring
    _ = (x ^ 3 - 16) * (x ^ 3 + 128) ^ 2 / x ^ 6 := by rw [hB]
    _ = ((x ^ 3 - 64) / x ^ 2) ^ 3 + 432 := by
      field_simp [hx]
      ring

#print axioms numerator_identity
#print axioms curve_equation

end Hecke432DualCurve
