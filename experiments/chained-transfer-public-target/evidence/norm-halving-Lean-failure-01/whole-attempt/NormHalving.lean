import Init.Grind.Module.Basic
import Init.Grind.Ring.Basic

/-! Prospective6dc948. Ordinary ring and abelian group algebra only.
Actual curve/Weil-restriction/Picard/order/cofactor-table bridges stay explicit.
The abscissa identity reuses the existing TwoPrimaryQuotient proof.
-/
set_option autoImplicit false
namespace NormHalving
open Lean.Grind

theorem halving_abscissa_identity {R : Type} [CommRing R] (x a b u : R) :
    (3*x^2+a)^2-4*(x^3+a*x+b)*(2*x+u) =
    x^4-4*u*x^3-2*a*x^2-(8*b+4*a*u)*x+a^2-4*b*u := by
  grind

theorem halving_ordinate_identity {R : Type} [CommRing R] (x a b u : R) :
    (x^3-3*u*x^2-a*x-a*u-2*b)^2 -
      4*(u^3+a*u+b)*(x^3+a*x+b) =
    (x^4-4*u*x^3-2*a*x^2-4*(a*u+2*b)*x+a^2-4*b*u)*(x-u)^2 := by
  grind

theorem halves_differ_by_two_torsion {A : Type} [IntModule A]
    (q a b : A) (ha : (2 : Int) • a=q) (hb : (2 : Int) • b=q) :
    (2 : Int) • (a-b)=0 := by
  grind

theorem halves_fixed_by_frobenius_square {A : Type} [IntModule A]
    (sigma : A → A)
    (sub_map : ∀ a b, sigma (a-b)=sigma a-sigma b)
    (linear : ∀ n : Int, ∀ a, sigma (n • a)=n • sigma a)
    (two_fixed : ∀ t, (2 : Int) • t=0 → sigma t=t)
    (q a : A) (rational_q : sigma q=q) (half : (2 : Int) • a=q) :
    sigma (sigma a)=a := by
  have hsa : (2 : Int) • sigma a=q := by
    rw [← linear, half, rational_q]
  have ht : (2 : Int) • (sigma a-a)=0 := by grind
  have hs := two_fixed (sigma a-a) ht
  rw [sub_map] at hs
  grind

theorem odd_class_has_explicit_norm_lift {A J : Type}
    [IntModule A] [IntModule J]
    (phi : A → J) (norm : J → A)
    (phi_linear : ∀ n : Int, ∀ a, phi (n • a)=n • phi a)
    (twice : ∀ x, phi (norm x)=(2 : Int) • x)
    (x : J) (odd : (2773073 : Int) • x=0) :
    phi ((1386537 : Int) • norm x)=x := by
  rw [phi_linear, twice]
  grind

/-- This proves the full lift from odd and cofactor data, rather than assuming
the rational-lift conclusion for x. The four actual cofactor lifts are native
and written geometric inputs; this theorem does not construct them. -/
theorem preimage_from_odd_and_cofactor {A J : Type}
    [IntModule A] [IntModule J]
    (phi : A → J) (norm : J → A)
    (phi_add : ∀ a b, phi (a+b)=phi a+phi b)
    (phi_linear : ∀ n : Int, ∀ a, phi (n • a)=n • phi a)
    (phi_norm : ∀ x, phi (norm x)=(2 : Int) • x)
    (norm_phi : ∀ a, norm (phi a)=(2 : Int) • a)
    (x odd cofactor : J) (lift_cofactor : A)
    (decomposition : x=odd+cofactor)
    (odd_order : (2773073 : Int) • odd=0)
    (actual_cofactor_lift : phi lift_cofactor=cofactor) :
    ∃ a0, phi a0=x ∧ (2 : Int) • a0=norm x := by
  let a0 := (1386537 : Int) • norm odd+lift_cofactor
  have hodd := odd_class_has_explicit_norm_lift phi norm phi_linear phi_norm odd odd_order
  have hp : phi a0=x := by
    dsimp [a0]
    rw [phi_add, hodd, actual_cofactor_lift]
    exact decomposition.symm
  refine ⟨a0,hp,?_⟩
  rw [← hp, norm_phi]

theorem correction_exists_for_every_half {A J : Type}
    [IntModule A] [IntModule J]
    (phi : A → J) (norm : J → A)
    (phi_sub : ∀ a b, phi (a-b)=phi a-phi b)
    (x : J) (a a0 : A)
    (correct_preimage : phi a0=x)
    (preimage_norm : (2 : Int) • a0=norm x)
    (half : (2 : Int) • a=norm x) :
    ∃ t, (2 : Int) • t=0 ∧ phi t=x-phi a := by
  refine ⟨a0-a,?_,?_⟩
  · exact halves_differ_by_two_torsion (norm x) a0 a preimage_norm half
  · rw [phi_sub, correct_preimage]

theorem corrected_evaluator_matches_beta {A J B : Type}
    [IntModule A] [IntModule J] [IntModule B]
    (phi : A → J) (psi : A → B) (beta : J → B)
    (phi_add : ∀ a b, phi (a+b)=phi a+phi b)
    (psi_add : ∀ a b, psi (a+b)=psi a+psi b)
    (quotient_square : ∀ a, beta (phi a)=psi a)
    (x : J) (a t : A) (actual_correction : phi t=x-phi a) :
    psi a+psi t=beta x := by
  have hm : phi (a+t)=x := by rw [phi_add, actual_correction]; grind
  rw [← psi_add, ← quotient_square, hm]

theorem corrected_lift_independent {A J B : Type}
    [IntModule A] [IntModule J] [IntModule B]
    (phi : A → J) (psi : A → B) (beta : J → B)
    (phi_add : ∀ a b, phi (a+b)=phi a+phi b)
    (psi_add : ∀ a b, psi (a+b)=psi a+psi b)
    (quotient_square : ∀ a, beta (phi a)=psi a)
    (x : J) (a t b u : A)
    (first : phi t=x-phi a) (second : phi u=x-phi b) :
    psi a+psi t=psi b+psi u := by
  rw [corrected_evaluator_matches_beta phi psi beta phi_add psi_add quotient_square x a t first,
    corrected_evaluator_matches_beta phi psi beta phi_add psi_add quotient_square x b u second]

theorem strongest_scalar_baseline_identity {A J B : Type}
    [IntModule A] [IntModule J] [IntModule B]
    (norm : J → A) (psi : A → B) (beta : J → B)
    (psi_linear : ∀ n : Int, ∀ a, psi (n • a)=n • psi a)
    (beta_linear : ∀ n : Int, ∀ x, beta (n • x)=n • beta x)
    (twice : ∀ x, psi (norm x)=(2 : Int) • beta x)
    (x : J) :
    psi ((1386537 : Int) • norm x)-beta ((2773073 : Int) • x)=beta x := by
  rw [psi_linear, twice, beta_linear]
  grind

end NormHalving
#print axioms NormHalving.halving_abscissa_identity
#print axioms NormHalving.halving_ordinate_identity
#print axioms NormHalving.halves_differ_by_two_torsion
#print axioms NormHalving.halves_fixed_by_frobenius_square
#print axioms NormHalving.odd_class_has_explicit_norm_lift
#print axioms NormHalving.preimage_from_odd_and_cofactor
#print axioms NormHalving.correction_exists_for_every_half
#print axioms NormHalving.corrected_evaluator_matches_beta
#print axioms NormHalving.corrected_lift_independent
#print axioms NormHalving.strongest_scalar_baseline_identity
