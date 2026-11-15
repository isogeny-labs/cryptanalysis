import Init.Grind.Ring.Basic
import Init.Grind.Module.Basic

/-! Conditional algebra for the canonical-class norm. Actual divisor groups,
principal divisors, the finite-cover function-field norm, R2/R4 algebras,
Picard functors and geometric surjectivity are written/native bridges.
These declarations do not identify those objects with the abstract modules.
No global inverse, execution proof or computational advantage is asserted. -/
set_option autoImplicit false
namespace G3CanonicalNorm
open Lean.Grind

theorem principal_push_well_defined
    {D J E : Type} [IntModule D] [IntModule J] [IntModule E]
    (cl : D → J) (push : D → E)
    (cl_sub : ∀ a b, cl (a-b)=cl a-cl b)
    (push_sub : ∀ a b, push (a-b)=push a-push b)
    (principal_norm : ∀ d, cl d=0 → push d=0)
    (a b : D) (same_class : cl a=cl b) : push a=push b := by
  have hc : cl (a-b)=0 := by rw [cl_sub, same_class]; grind
  have hp := principal_norm (a-b) hc
  rw [push_sub] at hp
  grind

theorem canonical_section_independence
    {D J E : Type} [IntModule D] [IntModule J] [IntModule E]
    (cl : D → J) (push : D → E)
    (cl_sub : ∀ a b, cl (a-b)=cl a-cl b)
    (push_sub : ∀ a b, push (a-b)=push a-push b)
    (principal_norm : ∀ d, cl d=0 → push d=0)
    (s t : J → D) (s_law : ∀ x, cl (s x)=x)
    (t_law : ∀ x, cl (t x)=x) (x : J) : push (s x)=push (t x) := by
  apply principal_push_well_defined cl push cl_sub push_sub principal_norm
  rw [s_law, t_law]

theorem descended_norm_additive
    {D J E : Type} [IntModule D] [IntModule J] [IntModule E]
    (cl : D → J) (push : D → E)
    (cl_sub : ∀ a b, cl (a-b)=cl a-cl b)
    (push_sub : ∀ a b, push (a-b)=push a-push b)
    (cl_add : ∀ a b, cl (a+b)=cl a+cl b)
    (push_add : ∀ a b, push (a+b)=push a+push b)
    (principal_norm : ∀ d, cl d=0 → push d=0)
    (s : J → D) (s_law : ∀ x, cl (s x)=x) (x y : J) :
    push (s (x+y))=push (s x)+push (s y) := by
  have h : push (s (x+y))=push (s x+s y) := by
    apply principal_push_well_defined cl push cl_sub push_sub principal_norm
    rw [s_law, cl_add, s_law, s_law]
  rw [h, push_add]

theorem plane_section_reference_independence
    {D J E : Type} [IntModule D] [IntModule J] [IntModule E]
    (cl : D → J) (push : D → E)
    (cl_sub : ∀ a b, cl (a-b)=cl a-cl b)
    (push_sub : ∀ a b, push (a-b)=push a-push b)
    (principal_norm : ∀ d, cl d=0 → push d=0)
    (d k0 k1 : D) (canonical_sections : cl k0=cl k1) :
    push (d-k0)=push (d-k1) := by
  apply principal_push_well_defined cl push cl_sub push_sub principal_norm
  rw [cl_sub, cl_sub, canonical_sections]

theorem exceptional_representative_correction
    {D : Type} [IntModule D] (canonical p0 p : D) :
    (canonical-p)-(canonical-p0)=p0-p := by grind

theorem monogenic_companion_characteristic
    {K : Type} [CommRing K] (t c0 c1 c2 : K) :
    t*(t*(t-c2)-c1)-c0=t^3-c2*t^2-c1*t-c0 := by grind

theorem monogenic_relation_evaluation
    {K : Type} [CommRing K] (t c0 c1 c2 : K)
    (relation : t^3=c0+c1*t+c2*t^2) :
    t^3-c2*t^2-c1*t-c0=0 := by grind

