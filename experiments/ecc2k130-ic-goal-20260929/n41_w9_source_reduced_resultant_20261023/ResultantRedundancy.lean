import Std
import Init.Grind.Ring.Basic

namespace ResultantRedundancy
open Lean.Grind

def s3 {F : Type} [Field F] (a b c : F) : F :=
  (1 + (a*b)^2)*c^2 + a*b*c + (a+b)^2

def jointResultant {F : Type} [Field F] (z u v t : F) : F :=
  let A := 1 + (u*v)^2
  let B := u*v
  let C := (u+v)^2
  let D := 1 + (z*t)^2
  let E := z*t
  let G := (z+t)^2
  (A*G+C*D)^2 + (A*E+B*D)*(B*G+C*E)

/-- The joint S3 resultant follows from the two existing S3 links.
    This is a polynomial implication over every characteristic-two field,
    including zero leading coefficients and exceptional reciprocals. -/
theorem joint_resultant_of_existing_links {F : Type} [Field F]
    (charTwo : ∀ x : F, x+x=0) (z u v w t : F)
    (hleft : s3 z u w = 0)
    (hright : s3 w v t = 0) :
    jointResultant z u v t = 0 := by
  unfold s3 at hleft hright
  unfold jointResultant
  have htwo : (2:F)=0 := by
    calc
      (2:F) = 1+1 := by grind +ring
      _ = 0 := charTwo 1
  grind +ring

#print axioms joint_resultant_of_existing_links

end ResultantRedundancy
