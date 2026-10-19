import Std
import Init.Grind.Ring.Basic

namespace FactoredElimination
open Lean.Grind

/-- A linear constraint and the first pair quadratic imply the final
    determinant condition in characteristic two. No leading coefficient
    assumption is needed for this implication. -/
theorem linear_quadratic_elimination {F : Type} [Field F]
    (charTwo : ∀ x : F, x+x=0)
    (C p H L M z : F)
    (hq : C*z^2+p*z+H=0)
    (hl : L*z+M=0) :
    C*M^2+p*L*M+H*L^2=0 := by
  have h1 := charTwo (L*z)
  have h2 := charTwo (C*z^2+p*z)
  grind +ring

#print axioms linear_quadratic_elimination

/-- Reduction of a quartic modulo the first pair quadratic, with the
    leading-coefficient powers kept explicit. -/
theorem quartic_reduction {F : Type} [Field F]
    (charTwo : ∀ x : F, x+x=0)
    (C p H K0 K1 K2 K3 K4 z : F)
    (hq : C*z^2+p*z+H=0)
    (hf : K0+K1*z+K2*z^2+K3*z^3+K4*z^4=0) :
    (C^3*K1+C^2*p*K2+C*(p^2+C*H)*K3+p^3*K4)*z+
    (C^3*K0+C^2*H*K2+C*p*H*K3+(p^2*H+C*H^2)*K4)=0 := by
  have h2 : C*z^2 = p*z+H := by
    have ht := charTwo (p*z+H)
    grind +ring
  have h3 : C^2*z^3 = (p^2+C*H)*z+p*H := by
    have ht := charTwo ((p^2+C*H)*z+p*H)
    grind +ring
  have h4 : C^3*z^4 = p^3*z+p^2*H+C*H^2 := by
    have ht := charTwo (p^3*z+p^2*H+C*H^2)
    grind +ring
  have hfscaled := congrArg (fun x : F => C^3*x) hf
  grind +ring

#print axioms quartic_reduction

/-- A root of the first pair quadratic and an eliminated quartic forces
    the denominator-free final constraint. -/
theorem quartic_quadratic_elimination {F : Type} [Field F]
    (charTwo : ∀ x : F, x+x=0)
    (C p H K0 K1 K2 K3 K4 z : F)
    (hq : C*z^2+p*z+H=0)
    (hf : K0+K1*z+K2*z^2+K3*z^3+K4*z^4=0) :
    let L := C^3*K1+C^2*p*K2+C*(p^2+C*H)*K3+p^3*K4
    let M := C^3*K0+C^2*H*K2+C*p*H*K3+(p^2*H+C*H^2)*K4
    C*M^2+p*L*M+H*L^2=0 := by
  dsimp
  exact linear_quadratic_elimination charTwo C p H _ _ z hq
    (quartic_reduction charTwo C p H K0 K1 K2 K3 K4 z hq hf)

#print axioms quartic_quadratic_elimination

private theorem quadratic_common_root {F : Type} [Field F]
    (charTwo : ∀ x : F, x+x=0)
    (A B C D E G z : F)
    (hf : A*z^2+B*z+C=0)
    (hg : D*z^2+E*z+G=0) :
    (A*G+C*D)^2+(A*E+B*D)*(B*G+C*E)=0 := by
  have hC := charTwo (A*z^2+B*z)
  have hG := charTwo (D*z^2+E*z)
  grind +ring

/-- Eliminate the second pair reciprocal from S3. The resulting quartic
    has the five coefficient formulas used by the circuit. -/
theorem second_pair_s3_elimination {F : Type} [Field F]
    (charTwo : ∀ x : F, x+x=0)
    (D q J z₁ z₂ t : F)
    (hq : D*z₂^2+q*z₂+J=0)
    (hs3 : (z₁*z₂*t)^2+z₁*z₂*t+(z₁+z₂)^2+t^2=0) :
    let U0 := J+D*t^2
    let U2 := D+J*t^2
    let K0 := U0^2+q^2*t^2
    let K1 := q*t*U0
    let K2 := q^2*(1+t^4)+D*J*t^2
    let K3 := q*t*U2
    let K4 := U2^2+q^2*t^2
    K0+K1*z₁+K2*z₁^2+K3*z₁^3+K4*z₁^4=0 := by
  have htwo : (2:F)=0 := by
    calc
      (2:F) = 1+1 := by grind +ring
      _ = 0 := charTwo 1
  have hs3quad : (z₁^2*t^2+1)*z₂^2+(z₁*t)*z₂+(z₁^2+t^2)=0 := by
    grind +ring
  have hres := quadratic_common_root charTwo
    (z₁^2*t^2+1) (z₁*t) (z₁^2+t^2) D q J z₂ hs3quad hq
  dsimp
  grind +ring

#print axioms second_pair_s3_elimination

/-- Exact necessary factored condition for a pair of source quadratics
    joined by the characteristic-two S3 equation. The output keeps the
    denominator-free leading-coefficient scale, so all degenerate S3
    leading-coefficient cases are retained. -/
theorem two_pair_factored_necessary {F : Type} [Field F]
    (charTwo : ∀ x : F, x+x=0)
    (C p H D q J z₁ z₂ t : F)
    (hfirst : C*z₁^2+p*z₁+H=0)
    (hsecond : D*z₂^2+q*z₂+J=0)
    (hs3 : (z₁*z₂*t)^2+z₁*z₂*t+(z₁+z₂)^2+t^2=0) :
    let U0 := J+D*t^2
    let U2 := D+J*t^2
    let K0 := U0^2+q^2*t^2
    let K1 := q*t*U0
    let K2 := q^2*(1+t^4)+D*J*t^2
    let K3 := q*t*U2
    let K4 := U2^2+q^2*t^2
    let L := C^3*K1+C^2*p*K2+C*(p^2+C*H)*K3+p^3*K4
    let M := C^3*K0+C^2*H*K2+C*p*H*K3+(p^2*H+C*H^2)*K4
    C*M^2+p*L*M+H*L^2=0 := by
  dsimp
  exact quartic_quadratic_elimination charTwo C p H _ _ _ _ _ z₁ hfirst
    (second_pair_s3_elimination charTwo D q J z₁ z₂ t hsecond hs3)

#print axioms two_pair_factored_necessary

end FactoredElimination
