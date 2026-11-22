import PairResultant

namespace OneRootNorm
open Lean.Grind

def norm {F : Type} [Field F] (a g b z t : F) : F :=
  let t2 := t^2
  let k := 1 + t2*b
  let A := t2*a*g+t
  let B := a*k
  let D := g*k
  let E := t2*(b^2+1)
  let M := A*z+D
  let N := B*z+E
  N^2+g*N*M+b*M^2

theorem norm_eq_two_f3 {F : Type} [Field F]
    (two_zero : ∀ x : F, x+x=0)
    (a g b z w t : F)
    (hz : z^2+a*z+b=0)
    (hw : w^2+g*w+b=0) :
    norm a g b z t = PairResultant.f3 z w t * PairResultant.f3 z (w+g) t := by
  have hwshift : (w+g)^2+g*(w+g)+b=0 := by
    have hself := two_zero g
    grind +ring
  have hww : w*(w+g)=b := by
    have hself := two_zero b
    grind +ring
  let A := t^2*a*g+t
  let B := a*(1+t^2*b)
  let D := g*(1+t^2*b)
  let E := t^2*(b^2+1)
  let M := A*z+D
  let N := B*z+E
  have hf1 := PairResultant.f3_eq_bilinear two_zero a g b t z w hz hw
  have hf2 := PairResultant.f3_eq_bilinear two_zero a g b t z (w+g) hz hwshift
  have hF1 : PairResultant.f3 z w t = M*w+N := by
    rw [hf1]
    dsimp [M, N, A, B, D, E]
    grind +ring
  have hF2 : PairResultant.f3 z (w+g) t = M*(w+g)+N := by
    rw [hf2]
    dsimp [M, N, A, B, D, E]
    grind +ring
  have hproduct : (M*w+N)*(M*(w+g)+N)=N^2+g*N*M+b*M^2 := by
    calc
      (M*w+N)*(M*(w+g)+N) = N^2+g*N*M+(w*(w+g))*M^2 := by
        have hself := two_zero (M*N*w)
        grind +ring
      _ = N^2+g*N*M+b*M^2 := by rw [hww]
  calc
    norm a g b z t = N^2+g*N*M+b*M^2 := by rfl
    _ = (M*w+N)*(M*(w+g)+N) := hproduct.symm
    _ = PairResultant.f3 z w t * PairResultant.f3 z (w+g) t := by
      rw [hF1, hF2]

theorem norm_zero_iff_one_f3 {F : Type} [Field F]
    (two_zero : ∀ x : F, x+x=0)
    (a g b z w t : F)
    (hz : z^2+a*z+b=0)
    (hw : w^2+g*w+b=0) :
    norm a g b z t = 0 ↔
      PairResultant.f3 z w t = 0 ∨ PairResultant.f3 z (w+g) t = 0 := by
  rw [norm_eq_two_f3 two_zero a g b z w t hz hw]
  grind

#print axioms norm_eq_two_f3
#print axioms norm_zero_iff_one_f3

end OneRootNorm
