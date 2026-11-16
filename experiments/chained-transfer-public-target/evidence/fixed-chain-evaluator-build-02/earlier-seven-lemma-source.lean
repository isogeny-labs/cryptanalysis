import Std.Tactic
import Init.Grind.Module.Basic
set_option autoImplicit false
namespace ChainDescent
open Lean.Grind

/-- An element fixed by the second and third powers is fixed by Frobenius.
This lemma is about an arbitrary function, so no inverse is assumed. -/
theorem square_cube_fixed {X : Type} (sigma : X → X) (x : X)
    (square : sigma (sigma x)=x) (cube : sigma (sigma (sigma x))=x) :
    sigma x=x := by
  calc
    sigma x = sigma (sigma (sigma x)) := congrArg sigma square.symm
    _ = x := cube

/-- The cube identity on a preimage passes to its image under equivariance. -/
theorem image_fixed {A J : Type} (sa : A → A) (sj : J → J)
    (phi : A → J) (equivariant : ∀ a, phi (sa a)=sj (phi a))
    (a : A) (cube : sa (sa (sa a))=a)
    (square : sj (sj (phi a))=phi a) : sj (phi a)=phi a := by
  apply square_cube_fixed sj (phi a) square
  rw [← equivariant a, ← equivariant (sa a), ← equivariant (sa (sa a)), cube]

/-- Averaging three conjugates of a two-torsion preimage supplies a rational
two-torsion preimage of a rational image. No rational preimage is assumed. -/
theorem rational_two_torsion_average {A J : Type} [IntModule A] [IntModule J]
    (sa : A → A) (sj : J → J) (phi : A → J)
    (sa_add : ∀ a b, sa (a+b)=sa a+sa b)
    (sa_linear : ∀ n : Int, ∀ a, sa (n • a)=n • sa a)
    (sa_zero : sa 0=0)
    (phi_add : ∀ a b, phi (a+b)=phi a+phi b)
    (phi_linear : ∀ n : Int, ∀ a, phi (n • a)=n • phi a)
    (phi_zero : phi 0=0)
    (equivariant : ∀ a, phi (sa a)=sj (phi a))
    (a : A) (two : (2 : Int) • a=0)
    (cube : sa (sa (sa a))=a) (rational_image : sj (phi a)=phi a) :
    ∃ b, (2 : Int) • b=0 ∧ sa b=b ∧ phi b=phi a := by
  let b := a+sa a+sa (sa a)
  have hsa : (2 : Int) • sa a=0 := by rw [← sa_linear, two, sa_zero]
  have hssa : (2 : Int) • sa (sa a)=0 := by rw [← sa_linear, hsa, sa_zero]
  have hphi : (2 : Int) • phi a=0 := by rw [← phi_linear, two, phi_zero]
  refine ⟨b, ?_, ?_, ?_⟩
  · dsimp [b]
    grind
  · dsimp [b]
    rw [sa_add, sa_add, cube]
    grind
  · have h1 : phi (sa a)=phi a := by rw [equivariant, rational_image]
    have h2 : phi (sa (sa a))=phi a := by rw [equivariant, h1, rational_image]
    dsimp [b]
    rw [phi_add, phi_add, h1, h2]
    grind

/-- The dual identity puts the norm-half difference in the actual norm kernel. -/
theorem norm_half_difference_in_kernel {A J : Type} [IntModule A] [IntModule J]
    (phi : A → J) (norm : J → A)
    (norm_sub : ∀ x y, norm (x-y)=norm x-norm y)
    (dual : ∀ a, norm (phi a)=(2 : Int) • a)
    (x : J) (p : A) (half : (2 : Int) • p=norm x) :
    norm (x-phi p)=0 := by
  rw [norm_sub, dual, half]
  grind

/-- Kernel transport suffices for equal source images to have equal targets;
there is no assumed quotient beta or assumed corrected evaluator in this lemma. -/
theorem equal_images_equal_targets {A J B : Type}
    [IntModule A] [IntModule J] [IntModule B]
    (phi : A → J) (psi : A → B)
    (phi_sub : ∀ a b, phi (a-b)=phi a-phi b)
    (psi_sub : ∀ a b, psi (a-b)=psi a-psi b)
    (kernel_transport : ∀ a, phi a=0 → psi a=0)
    (a b : A) (same : phi a=phi b) : psi a=psi b := by
  have hk : phi (a-b)=0 := by rw [phi_sub, same]; grind
  have ht := kernel_transport (a-b) hk
  rw [psi_sub] at ht
  exact AddCommGroup.sub_eq_zero_iff.mp ht

/-- Complete corrections give the same target for any two halves, using only
the full kernel-transport condition rather than an assumed desired beta. -/
theorem corrected_half_choice_independent {A J B : Type}
    [IntModule A] [IntModule J] [IntModule B]
    (phi : A → J) (psi : A → B)
    (phi_add : ∀ a b, phi (a+b)=phi a+phi b)
    (phi_sub : ∀ a b, phi (a-b)=phi a-phi b)
    (psi_add : ∀ a b, psi (a+b)=psi a+psi b)
    (psi_sub : ∀ a b, psi (a-b)=psi a-psi b)
    (kernel_transport : ∀ a, phi a=0 → psi a=0)
    (x : J) (p t q u : A)
    (first : phi t=x-phi p) (second : phi u=x-phi q) :
    psi p+psi t=psi q+psi u := by
  have h1 : phi (p+t)=x := by rw [phi_add, first]; grind
  have h2 : phi (q+u)=x := by rw [phi_add, second]; grind
  have h := equal_images_equal_targets phi psi phi_sub psi_sub kernel_transport
    (p+t) (q+u) (h1.trans h2.symm)
  rw [psi_add, psi_add] at h
  exact h

/-- Equivariance and kernel transport prove Frobenius-fixed output from any
preimage of a rational input. Actual fixed-field descent remains a bridge. -/
theorem corrected_output_fixed {A J B : Type}
    [IntModule A] [IntModule J] [IntModule B]
    (sa : A → A) (sj : J → J) (sb : B → B)
    (phi : A → J) (psi : A → B)
    (phi_sub : ∀ a b, phi (a-b)=phi a-phi b)
    (psi_sub : ∀ a b, psi (a-b)=psi a-psi b)
    (kernel_transport : ∀ a, phi a=0 → psi a=0)
    (phi_equivariant : ∀ a, phi (sa a)=sj (phi a))
    (psi_equivariant : ∀ a, psi (sa a)=sb (psi a))
    (x : J) (rational : sj x=x) (a : A) (preimage : phi a=x) :
    sb (psi a)=psi a := by
  have h : phi (sa a)=phi a := by rw [phi_equivariant, preimage, rational]
  have target := equal_images_equal_targets phi psi phi_sub psi_sub kernel_transport
    (sa a) a h
  rw [psi_equivariant] at target
  exact target

end ChainDescent
