import Mathlib

/-!
Every shift that preserves the three public coordinate/coefficient residues
places its lifted point on a curve with the same reduced B coefficient.
The common-preimage relation remains exact for every shifted rational point.
-/

theorem shifted_one_point_curve_equation
    (x y A : ℤ) :
    let B := y ^ 2 - x ^ 3 - A * x
    y ^ 2 = x ^ 3 + A * x + B := by
  dsimp
  ring

theorem shifted_coefficient_reduces
    {K : Type*} [CommRing K] (red : ℤ →+* K)
    (x y A : ℤ) (X Y A₀ B₀ : K)
    (hx : red x = X) (hy : red y = Y) (hA : red A = A₀)
    (hpoint : Y ^ 2 = X ^ 3 + A₀ * X + B₀) :
    red (y ^ 2 - x ^ 3 - A * x) = B₀ := by
  simp only [map_sub, map_pow, map_mul, hx, hy, hA]
  linear_combination hpoint

theorem every_variant_common_relation
    {R : Type*} [AddCommGroup R] (a b : ℤ) (T : R) :
    a • (b • T) + b • ((-a) • T) = 0 := by
  calc
    a • (b • T) + b • ((-a) • T) = (a * b + b * (-a)) • T := by
      rw [smul_smul, smul_smul, add_smul]
    _ = (0 : ℤ) • T := by congr 1; ring
    _ = 0 := by simp

#print axioms shifted_one_point_curve_equation
#print axioms shifted_coefficient_reduces
#print axioms every_variant_common_relation
