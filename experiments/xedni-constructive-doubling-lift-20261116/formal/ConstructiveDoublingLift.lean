import Mathlib

/-!
Polynomial coordinates of an integral tangent lift. For a finite-field
specialization, the second theorem establishes reduction of the new curve
coefficients to the chosen public curve, provided the chosen slope is the
public doubling slope. The remaining group-law bridge is recorded in RESULT.
-/

theorem constructed_doubling_coordinates
    {K : Type*} [CommRing K] (x y s : K) :
    let A := 2 * y * s - 3 * x ^ 2
    let B := y ^ 2 - x ^ 3 - A * x
    let u := s ^ 2 - 2 * x
    let v := s * (x - u) - y
    y ^ 2 = x ^ 3 + A * x + B ∧
      v ^ 2 = u ^ 3 + A * u + B ∧
      3 * x ^ 2 + A = 2 * y * s ∧
      (y + v) ^ 2 = (x - u) ^ 2 * (2 * x + u) := by
  dsimp
  constructor
  · ring
  constructor
  · ring
  constructor
  · ring
  · ring

theorem constructed_coefficients_reduce
    {K : Type*} [CommRing K] (x y s A₀ B₀ : K)
    (hs : 2 * y * s = 3 * x ^ 2 + A₀)
    (hP : y ^ 2 = x ^ 3 + A₀ * x + B₀) :
    let A := 2 * y * s - 3 * x ^ 2
    let B := y ^ 2 - x ^ 3 - A * x
    A = A₀ ∧ B = B₀ := by
  dsimp
  have hA : 2 * y * s - 3 * x ^ 2 = A₀ := by linear_combination hs
  constructor
  · exact hA
  · rw [hA]
    linear_combination hP

#print axioms constructed_doubling_coordinates
#print axioms constructed_coefficients_reduce
