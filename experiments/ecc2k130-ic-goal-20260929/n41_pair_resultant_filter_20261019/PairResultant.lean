import Std
import Init.Grind.Ring.Basic

namespace PairResultant
open Lean.Grind

def f3 {F : Type} [Field F] (z w t : F) : F :=
  (z*w*t)^2 + z*w*t + (z+w+t)^2

def resultant {F : Type} [Field F] (a g b t : F) : F :=
  let t2 := t^2
  let k := 1 + t2*b
  let A := t2*a*g+t
  let B := a*k
  let D := g*k
  let E := t2*(b^2+1)
  let U := B^2+g*B*A+b*A^2
  let V := g*(B*D+E*A)
  let W := E^2+g*E*D+b*D^2
  let L1 := U*a+V
  let L0 := U*b+W
  L0^2+a*L0*L1+b*L1^2

def bilinearNorm {F : Type} [Field F] (a g b A B D E : F) : F :=
  let U := B^2+g*B*A+b*A^2
  let V := g*(B*D+E*A)
  let W := E^2+g*E*D+b*D^2
  let L1 := U*a+V
  let L0 := U*b+W
  L0^2+a*L0*L1+b*L1^2

def bilin {F : Type} [Field F] (A B D E z w : F) : F :=
  A*z*w+B*z+D*w+E

private theorem shifted_root {F : Type} [Field F]
    (two_zero : ∀ x : F, x+x=0)
    (a b z : F) (hz : z^2+a*z+b=0) :
    (z+a)^2+a*(z+a)+b=0 := by
  have hself := two_zero a
  grind +ring

private theorem affine_product_over_roots {F : Type} [Field F]
    (two_zero : ∀ x : F, x+x=0)
    (g b w M N : F)
    (hw : w^2+g*w+b=0) :
    (M*w+N)*(M*(w+g)+N)=N^2+g*N*M+b*M^2 := by
  have hww : w*(w+g)=b := by
    have hself := two_zero b
    grind +ring
  have hself := two_zero (M*N*w)
  calc
    (M*w+N)*(M*(w+g)+N) =
        N^2+g*N*M+(w*(w+g))*M^2 := by grind +ring
    _ = N^2+g*N*M+b*M^2 := by rw [hww]

/-- Reducing reciprocal S3 by both fixed-seed quadratics gives a bilinear
    equation in the two unresolved roots. -/
theorem f3_eq_bilinear {F : Type} [Field F]
    (two_zero : ∀ x : F, x+x=0)
    (a g b t z w : F)
    (hz : z^2+a*z+b=0)
    (hw : w^2+g*w+b=0) :
    f3 z w t = (t^2*a*g+t)*z*w + a*(1+t^2*b)*z +
      g*(1+t^2*b)*w + t^2*(b^2+1) := by
  have hsquare (x y : F) : (x+y)^2=x^2+y^2 := by
    calc
      (x+y)^2 = x^2+y^2+(x*y+x*y) := by grind +ring
      _ = x^2+y^2 := by rw [two_zero, AddCommMonoid.add_zero]
  have hexpand : f3 z w t = t^2*z^2*w^2+t*z*w+z^2+w^2+t^2 := by
    unfold f3
    rw [hsquare (z+w) t, hsquare z w]
    grind +ring
  have hz2 : z^2=a*z+b := by
    have hself := two_zero (a*z+b)
    grind +ring
  have hw2 : w^2=g*w+b := by
    have hself := two_zero (g*w+b)
    grind +ring
  have hpoly :
      t^2*z^2*w^2+t*z*w+z^2+w^2+t^2 =
      (t^2*a*g+t)*z*w+a*(1+t^2*b)*z+
        g*(1+t^2*b)*w+t^2*(b^2+1) := by
    rw [hz2, hw2]
    calc
      t^2*(a*z+b)*(g*w+b)+t*z*w+(a*z+b)+(g*w+b)+t^2 =
          (t^2*a*g+t)*z*w+a*(1+t^2*b)*z+
            g*(1+t^2*b)*w+t^2*(b^2+1)+(b+b) := by grind +ring
      _ = _ := by rw [two_zero b, AddCommMonoid.add_zero]
  exact hexpand.trans hpoly

theorem f3_to_bilinear {F : Type} [Field F]
    (two_zero : ∀ x : F, x+x=0)
    (a g b t z w : F)
    (hz : z^2+a*z+b=0)
    (hw : w^2+g*w+b=0)
    (hf : f3 z w t=0) :
    (t^2*a*g+t)*z*w + a*(1+t^2*b)*z +
      g*(1+t^2*b)*w + t^2*(b^2+1)=0 := by
  rw [f3_eq_bilinear two_zero a g b t z w hz hw] at hf
  exact hf

