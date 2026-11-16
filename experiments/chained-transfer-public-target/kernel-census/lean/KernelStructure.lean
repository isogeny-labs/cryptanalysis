import Std.Tactic

/-! Structural implications used by the written conjugacy/cardinality argument.
Actual symplectic-group cardinality, computational census execution, theta
and Galois identification, polarized isogenies and Jacobians are not defined
here. No custom axioms, holes or unverified native evaluation. -/
set_option autoImplicit false
set_option maxRecDepth 10000
set_option maxHeartbeats 2000000
namespace Kernel223

theorem closed_cardinality_arithmetic :
    (63*32*15*8*3*2 : Nat)=1451520 ∧
    (2+1)*(4+1)*(8+1)=135 ∧ (120960*12 : Nat)=1451520 := by decide

def Stable {V : Type} (f : V → V) (S : V → Prop) : Prop :=
  ∀ x, S x → S (f x)

def Transport {V : Type} (inverse : V → V) (S : V → Prop) : V → Prop :=
  fun y => S (inverse y)

theorem conjugacy_transports_stability
    {V : Type} (f g h inverse : V → V)
    (left_inverse : ∀ x, inverse (h x)=x)
    (right_inverse : ∀ y, h (inverse y)=y)
    (intertwines : ∀ x, h (f x)=g (h x)) (S : V → Prop) :
    Stable f S ↔ Stable g (Transport inverse S) := by
  have inverse_conjugacy (y : V) : inverse (g y)=f (inverse y) := by
    have equation := congrArg inverse (intertwines (inverse y))
    rw [left_inverse, right_inverse] at equation
    exact equation.symm
  constructor
  · intro stable y hy
    change S (inverse (g y))
    rw [inverse_conjugacy]
    exact stable (inverse y) hy
  · intro stable x hx
    have transported : Transport inverse S (h x) := by
      change S (inverse (h x))
      rw [left_inverse]
      exact hx
    have result := stable (h x) transported
    change S (inverse (g (h x))) at result
    rw [← intertwines x, left_inverse] at result
    exact result

def Isotropic {V : Type} (orthogonal : V → V → Prop) (S : V → Prop) : Prop :=
  ∀ x y, S x → S y → orthogonal x y

theorem isometry_transports_isotropy
    {V : Type} (h inverse : V → V)
    (left_inverse : ∀ x, inverse (h x)=x)
    (right_inverse : ∀ y, h (inverse y)=y)
    (orthogonal : V → V → Prop)
    (preserves : ∀ x y, orthogonal (h x) (h y) ↔ orthogonal x y)
    (S : V → Prop) :
    Isotropic orthogonal S ↔ Isotropic orthogonal (Transport inverse S) := by
  constructor
  · intro isotropic x y hx hy
    have equivalence := preserves (inverse x) (inverse y)
    rw [right_inverse, right_inverse] at equivalence
    exact equivalence.mpr (isotropic (inverse x) (inverse y) hx hy)
  · intro isotropic x y hx hy
    have tx : Transport inverse S (h x) := by
      change S (inverse (h x)); rw [left_inverse]; exact hx
    have ty : Transport inverse S (h y) := by
      change S (inverse (h y)); rw [left_inverse]; exact hy
    exact (preserves x y).mp (isotropic (h x) (h y) tx ty)

def trueCount : (n : Nat) → (Fin n → Bool) → Nat
  | 0, _ => 0
  | n+1, p => (if p 0 then 1 else 0) + trueCount n (fun i => p i.succ)

theorem true_count_monotone (n : Nat) (p q : Fin n → Bool)
    (inclusion : ∀ i, p i=true → q i=true) :
    trueCount n p ≤ trueCount n q := by
  induction n with
  | zero => simp [trueCount]
  | succ n ih =>
    have tail := ih (fun i => p i.succ) (fun i => q i.succ)
      (fun i hi => inclusion i.succ hi)
    have head : (if p 0 then 1 else 0 : Nat) ≤ (if q 0 then 1 else 0) := by
      have h := inclusion 0
      cases hp : p 0 <;> cases hq : q 0 <;> simp_all
    simp only [trueCount]
    omega

theorem equal_count_and_inclusion_give_equal_membership
    (n : Nat) (p q : Fin n → Bool)
    (inclusion : ∀ i, p i=true → q i=true)
    (equal_count : trueCount n p=trueCount n q) :
    ∀ i, p i=q i := by
  induction n with
  | zero => intro i; exact Fin.elim0 i
  | succ n ih =>
    have tail_inclusion : ∀ i : Fin n, p i.succ=true → q i.succ=true :=
      fun i hi => inclusion i.succ hi
    have tail_bound := true_count_monotone n (fun i => p i.succ)
      (fun i => q i.succ) tail_inclusion
    have head : p 0=q 0 := by
      have h := inclusion 0
      simp only [trueCount] at equal_count
      cases hp : p 0 <;> cases hq : q 0 <;> simp_all <;> omega
    have tail_count : trueCount n (fun i => p i.succ)=
        trueCount n (fun i => q i.succ) := by
      simp only [trueCount] at equal_count
      rw [head] at equal_count
      omega
    have tail := ih (fun i => p i.succ) (fun i => q i.succ)
      tail_inclusion tail_count
    intro i
    exact Fin.cases head (fun j => tail j) i

end Kernel223
