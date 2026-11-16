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

namespace ChainDescent
open Lean.Grind

/-- Complete rational two-torsion correction from the actual norm-kernel
identity and Frobenius cube law. The conclusion is not a hypothesis. -/
theorem rational_correction_complete {A J : Type} [IntModule A] [IntModule J]
    (sa : A → A) (sj : J → J) (phi : A → J) (norm : J → A)
    (sa_add : ∀ a b, sa (a+b)=sa a+sa b)
    (sa_linear : ∀ n : Int, ∀ a, sa (n • a)=n • sa a)
    (sa_zero : sa 0=0)
    (phi_add : ∀ a b, phi (a+b)=phi a+phi b)
    (phi_linear : ∀ n : Int, ∀ a, phi (n • a)=n • phi a)
    (phi_zero : phi 0=0)
    (equivariant : ∀ a, phi (sa a)=sj (phi a))
    (cube_on_two : ∀ a, (2 : Int) • a=0 → sa (sa (sa a))=a)
    (kernel_description : ∀ d, norm d=0 → ∃ a, (2 : Int) • a=0 ∧ phi a=d)
    (delta : J) (in_kernel : norm delta=0)
    (square : sj (sj delta)=delta) :
    ∃ t, (2 : Int) • t=0 ∧ sa t=t ∧ phi t=delta := by
  obtain ⟨a, two, image⟩ := kernel_description delta in_kernel
  have hcube := cube_on_two a two
  have hsquare : sj (sj (phi a))=phi a := by rw [image]; exact square
  have rational := image_fixed sa sj phi equivariant a hcube hsquare
  obtain ⟨t, ht, fixed, mapped⟩ := rational_two_torsion_average sa sj phi sa_add
    sa_linear sa_zero phi_add phi_linear phi_zero equivariant a two hcube rational
  exact ⟨t, ht, fixed, mapped.trans image⟩

end ChainDescent

namespace FullGroupNorm
open Lean.Grind

/-- Both composite norms follow from the individual dual norms and linearity;
the composite norm is not itself a hypothesis. -/
theorem two_pair_norm {A B C : Type} [IntModule A] [IntModule B] [IntModule C]
    (f : A → B) (fh : B → A) (g : B → C) (gh : C → B) (n m : Int)
    (hf : ∀ a, fh (f a)=n • a) (hfh : ∀ b, f (fh b)=n • b)
    (hg : ∀ b, gh (g b)=m • b) (hgh : ∀ c, g (gh c)=m • c)
    (fh_linear : ∀ z : Int, ∀ b, fh (z • b)=z • fh b)
    (g_linear : ∀ z : Int, ∀ b, g (z • b)=z • g b) :
    (∀ a, fh (gh (g (f a)))=(n*m) • a) ∧
      (∀ c, g (f (fh (gh c)))=(n*m) • c) := by
  constructor
  · intro a
    rw [hg, fh_linear, hf, ← IntModule.mul_zsmul, Int.mul_comm]
  · intro c
    rw [hfh, g_linear, hgh, ← IntModule.mul_zsmul]

/-- Recovery is on the full stated annihilator, including its cofactor. -/
theorem inverse_on_full_annihilator {A B : Type} [IntModule A]
    (f : A → B) (fh : B → A) (n order inverse quotient : Int)
    (dual_norm : ∀ a, fh (f a)=n • a)
    (bezout : inverse*n+quotient*order=1)
    (a : A) (annihilated : order • a=0) : inverse • fh (f a)=a := by
  rw [dual_norm]
  calc
    inverse • (n • a) = (inverse*n+quotient*order) • a := by
      rw [IntModule.add_zsmul, IntModule.mul_zsmul, IntModule.mul_zsmul,
        annihilated, IntModule.zsmul_zero]
      grind
    _ = a := by rw [bezout, IntModule.one_zsmul]

/-- Exact integer witnesses for the fixed full rational group and the independent
prime-source recovery scalar. This is not a field or group-order certificate. -/
theorem actual_full_group_witnesses :
    (13*5117005 : Nat)=6*11086844+1 ∧
    (169*7216289 : Nat)=110*11086844+1 ∧
    (8*346464 : Nat)=2771711+1 ∧ 1385856 % 4=0 := by
  decide

theorem full_group_coprime :
    Nat.gcd 13 11086844=1 ∧ Nat.gcd 169 11086844=1 := by
  decide

/-- Carrying an actual elliptic lift evaluates the two quotient maps using the
factored elliptic composition. This explains the strongest comparator; it is
not an assumption that an arbitrary input already has such a lift. -/
theorem retained_lift_chain {A B C J K L : Type}
    (pa : A → J) (pb : B → K) (pc : C → L)
    (g : A → B) (h : B → C) (first : J → K) (second : K → L)
    (first_square : ∀ a, first (pa a)=pb (g a))
    (second_square : ∀ b, second (pb b)=pc (h b)) (a : A) :
    second (first (pa a))=pc (h (g a)) := by
  rw [first_square, second_square]

