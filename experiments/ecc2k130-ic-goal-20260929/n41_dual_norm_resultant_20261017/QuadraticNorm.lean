import Std
import Init.Grind.Ring.Basic

namespace QuadraticNorm
open Lean.Grind

/-- The public reciprocal S3 equation is quadratic in the eliminated
coordinate, including the coefficient that defines its exceptional branch. -/
theorem s3AsQuadratic {R : Type} [CommRing R]
    (t u q : R) (charTwo : (2 : R) = 0) :
    (t + u + q) * (t + u + q) + t * u * q +
        (t * u * q) * (t * u * q) =
      (1 + (t * q) * (t * q)) * (u * u) +
        (t * q) * u + (t + q) * (t + q) := by
  grind

/-- Divide the quadratic by its invertible leading coefficient. -/
theorem normalizeQuadratic {R : Type} [CommRing R]
    (A B C inverse u : R)
    (inverseLaw : A * inverse = 1)
    (quadratic : A * (u * u) + B * u + C = 0) :
    u * u + (B * inverse) * u + C * inverse = 0 := by
  grind

/-- If a quadratic link and a linear reduced equation share a root in
characteristic two, the quadratic norm of the reduced equation vanishes. -/
theorem commonRootImpliesNormZero {R : Type} [CommRing R]
    (α β u r₀ r₁ : R)
    (charTwo : (2 : R) = 0)
    (quadratic : u * u + α * u + β = 0)
    (reduced : r₀ + r₁ * u = 0) :
    r₀ * r₀ + α * r₀ * r₁ + β * r₁ * r₁ = 0 := by
  grind

#print axioms s3AsQuadratic
#print axioms normalizeQuadratic
#print axioms commonRootImpliesNormZero

end QuadraticNorm
