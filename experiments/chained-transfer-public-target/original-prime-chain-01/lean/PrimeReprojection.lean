import Std.Tactic
import Init.Grind.Module.Basic
set_option autoImplicit false
namespace PrimeReprojection
open Lean.Grind

/-- The actual types in the application must be the stated ell-torsion groups.
The annihilation hypothesis is essential; no inverse-two on a cofactor is claimed. -/
theorem inverse_two {A : Type} [IntModule A]
    (a ell quotient : Int) (bezout : a*2+quotient*ell=1)
    (x : A) (annihilated : ell • x=0) : a • ((2 : Int) • x)=x := by
  calc
    a • ((2 : Int) • x) = (a*2+quotient*ell) • x := by
      rw [IntModule.add_zsmul, IntModule.mul_zsmul, IntModule.mul_zsmul,
        annihilated, IntModule.zsmul_zero]
      grind
    _ = x := by rw [bezout, IntModule.one_zsmul]

/-- Norm normalization is derived from both HLP dual identities and scalar
linearity, not from a desired transfer or matching of two-torsion kernels. -/
theorem normalized_norm_pair {A J : Type} [IntModule A] [IntModule J]
    (phi : A → J) (norm : J → A) (a ell quotient : Int)
    (source_dual : ∀ p, norm (phi p)=(2 : Int) • p)
    (target_dual : ∀ x, phi (norm x)=(2 : Int) • x)
    (phi_linear : ∀ z : Int, ∀ p, phi (z • p)=z • phi p)
    (source_ann : ∀ p : A, ell • p=0) (target_ann : ∀ x : J, ell • x=0)
    (bezout : a*2+quotient*ell=1) :
    (∀ p, a • norm (phi p)=p) ∧ (∀ x, phi (a • norm x)=x) := by
  constructor
  · intro p
    rw [source_dual]
    exact inverse_two a ell quotient bezout p (source_ann p)
  · intro x
    rw [phi_linear, target_dual]
    exact inverse_two a ell quotient bezout x (target_ann x)

def transfer {A B J K : Type} [IntModule A]
    (phi : B → K) (g : A → B) (norm : J → A) (a : Int) (x : J) : K :=
  phi (g (a • norm x))

/-- Both desired prime-group dual norms follow from the individual HLP and
elliptic dual identities. No kernel-compatibility or transfer-norm hypothesis. -/
theorem reprojection_dual_norm {A B J K : Type}
    [IntModule A] [IntModule B] [IntModule J] [IntModule K]
    (pi : A → J) (pj : B → K) (ni : J → A) (nj : K → B)
    (g : A → B) (gh : B → A) (a ell quotient n : Int)
    (ni_pi : ∀ p, ni (pi p)=(2 : Int) • p)
    (pi_ni : ∀ x, pi (ni x)=(2 : Int) • x)
    (nj_pj : ∀ p, nj (pj p)=(2 : Int) • p)
    (pj_nj : ∀ x, pj (nj x)=(2 : Int) • x)
    (pi_linear : ∀ z : Int, ∀ p, pi (z • p)=z • pi p)
    (pj_linear : ∀ z : Int, ∀ p, pj (z • p)=z • pj p)
    (annA : ∀ p : A, ell • p=0) (annB : ∀ p : B, ell • p=0)
    (annJ : ∀ x : J, ell • x=0) (annK : ∀ x : K, ell • x=0)
    (bezout : a*2+quotient*ell=1)
    (source_elliptic_dual : ∀ p, gh (g p)=n • p)
    (target_elliptic_dual : ∀ p, g (gh p)=n • p) :
    (∀ x, transfer pi gh nj a (transfer pj g ni a x)=n • x) ∧
    (∀ y, transfer pj g ni a (transfer pi gh nj a y)=n • y) := by
  have hi := normalized_norm_pair pi ni a ell quotient ni_pi pi_ni
    pi_linear annA annJ bezout
  have hj := normalized_norm_pair pj nj a ell quotient nj_pj pj_nj
    pj_linear annB annK bezout
  constructor
  · intro x
    unfold transfer
    rw [hj.1, source_elliptic_dual, pi_linear, hi.2]
  · intro y
    unfold transfer
    rw [hi.1, target_elliptic_dual, pj_linear, hj.2]

/-- A literal adjacent Jacobian chain equals one initial normalized norm,
the factored elliptic composition, and one final quotient. -/
theorem reprojection_chain {A B C J K L : Type}
    [IntModule A] [IntModule B]
    (pj : B → K) (pc : C → L) (ni : J → A) (nj : K → B)
    (g : A → B) (h : B → C) (a ell quotient : Int)
    (middle_dual : ∀ p, nj (pj p)=(2 : Int) • p)
    (annB : ∀ p : B, ell • p=0) (bezout : a*2+quotient*ell=1) (x : J) :
    transfer pc h nj a (transfer pj g ni a x)=
      transfer pc (fun p => h (g p)) ni a x := by
  unfold transfer
  rw [middle_dual, inverse_two a ell quotient bezout _ (annB _)]

/-- A known initial elliptic point avoids norm recovery and inverse-two.
Its exact target is the same prime-class transfer, not a weaker benchmark. -/
theorem known_initial_point {A B J K : Type} [IntModule A]
    (pi : A → J) (pj : B → K) (ni : J → A) (g : A → B)
    (a ell quotient : Int) (source_dual : ∀ p, ni (pi p)=(2 : Int) • p)
    (annA : ∀ p : A, ell • p=0) (bezout : a*2+quotient*ell=1) (p : A) :
    transfer pj g ni a (pi p)=pj (g p) := by
  unfold transfer
  rw [source_dual, inverse_two a ell quotient bezout p (annA p)]

/-- Integer linearity supplies the DLP relation. Injective recovery separately
uses the derived dual norm and an inverse-n witness on the ell annihilator. -/
theorem transfer_integer_linear {A B J K : Type}
    [IntModule A] [IntModule B] [IntModule J] [IntModule K]
    (phi : B → K) (g : A → B) (norm : J → A) (a : Int)
    (norm_linear : ∀ z : Int, ∀ x, norm (z • x)=z • norm x)
    (g_linear : ∀ z : Int, ∀ p, g (z • p)=z • g p)
    (phi_linear : ∀ z : Int, ∀ p, phi (z • p)=z • phi p)
    (z : Int) (x : J) : transfer phi g norm a (z • x)=z • transfer phi g norm a x := by
  unfold transfer
  rw [norm_linear]
  have commute : a • (z • norm x)=z • (a • norm x) := by
    rw [← IntModule.mul_zsmul, ← IntModule.mul_zsmul, Int.mul_comm]
  rw [commute, g_linear, phi_linear]

/-- Exact old scalar, coprimality and positive-square witnesses only. These
are not certificates for an actual Jacobian order or encoded field bridge. -/
theorem actual_original_witnesses :
    (2*1386537 : Nat)=2773073+1 ∧
    Nat.gcd 13 2773073=1 ∧ Nat.gcd 169 2773073=1 ∧
    Nat.gcd 2197 2773073=1 ∧ Nat.gcd 28561 2773073=1 ∧
    (10*10 : Nat)%223=100 ∧ (40*40 : Nat)%223=39 ∧ (22*22 : Nat)%223=38 := by
  decide

end PrimeReprojection
