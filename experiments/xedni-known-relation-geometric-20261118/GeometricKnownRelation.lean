import Mathlib

/-!
Interpolation of a short Weierstrass model through an integral representative
of a public point, with exact equation and good-reduction conclusions.
-/

namespace XedniKnownRelationGeometric

def shortCurve {R : Type*} [CommRing R] (A B : R) : WeierstrassCurve R :=
  ⟨0, 0, 0, A, B⟩

theorem shortCurve_map {R S : Type*} [CommRing R] [CommRing S]
    (f : R →+* S) (A B : R) :
    (shortCurve A B).map f = shortCurve (f A) (f B) := by
  ext <;> simp [shortCurve, WeierstrassCurve.map]

theorem shortCurve_discriminant {R : Type*} [CommRing R] (A B : R) :
    (shortCurve A B).Δ = -16 * (4 * A ^ 3 + 27 * B ^ 2) := by
  simp only [shortCurve, WeierstrassCurve.Δ, WeierstrassCurve.b₂,
    WeierstrassCurve.b₄, WeierstrassCurve.b₆, WeierstrassCurve.b₈]
  ring

theorem interpolated_coefficient_map {S : Type*} [CommRing S]
    (f : ℤ →+* S) (A B₀ x y : ℤ)
    (hpoint : (f y) ^ 2 = (f x) ^ 3 + f A * f x + f B₀) :
    f (y ^ 2 - x ^ 3 - A * x) = f B₀ := by
  simp only [map_sub, map_pow, map_mul]
  rw [hpoint]
  ring

theorem interpolated_curve_reduction {S : Type*} [CommRing S]
    (f : ℤ →+* S) (A B₀ x y : ℤ)
    (hpoint : (f y) ^ 2 = (f x) ^ 3 + f A * f x + f B₀) :
    (shortCurve A (y ^ 2 - x ^ 3 - A * x)).map f =
      shortCurve (f A) (f B₀) := by
  rw [shortCurve_map, interpolated_coefficient_map f A B₀ x y hpoint]

theorem interpolated_curve_nonsingular {S : Type*} [CommRing S]
    (f : ℤ →+* S) (A B₀ x y : ℤ)
    (hpoint : (f y) ^ 2 = (f x) ^ 3 + f A * f x + f B₀)
    (hgood : (shortCurve (f A) (f B₀)).Δ ≠ 0) :
    (shortCurve A (y ^ 2 - x ^ 3 - A * x)).Δ ≠ 0 := by
  intro hz
  apply hgood
  have hmap := congrArg f hz
  simpa only [← WeierstrassCurve.map_Δ,
    interpolated_curve_reduction f A B₀ x y hpoint, map_zero] using hmap

theorem interpolated_rational_equation (A x y : ℤ) :
    let B : ℤ := y ^ 2 - x ^ 3 - A * x
    (shortCurve (A : ℚ) (B : ℚ)).toAffine.Equation (x : ℚ) (y : ℚ) := by
  dsimp
  rw [WeierstrassCurve.Affine.equation_iff]
  simp only [shortCurve]
  push_cast
  ring

theorem interpolated_rational_elliptic {S : Type*} [CommRing S]
    (f : ℤ →+* S) (A B₀ x y : ℤ)
    (hpoint : (f y) ^ 2 = (f x) ^ 3 + f A * f x + f B₀)
    (hgood : (shortCurve (f A) (f B₀)).Δ ≠ 0) :
    (shortCurve (A : ℚ) ((y ^ 2 - x ^ 3 - A * x : ℤ) : ℚ)).IsElliptic := by
  let B : ℤ := y ^ 2 - x ^ 3 - A * x
  have hΔz : (shortCurve A B).Δ ≠ 0 :=
    interpolated_curve_nonsingular f A B₀ x y hpoint hgood
  have hΔq : (shortCurve (A : ℚ) (B : ℚ)).Δ ≠ 0 := by
    have hcast : (((shortCurve A B).Δ : ℤ) : ℚ) ≠ 0 := by exact_mod_cast hΔz
    have hmap : ((shortCurve A B).map (Int.castRingHom ℚ)).Δ ≠ 0 := by
      simpa [WeierstrassCurve.map_Δ] using hcast
    simpa [shortCurve_map] using hmap
  exact ⟨(isUnit_iff_ne_zero).mpr hΔq⟩

theorem interpolated_rational_nonsingular_point {S : Type*} [CommRing S]
    (f : ℤ →+* S) (A B₀ x y : ℤ)
    (hpoint : (f y) ^ 2 = (f x) ^ 3 + f A * f x + f B₀)
    (hgood : (shortCurve (f A) (f B₀)).Δ ≠ 0) :
    (shortCurve (A : ℚ) ((y ^ 2 - x ^ 3 - A * x : ℤ) : ℚ)).toAffine.Nonsingular
      (x : ℚ) (y : ℚ) := by
  let B : ℤ := y ^ 2 - x ^ 3 - A * x
  let W : WeierstrassCurve ℚ := shortCurve (A : ℚ) (B : ℚ)
  have hEll : W.IsElliptic := by
    simpa only [W, B] using interpolated_rational_elliptic f A B₀ x y hpoint hgood
  have hΔ : W.Δ ≠ 0 := (isUnit_iff_ne_zero).mp hEll.isUnit
  exact (W.toAffine.equation_iff_nonsingular_of_Δ_ne_zero hΔ).mp
    (interpolated_rational_equation A x y)

#print axioms shortCurve_map
#print axioms shortCurve_discriminant
#print axioms interpolated_coefficient_map
#print axioms interpolated_curve_reduction
#print axioms interpolated_curve_nonsingular
#print axioms interpolated_rational_equation
#print axioms interpolated_rational_elliptic
#print axioms interpolated_rational_nonsingular_point

end XedniKnownRelationGeometric