end FullGroupNorm

namespace NormPointReuse
open Lean.Grind

/-- A half and a rational two-torsion correction have the same doubled norm. -/
theorem corrected_lift_doubles {A : Type} [IntModule A]
    (p t q : A) (half : (2 : Int) • p = q)
    (correction_two_torsion : (2 : Int) • t = 0) :
    (2 : Int) • (p + t) = q := by
  rw [IntModule.zsmul_add, half, correction_two_torsion]
  grind

/-- The transported norm is derived from duality, linearity, a half and
2-torsion correction. Equality with the old transported norm is not assumed. -/
theorem corrected_norm_reuse {A B J : Type} [IntModule A] [IntModule B]
    (g : A → B) (phi : B → J) (norm : J → B)
    (duality : ∀ z, norm (phi z) = (2 : Int) • z)
    (linear_two : ∀ a, g ((2 : Int) • a) = (2 : Int) • g a)
    (p t q : A) (half : (2 : Int) • p = q)
    (correction_two_torsion : (2 : Int) • t = 0) :
    norm (phi (g (p + t))) = (2 : Int) • g (p + t) ∧
      (2 : Int) • g (p + t) = g q := by
  constructor
  · exact duality _
  · rw [← linear_two, corrected_lift_doubles p t q half correction_two_torsion]

/-- For a factored elliptic composition the reused final point has the same
transported norm as evaluating both original maps on the source norm. -/
theorem factored_norm_reuse {A B C J : Type}
    [IntModule A] [IntModule B] [IntModule C]
    (g : A → B) (h : B → C) (phi : C → J) (norm : J → C)
    (duality : ∀ z, norm (phi z) = (2 : Int) • z)
    (g_linear_two : ∀ a, g ((2 : Int) • a) = (2 : Int) • g a)
    (h_linear_two : ∀ b, h ((2 : Int) • b) = (2 : Int) • h b)
    (p t q : A) (half : (2 : Int) • p = q)
    (correction_two_torsion : (2 : Int) • t = 0) :
    norm (phi (h (g (p + t)))) = (2 : Int) • h (g (p + t)) ∧
      (2 : Int) • h (g (p + t)) = h (g q) := by
  apply corrected_norm_reuse (fun a => h (g a)) phi norm duality
  · intro a
    rw [g_linear_two, h_linear_two]
  · exact half
  · exact correction_two_torsion

end NormPointReuse

namespace OriginalFullChain
open Lean.Grind

/-- A known source point supplies an admissible half and zero correction for
its actual Phi image. No inverse of two on a cofactor group is used. -/
theorem known_point_representation {A J : Type} [IntModule A] [IntModule J]
    (phi : A → J) (norm : J → A)
    (duality : ∀ a, norm (phi a)=(2 : Int) • a)
    (phi_zero : phi 0=0) (p : A) :
    (2 : Int) • p=norm (phi p) ∧ phi 0=phi p-phi p := by
  constructor
  · exact (duality p).symm
  · rw [phi_zero]
    grind

/-- Compare any corrected opaque presentation to the explicit p/zero
presentation using the old choice-independence theorem. psi is the target
quotient composed with the elliptic map; no desired beta identity is assumed. -/
theorem known_point_corrected_output {A J B : Type}
    [IntModule A] [IntModule J] [IntModule B]
    (phi : A → J) (psi : A → B)
    (phi_add : ∀ a b, phi (a+b)=phi a+phi b)
    (phi_sub : ∀ a b, phi (a-b)=phi a-phi b)
    (psi_add : ∀ a b, psi (a+b)=psi a+psi b)
    (psi_sub : ∀ a b, psi (a-b)=psi a-psi b)
    (phi_zero : phi 0=0) (psi_zero : psi 0=0)
    (kernel_transport : ∀ a, phi a=0 → psi a=0)
    (h t p : A) (correction : phi t=phi p-phi h) :
    psi h+psi t=psi p := by
  have zero_correction : phi 0=phi p-phi p := by
    rw [phi_zero]
    grind
  have equal := ChainDescent.corrected_half_choice_independent phi psi
    phi_add phi_sub psi_add psi_sub kernel_transport (phi p) h t p 0
    correction zero_correction
  rw [psi_zero] at equal
  grind

/-- Literal original-source order, coprimality and selected positive-square
witnesses; not an actual field/Jacobian-order/program bridge. -/
theorem actual_original_full_witnesses :
    (4*2773073 : Nat)=11092292 ∧
    Nat.gcd 13 11092292=1 ∧ Nat.gcd 169 11092292=1 ∧
    (89*89 : Nat)%223=116 ∧ (40*40 : Nat)%223=39 ∧
    (6*6 : Nat)%223=36 ∧
    (13*3413013 : Nat)=4*11092292+1 ∧
    (169*9648325 : Nat)=147*11092292+1 ∧
    (3413013*13+(-4)*11092292 : Int)=1 ∧
    (9648325*169+(-147)*11092292 : Int)=1 := by
  decide

end OriginalFullChain