/-- The norm of the bilinear equation vanishes whenever two quadratic roots
    satisfy it. This is a necessary filter and includes zero-denominator
    cases because no division by a root-dependent expression occurs. -/
theorem bilinear_norm_zero {F : Type} [Field F]
    (two_zero : ∀ x : F, x+x=0)
    (a g b A B D E z w : F)
    (hz : z^2+a*z+b=0)
    (hw : w^2+g*w+b=0)
    (hbilinear : A*z*w+B*z+D*w+E=0) :
    bilinearNorm a g b A B D E=0 := by
  let M := A*z+D
  let N := B*z+E
  let U := B^2+g*B*A+b*A^2
  let V := g*(B*D+E*A)
  let W := E^2+g*E*D+b*D^2
  let L1 := U*a+V
  let L0 := U*b+W
  have hN : N=M*w := by
    have hself := two_zero (M*w)
    dsimp [N, M] at *
    grind +ring
  have hG : N^2+g*N*M+b*M^2=0 := by
    rw [hN]
    have hfactor : (M*w)^2+g*(M*w)*M+b*M^2 =
        M^2*(w^2+g*w+b) := by grind +ring
    rw [hfactor, hw]
    grind
  have hExpand : N^2+g*N*M+b*M^2=U*z^2+V*z+W := by
    have hcross₀ := two_zero (B*z*E)
    have hcross₁ := two_zero (A*z*D)
    dsimp [N, M, U, V, W]
    grind +ring
  have hz2 : z^2=a*z+b := by
    have hself := two_zero (a*z+b)
    grind +ring
  have hL : L0+L1*z=0 := by
    dsimp [L0, L1]
    have h := hG
    rw [hExpand] at h
    rw [hz2] at h
    grind +ring
  have hzz : z*(z+a)=b := by
    have hself := two_zero (a*z)
    grind +ring
  have hnorm : L0^2+a*L0*L1+b*L1^2 =
      (L0+L1*z)*(L0+L1*(z+a)) := by
    have hself := two_zero (L0*L1*z)
    grind +ring
  dsimp [bilinearNorm]
  rw [hnorm, hL]
  grind

/-- When both pair quadratics split, the norm is exactly the product over
    their four root choices. This gives sufficiency as well as necessity for
    the reciprocal S3 equation, with no exceptional denominator. -/
theorem bilinear_norm_eq_four_roots {F : Type} [Field F]
    (two_zero : ∀ x : F, x+x=0)
    (a g b A B D E z w : F)
    (hz : z^2+a*z+b=0)
    (hw : w^2+g*w+b=0) :
    bilinearNorm a g b A B D E =
      bilin A B D E z w * bilin A B D E z (w+g) *
      bilin A B D E (z+a) w * bilin A B D E (z+a) (w+g) := by
  let U := B^2+g*B*A+b*A^2
  let V := g*(B*D+E*A)
  let W := E^2+g*E*D+b*D^2
  let L1 := U*a+V
  let L0 := U*b+W
  let G := fun x : F => (B*x+E)^2+g*(B*x+E)*(A*x+D)+b*(A*x+D)^2
  have hExpand (x : F) : G x=U*x^2+V*x+W := by
    have hcross₀ := two_zero (B*x*E)
    have hcross₁ := two_zero (A*x*D)
    dsimp [G, U, V, W]
    grind +ring
  have hReduce (x : F) (hx : x^2+a*x+b=0) : G x=L0+L1*x := by
    have hx2 : x^2=a*x+b := by
      have hself := two_zero (a*x+b)
      grind +ring
    rw [hExpand, hx2]
    dsimp [L0, L1]
    grind +ring
  have hProd (x : F) :
      bilin A B D E x w * bilin A B D E x (w+g) = G x := by
    have hforms :
        bilin A B D E x w * bilin A B D E x (w+g) =
        ((A*x+D)*w+(B*x+E))*((A*x+D)*(w+g)+(B*x+E)) := by
      dsimp [bilin]
      grind +ring
    rw [hforms]
    exact affine_product_over_roots two_zero g b w (A*x+D) (B*x+E) hw
  have hshift := shifted_root two_zero a b z hz
  have hzz : z*(z+a)=b := by
    have hself := two_zero b
    grind +ring
  have hnorm : L0^2+a*L0*L1+b*L1^2 =
      (L0+L1*z)*(L0+L1*(z+a)) := by
    have hself := two_zero (L0*L1*z)
    grind +ring
  change L0^2+a*L0*L1+b*L1^2 = _
  calc
    L0^2+a*L0*L1+b*L1^2 = (L0+L1*z)*(L0+L1*(z+a)) := hnorm
    _ = G z * G (z+a) := by rw [hReduce z hz, hReduce (z+a) hshift]
    _ = bilin A B D E z w * bilin A B D E z (w+g) *
          bilin A B D E (z+a) w * bilin A B D E (z+a) (w+g) := by
      rw [← hProd z, ← hProd (z+a)]
      grind +ring

