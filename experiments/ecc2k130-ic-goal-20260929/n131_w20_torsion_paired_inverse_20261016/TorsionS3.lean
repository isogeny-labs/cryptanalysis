import Std
import Init.Grind.Ring.Basic

namespace TorsionS3
open Lean.Grind

/-- The raw reciprocal S3 equation for three nonzero x-coordinates. -/
def s3 {R : Type} [CommRing R] (u d z : R) : R :=
  (u*d*z)^2 + u*d*z + u^2 + d^2 + z^2

/-- Inverting both the right partial sum and target coordinates scales
    S3 by the nonzero square of their product. -/
theorem reciprocal_identity {R : Type} [CommRing R]
    (u d z e f : R) (de : d*e = 1) (zf : z*f = 1) :
    (d*z)^2 * s3 u e f = s3 u d z := by
  grind [s3]

/-- A right S3 root for one target is a reciprocal right root for its
    rational two-torsion partner. The inverse witnesses expose the chart
    assumptions used by the computation. -/
theorem reciprocal_root_iff {R : Type} [Field R]
    (u d z e f : R) (de : d*e = 1) (zf : z*f = 1) :
    s3 u d z = 0 ↔ s3 u e f = 0 := by
  have ed : e*d = 1 := by grind
  have fz : f*z = 1 := by grind
  have forward := reciprocal_identity u e f d z ed fz
  have backward := reciprocal_identity u d z e f de zf
  constructor
  · intro h
    grind
  · intro h
    grind

/-- The quadratic relation replaces the inverse of a right root by an
    affine expression in that root. -/
theorem inverse_linear {R : Type} [CommRing R]
    (A B E d e : R) (charTwo : (2 : R) = 0)
    (quadratic : A*d^2 + B*d + E = 0) (inverse : d*e = 1) :
    E*e = A*d+B := by
  grind

/-- Initial affine states for the original and torsion-partner product
    predicates in the same quadratic algebra. -/
theorem fused_initial {R : Type} [CommRing R]
    (A B E H d e : R) (charTwo : (2 : R) = 0)
    (quadratic : A*d^2 + B*d + E = 0) (inverse : d*e = 1) :
    E*((1+H)*d+H*e) = ((1+H)*E+H*A)*d+H*B ∧
    E*((1+H)*e+H*d) = ((1+H)*A+H*E)*d+(1+H)*B := by
  have h := inverse_linear A B E d e charTwo quadratic inverse
  constructor <;> grind

#print axioms reciprocal_identity
#print axioms reciprocal_root_iff
#print axioms inverse_linear
#print axioms fused_initial
end TorsionS3
