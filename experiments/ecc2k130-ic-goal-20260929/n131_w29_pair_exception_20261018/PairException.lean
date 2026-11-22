import Std
import Init.Grind.Ring.Basic

namespace PairException
open Lean.Grind

/-- Two reciprocal roots of the fixed-seed pair quadratics are linear
in their source products when `C+H=1`. -/
theorem reciprocal_roots_linearize
    {F : Type} [Field F] (charTwo : ∀ x : F, x+x=0)
    (C H p q u v : F) (hCH : C+H=1) (huv : u*v=1)
    (hp : C*u*u+p*u+H=0)
    (hq : C*v*v+q*v+H=0) :
    u=C*p+H*q ∧ v=H*p+C*q := by
  have htwo : (2 : F)=0 := by
    have hz:=charTwo 1
    grind +ring
  have hp' : p=C*u+H*v := by
    have hm := congrArg (fun z : F => z*v) hp
    grind +ring
  have hq' : q=C*v+H*u := by
    have hm := congrArg (fun z : F => z*u) hq
    grind +ring
  constructor <;> rw [hp',hq'] <;> grind +ring

/-- An exceptional zero-x sum requires a solution of one quadratic
product-subspace equation in the two source products. -/
theorem reciprocal_roots_force_product_one
    {F : Type} [Field F] (charTwo : ∀ x : F, x+x=0)
    (C H p q u v : F) (hCH : C+H=1) (huv : u*v=1)
    (hp : C*u*u+p*u+H=0)
    (hq : C*v*v+q*v+H=0) :
    (C*p+H*q)*(H*p+C*q)=1 := by
  obtain ⟨hu,hv⟩ := reciprocal_roots_linearize charTwo C H p q u v hCH huv hp hq
  rw [←hu,←hv]
  exact huv

/-- A nonzero common root of two fixed-seed pair quadratics forces
the same source product in both slots. -/
theorem common_nonzero_root_forces_equal_products
    {F : Type} [Field F] (charTwo : ∀ x : F, x+x=0)
    (C H p q u : F) (hu : u≠0)
    (hp : C*u*u+p*u+H=0)
    (hq : C*u*u+q*u+H=0) : p=q := by
  have htwo : (2 : F)=0 := by
    have hz:=charTwo 1
    grind +ring
  grind +ring

/-- Reparameterizing the second source product as `q=p+s` exposes
only bilinear products of the two W29 code vectors. -/
theorem sparse_product_identity
    {F : Type} [Field F] (charTwo : ∀ x : F, x+x=0)
    (C H p q s : F) (hCH : C+H=1) (hqs : q=p+s) :
    (C*p+H*q)*(H*p+C*q)=p*p+p*s+C*H*s*s := by
  have htwo : (2 : F)=0 := by
    have hz:=charTwo 1
    grind +ring
  rw [hqs]
  grind +ring

/-- On `y²+xy=x³+1`, the usual affine addition expression with
`T=(0,1)` has x-coordinate `1/x` whenever `x≠0`. -/
theorem two_torsion_translate_x
    {F : Type} [Field F] (charTwo : ∀ z : F, z+z=0)
    (x y : F) (hx : x≠0) (hcurve : y*y+x*y=x*x*x+1) :
    ((y+1)/x)*((y+1)/x)+(y+1)/x+x=1/x := by
  have htwo : (2 : F)=0 := by
    have hz:=charTwo 1
    grind +ring
  have hxi : x * x⁻¹ = 1 := Field.mul_inv_cancel hx
  rw [Field.div_eq_mul_inv]
  grind +ring

/-- The fixed-seed coefficient `C*H` is the square of the seed when
`H²+H` is that square. -/
theorem seed_square_factorization
    {F : Type} [Field F] (charTwo : ∀ z : F, z+z=0)
    (seed C H : F) (hCH : C+H=1)
    (hhalf : H*H+H=seed*seed) : C*H=seed*seed := by
  have htwo : (2 : F)=0 := by
    have hz:=charTwo 1
    grind +ring
  grind +ring

/-- An additive separator turns the three zero-coefficient terms into
an obstruction to the sparse equation. The fixed-instance certificate
supplies this functional and checks its generator values separately. -/
theorem additive_separator
    {F : Type} [Field F] (L : F → F)
    (hadd : ∀ a b, L (a+b)=L a+L b)
    (p s K : F) (hone : L 1=1)
    (hp2 : L (p*p)=0) (hps : L (p*s)=0)
    (hKs2 : L (K*s*s)=0) :
    p*p+p*s+K*s*s≠1 := by
  intro heq
  have hL := congrArg L heq
  rw [hadd, hadd, hp2, hps, hKs2, hone] at hL
  grind +ring

#print axioms PairException.reciprocal_roots_linearize
#print axioms PairException.reciprocal_roots_force_product_one
#print axioms PairException.common_nonzero_root_forces_equal_products
#print axioms PairException.sparse_product_identity
#print axioms PairException.two_torsion_translate_x
#print axioms PairException.seed_square_factorization
#print axioms PairException.additive_separator

end PairException