/-- A genuine two-pair reciprocal S3 witness always passes the branch-free
    resultant. The only field assumption beyond `Field` is characteristic 2.
    No root-dependent divisor is inverted, so all exceptional bilinear
    coefficients are covered. -/
theorem resultant_zero_of_f3 {F : Type} [Field F]
    (two_zero : ∀ x : F, x+x=0)
    (a g b t z w : F)
    (hz : z^2+a*z+b=0)
    (hw : w^2+g*w+b=0)
    (hf : f3 z w t=0) :
    resultant a g b t=0 := by
  have hbilinear := f3_to_bilinear two_zero a g b t z w hz hw hf
  exact bilinear_norm_zero two_zero a g b
    (t^2*a*g+t) (a*(1+t^2*b)) (g*(1+t^2*b))
    (t^2*(b^2+1)) z w hz hw hbilinear

/-- Dividing the common-leading-coefficient pair quadratic by a supplied
    inverse preserves the exact root condition. -/
theorem normalize_pair_root {F : Type} [Field F]
    (C Cinv p H z : F)
    (hinv : C*Cinv=1)
    (hroot : C*z^2+p*z+H=0) :
    z^2+(p*Cinv)*z+H*Cinv=0 := by
  have hmul := congrArg (fun x : F => x*Cinv) hroot
  grind +ring

/-- The fixed-seed quadratic form used by the binary-curve pair source
    therefore has a branch-free necessary target predicate. -/
theorem fixed_seed_pair_resultant_zero {F : Type} [Field F]
    (two_zero : ∀ x : F, x+x=0)
    (C Cinv p q H t z w : F)
    (hinv : C*Cinv=1)
    (hz : C*z^2+p*z+H=0)
    (hw : C*w^2+q*w+H=0)
    (hf : f3 z w t=0) :
    resultant (p*Cinv) (q*Cinv) (H*Cinv) t=0 := by
  exact resultant_zero_of_f3 two_zero (p*Cinv) (q*Cinv) (H*Cinv)
    t z w (normalize_pair_root C Cinv p H z hinv hz)
    (normalize_pair_root C Cinv q H w hinv hw) hf

/-- With the two source-valid root pairs present, the branch-free resultant
    is exactly the product of the four reciprocal S3 checks. -/
theorem resultant_eq_four_f3 {F : Type} [Field F]
    (two_zero : ∀ x : F, x+x=0)
    (a g b t z w : F)
    (hz : z^2+a*z+b=0)
    (hw : w^2+g*w+b=0) :
    resultant a g b t =
      f3 z w t * f3 z (w+g) t *
      f3 (z+a) w t * f3 (z+a) (w+g) t := by
  let A := t^2*a*g+t
  let B := a*(1+t^2*b)
  let D := g*(1+t^2*b)
  let E := t^2*(b^2+1)
  have hshiftz := shifted_root two_zero a b z hz
  have hshiftw := shifted_root two_zero g b w hw
  have h00 := f3_eq_bilinear two_zero a g b t z w hz hw
  have h01 := f3_eq_bilinear two_zero a g b t z (w+g) hz hshiftw
  have h10 := f3_eq_bilinear two_zero a g b t (z+a) w hshiftz hw
  have h11 := f3_eq_bilinear two_zero a g b t (z+a) (w+g) hshiftz hshiftw
  change bilinearNorm a g b A B D E = _
  rw [bilinear_norm_eq_four_roots two_zero a g b A B D E z w hz hw]
  dsimp [bilin, A, B, D, E]
  rw [h00, h01, h10, h11]

/-- For a source-valid pair of split quadratics, the scalar filter accepts
    exactly when at least one of the four reciprocal S3 branches accepts. -/
theorem resultant_zero_iff_four_f3 {F : Type} [Field F]
    (two_zero : ∀ x : F, x+x=0)
    (a g b t z w : F)
    (hz : z^2+a*z+b=0)
    (hw : w^2+g*w+b=0) :
    resultant a g b t=0 ↔
      f3 z w t=0 ∨ f3 z (w+g) t=0 ∨
      f3 (z+a) w t=0 ∨ f3 (z+a) (w+g) t=0 := by
  rw [resultant_eq_four_f3 two_zero a g b t z w hz hw]
  grind

#print axioms f3_eq_bilinear
#print axioms f3_to_bilinear
#print axioms bilinear_norm_zero
#print axioms resultant_zero_of_f3
#print axioms normalize_pair_root
#print axioms fixed_seed_pair_resultant_zero
#print axioms bilinear_norm_eq_four_roots
#print axioms resultant_eq_four_f3
#print axioms resultant_zero_iff_four_f3

end PairResultant
