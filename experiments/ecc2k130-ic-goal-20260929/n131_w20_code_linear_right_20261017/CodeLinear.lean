import Std
import Init.Grind.Ring.Basic

namespace CodeLinear
open Lean.Grind

/-- The pair product and the S3 root determine the division-free affine
relation used by the code solver. -/
theorem scaled_product {R : Type} [CommRing R]
    (charTwo : (2 : R) = 0) (A B D C H d p : R)
    (s3 : A * d^2 + B * d + D = 0)
    (pair : C * d^2 + p * d + H = 0) :
    D * p = (C * D + H * A) * d + H * B := by
  grind

/-- Every genuine right source product obeys a linearized quadratic in the
product. Its coefficients depend only on the left root and public target. -/
theorem source_implies_linearized {R : Type} [CommRing R]
    (charTwo : (2 : R) = 0) (A B D C H d p : R)
    (s3 : A * d^2 + B * d + D = 0)
    (pair : C * d^2 + p * d + H = 0) :
    let U := C * D + H * A
    let V := H * B
    (A * D^2) * p^2 + (B * U * D) * p +
      (A * V^2 + B * U * V + D * U^2) = 0 := by
  have affine := scaled_product charTwo A B D C H d p s3 pair
  grind

/-- With invertible leading map U, a code satisfying the linearized
equation reconstructs a root of the target S3 quadratic. -/
theorem linearized_implies_s3 {R : Type} [CommRing R]
    (charTwo : (2 : R) = 0) (A B D C H p inverseU : R)
    (hU : (C * D + H * A) * inverseU = 1)
    (linearized :
      let U := C * D + H * A
      let V := H * B
      (A * D^2) * p^2 + (B * U * D) * p +
        (A * V^2 + B * U * V + D * U^2) = 0) :
    let U := C * D + H * A
    let V := H * B
    let d := inverseU * (D * p + V)
    A * d^2 + B * d + D = 0 := by
  grind

/-- A candidate reconstructed from the linearized equation also obeys
the source pair quadratic when D is invertible. -/
theorem linearized_implies_pair {R : Type} [CommRing R]
    (charTwo : (2 : R) = 0) (A B D C H p inverseU inverseD : R)
    (hU : (C * D + H * A) * inverseU = 1)
    (hD : D * inverseD = 1)
    (linearized :
      let U := C * D + H * A
      let V := H * B
      (A * D^2) * p^2 + (B * U * D) * p +
        (A * V^2 + B * U * V + D * U^2) = 0) :
    let U := C * D + H * A
    let V := H * B
    let d := inverseU * (D * p + V)
    C * d^2 + p * d + H = 0 := by
  have hs3 := linearized_implies_s3 charTwo A B D C H p inverseU hU linearized
  grind

#print axioms CodeLinear.scaled_product
#print axioms CodeLinear.source_implies_linearized
#print axioms CodeLinear.linearized_implies_s3
#print axioms CodeLinear.linearized_implies_pair

end CodeLinear
