import Mathlib

/-!
The polynomial tangent admission identity for two affine points on the same
short Weierstrass curve. The group-law interpretation of the tangent equation
is stated separately in the research report.
-/

theorem tangent_square_identity
    {K : Type*} [CommRing K] (x y u v A B : K)
    (hP : y ^ 2 = x ^ 3 + A * x + B)
    (hR : v ^ 2 = u ^ 3 + A * u + B) :
    (x - u) * (3 * x ^ 2 + A) - 2 * y * (y + v) =
      (x - u) ^ 2 * (2 * x + u) - (y + v) ^ 2 := by
  calc
    (x - u) * (3 * x ^ 2 + A) - 2 * y * (y + v) =
        (x - u) ^ 2 * (2 * x + u) - (y + v) ^ 2 +
          (x ^ 3 + A * x + B - y ^ 2) - (u ^ 3 + A * u + B - v ^ 2) := by ring
    _ = (x - u) ^ 2 * (2 * x + u) - (y + v) ^ 2 := by rw [← hP, ← hR]; ring

theorem tangent_equation_iff_square_condition
    {K : Type*} [CommRing K] (x y u v A B : K)
    (hP : y ^ 2 = x ^ 3 + A * x + B)
    (hR : v ^ 2 = u ^ 3 + A * u + B) :
    (x - u) * (3 * x ^ 2 + A) = 2 * y * (y + v) ↔
      (y + v) ^ 2 = (x - u) ^ 2 * (2 * x + u) := by
  have h := tangent_square_identity x y u v A B hP hR
  constructor
  · intro hh
    have hzero : (x - u) ^ 2 * (2 * x + u) - (y + v) ^ 2 = 0 := by
      rw [hh, sub_self] at h
      exact h.symm
    exact (sub_eq_zero.mp hzero).symm
  · intro hh
    have hzero : (x - u) * (3 * x ^ 2 + A) - 2 * y * (y + v) = 0 := by
      rw [hh, sub_self] at h
      exact h
    exact sub_eq_zero.mp hzero

#print axioms tangent_square_identity
#print axioms tangent_equation_iff_square_condition