theorem repeated_cycle_multiplicity
    {E : Type} [IntModule E] (p q : E) :
    (2 : Int) • p+q=p+(p+q) := by grind

theorem reduced_cycle_changes_nonzero_repeated_point
    {E : Type} [IntModule E] (p q : E) (nonzero : p≠0) :
    (2 : Int) • p+q≠p+q := by grind

/- Surjectivity here is geometric surjectivity of the product pullback
over an algebraic closure. It is not surjectivity on Fq-rational points. -/
theorem reverse_composition_from_surjective_pullback
    {A J : Type} [IntModule A] [IntModule J]
    (pull : A → J) (norm : J → A)
    (pull_two : ∀ x, pull ((2 : Int) • x)=(2 : Int) • pull x)
    (diagonal : ∀ x, norm (pull x)=(2 : Int) • x)
    (geometric_surjectivity : ∀ j, ∃ x, pull x=j) (j : J) :
    pull (norm j)=(2 : Int) • j := by
  obtain ⟨x, hx⟩ := geometric_surjectivity j
  rw [← hx, diagonal, pull_two]

theorem odd_two_recovery
    {E : Type} [IntModule E] (ell u v : Int)
    (bezout : 2*u+ell*v=1) (x : E) (order : ell • x=0) :
    u • ((2 : Int) • x)=x := by
  have expand : x=u • ((2 : Int) • x)+v • (ell • x) := by
    calc
      x=(1 : Int) • x := (IntModule.one_zsmul x).symm
      _=(u*2+v*ell) • x := by congr 1; grind
      _=u • ((2 : Int) • x)+v • (ell • x) := by
        rw [IntModule.add_zsmul, IntModule.mul_zsmul, IntModule.mul_zsmul]
  rw [order, IntModule.zsmul_zero, AddCommMonoid.add_zero] at expand
  exact expand.symm

theorem two_way_odd_subgroup_recovery
    {E J : Type} [IntModule E] [IntModule J]
    (phi : E → J) (norm : J → E)
    (forward_composition : ∀ x, norm (phi x)=(2 : Int) • x)
    (reverse_composition : ∀ y, phi (norm y)=(2 : Int) • y)
    (ell u v : Int) (bezout : 2*u+ell*v=1)
    (x : E) (y : J) (order_x : ell • x=0) (order_y : ell • y=0) :
    u • norm (phi x)=x ∧ u • phi (norm y)=y := by
  rw [forward_composition, reverse_composition]
  exact ⟨odd_two_recovery ell u v bezout x order_x,
    odd_two_recovery ell u v bezout y order_y⟩

theorem actual_odd_recovery_constants :
    (2 : Int)*19+37*(-1)=1 ∧ (2 : Int)*45+89*(-1)=1 ∧
    (2 : Int)*166+331*(-1)=1 := by decide

end G3CanonicalNorm
#print axioms G3CanonicalNorm.principal_push_well_defined
#print axioms G3CanonicalNorm.canonical_section_independence
#print axioms G3CanonicalNorm.descended_norm_additive
#print axioms G3CanonicalNorm.plane_section_reference_independence
#print axioms G3CanonicalNorm.exceptional_representative_correction
#print axioms G3CanonicalNorm.monogenic_companion_characteristic
#print axioms G3CanonicalNorm.monogenic_relation_evaluation
#print axioms G3CanonicalNorm.repeated_cycle_multiplicity
#print axioms G3CanonicalNorm.reduced_cycle_changes_nonzero_repeated_point
#print axioms G3CanonicalNorm.reverse_composition_from_surjective_pullback
#print axioms G3CanonicalNorm.odd_two_recovery
#print axioms G3CanonicalNorm.two_way_odd_subgroup_recovery
#print axioms G3CanonicalNorm.actual_odd_recovery_constants
