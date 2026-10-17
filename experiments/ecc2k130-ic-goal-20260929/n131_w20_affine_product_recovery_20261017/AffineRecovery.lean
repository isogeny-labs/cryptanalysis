import Std
import Init.Grind.Ring.Basic

namespace AffineRecovery
open Lean.Grind

/-- On the nonzero constant-coefficient S3 chart, the right source product
is an affine function of either S3 root. The hypotheses are the exact S3
quadratic and a checked inverse of its constant coefficient. -/
theorem recovered_product_satisfies_pair {R : Type} [CommRing R]
    (charTwo : (2 : R) = 0)
    (A B D C H d inverseD : R)
    (s3 : A * (d * d) + B * d + D = 0)
    (invD : D * inverseD = 1) :
    C * (d * d) +
      ((C + H * A * inverseD) * d + H * B * inverseD) * d + H = 0 := by
  grind

/-- The inverse of an S3 root follows from the same constant-coefficient
inverse, including both roots of a split quadratic. -/
theorem s3_root_inverse {R : Type} [CommRing R]
    (charTwo : (2 : R) = 0)
    (A B D d inverseD : R)
    (s3 : A * (d * d) + B * d + D = 0)
    (invD : D * inverseD = 1) :
    d * ((A * d + B) * inverseD) = 1 := by
  grind

/-- Any source product whose pair quadratic holds at this S3 root equals
the affine recovered product. This supplies the no-false-negative direction. -/
theorem recovered_product_unique {R : Type} [CommRing R]
    (charTwo : (2 : R) = 0)
    (A B D C H d inverseD p : R)
    (s3 : A * (d * d) + B * d + D = 0)
    (invD : D * inverseD = 1)
    (pair : C * (d * d) + p * d + H = 0) :
    p = (C + H * A * inverseD) * d + H * B * inverseD := by
  have hroot := s3_root_inverse charTwo A B D d inverseD s3 invD
  have hrecover := recovered_product_satisfies_pair charTwo A B D C H d inverseD s3 invD
  grind

#print axioms AffineRecovery.recovered_product_satisfies_pair
#print axioms AffineRecovery.s3_root_inverse
#print axioms AffineRecovery.recovered_product_unique

end AffineRecovery
