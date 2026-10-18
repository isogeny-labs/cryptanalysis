import Std
import Init.Grind.Ring.Basic

namespace StagedS3
open Lean.Grind

def s3 {F : Type} [CommRing F] (a b t : F) : F :=
  let v := a*b*t
  v*v+v+a*a+b*b+t*t

def f4 {F : Type} [CommRing F] (a b c z : F) : F :=
  let A := 1+(a*b)*(a*b)
  let B := a*b
  let C := a*a+b*b
  let D := 1+(c*z)*(c*z)
  let E := c*z
  let G := c*c+z*z
  (A*G+C*D)*(A*G+C*D)+(A*E+B*D)*(B*G+C*E)

/-- A shared root of the two quadratic S3 equations forces their
four-point eliminant to vanish, including singular leading coefficients. -/
theorem two_quadratics_imply_resultant
    {F : Type} [CommRing F] (charTwo : ∀ x : F, x+x=0)
    (A B C D E G m : F)
    (hfirst : A*m*m+B*m+C=0)
    (hsecond : D*m*m+E*m+G=0) :
    (A*G+C*D)*(A*G+C*D)+(A*E+B*D)*(B*G+C*E)=0 := by
  have htwo : (2 : F)=0 := by
    have hz:=charTwo 1
    grind +ring
  let M : F := A*G+C*D
  let L : F := A*E+B*D
  have hM : M=L*m := by
    have hi : L*m+M = A*(D*m*m+E*m+G)+D*(A*m*m+B*m+C) := by
      dsimp [L,M]
      grind +ring
    rw [hfirst,hsecond] at hi
    dsimp [L,M] at *
    grind +ring
  have hG : G=D*m*m+E*m := by grind +ring
  have hC : C=A*m*m+B*m := by grind +ring
  have hN : B*G+C*E=L*m*m := by
    rw [hG,hC]
    dsimp [L]
    grind +ring
  change M*M+L*(B*G+C*E)=0
  rw [hM,hN]
  grind +ring

/-- Two reciprocal-x S3 links imply the exact F4 polynomial gate. -/
theorem staged_s3_implies_f4
    {F : Type} [CommRing F] (charTwo : ∀ x : F, x+x=0)
    (a b c z m : F)
    (hfirst : s3 a b m=0)
    (hsecond : s3 m c z=0) : f4 a b c z=0 := by
  have h1 : (1+(a*b)*(a*b))*m*m+(a*b)*m+(a*a+b*b)=0 := by
    dsimp [s3] at hfirst
    grind +ring
  have h2 : (1+(c*z)*(c*z))*m*m+(c*z)*m+(c*c+z*z)=0 := by
    have hid : (1+(c*z)*(c*z))*m*m+(c*z)*m+(c*c+z*z) =
        (m*c*z)*(m*c*z)+(m*c*z)+m*m+c*c+z*z := by
      clear hfirst hsecond h1
      grind +ring
    rw [hid]
    simpa [s3] using hsecond
  have h := two_quadratics_imply_resultant charTwo
    (1+(a*b)*(a*b)) (a*b) (a*a+b*b)
    (1+(c*z)*(c*z)) (c*z) (c*c+z*z) m h1 h2
  simpa [f4] using h

#print axioms StagedS3.two_quadratics_imply_resultant
#print axioms StagedS3.staged_s3_implies_f4

end StagedS3
