import Std.Tactic
import Init.Grind.Module.Basic

/-! Faithful conditional algebra for the written q223 two-torsion argument.
The actual Jacobian, Ciani isogeny, geometric torsion, Cayley-Hamilton,
orbit decomposition and characteristic-polynomial bridges remain open.
No custom axioms, proof holes or unverified native evaluation are used. -/
set_option autoImplicit false
set_option maxRecDepth 10000
set_option maxHeartbeats 2000000
namespace TwoPrimary223
open Lean.Grind

def iterate {V : Type} (f : V → V) : Nat → V → V
  | 0, x => x
  | n+1, x => f (iterate f n x)

theorem exact_trace_and_parity :
    (223 : Int)^3 + 1 - 11092292 = -2724 ∧
    (2724 : Nat) % 2 = 0 ∧ (11089567 : Nat) % 2 = 1 := by decide

theorem no_three_cycle_partition (cycles : Nat) :
    64 ≠ 2 + 3*cycles := by omega

theorem sixth_iterate_on_exponent_two
    {V : Type} [IntModule V] (f : V → V)
    (exponent_two : ∀ x : V, (2 : Nat) • x = 0)
    (annihilator : ∀ x : V,
      iterate f 6 x + (2724 : Nat) • iterate f 3 x +
        (11089567 : Nat) • x = 0) :
    ∀ x : V, iterate f 6 x = x := by
  have even_zero (k : Nat) (x : V) : (2*k) • x = 0 := by
    rw [Nat.mul_comm, NatModule.mul_nsmul, exponent_two,
      NatModule.nsmul_zero]
  intro x
  have middle : (2724 : Nat) • iterate f 3 x = 0 :=
    even_zero 1362 (iterate f 3 x)
  have constant : (11089567 : Nat) • x = x := by
    change (2*5544783+1) • x = x
    rw [NatModule.add_nsmul, even_zero, NatModule.one_nsmul,
      AddCommMonoid.zero_add]
  have twice : x+x=0 := by
    have h := exponent_two x
    change (1+1 : Nat) • x = 0 at h
    simpa only [NatModule.add_nsmul, NatModule.one_nsmul] using h
  have h := annihilator x
  rw [middle, AddCommMonoid.add_zero, constant] at h
  apply (AddCommGroup.add_left_inj x).mp
  exact h.trans twice.symm

theorem exact_six_from_divisor_exclusions (d : Nat)
    (divides_six : d ∣ 6) (not_two : ¬ d ∣ 2)
    (not_three : ¬ d ∣ 3) : d=6 := by
  have bound : d ≤ 6 := Nat.le_of_dvd (by decide) divides_six
  have cases : d=0 ∨ d=1 ∨ d=2 ∨ d=3 ∨ d=4 ∨ d=5 ∨ d=6 := by omega
  rcases cases with h|h|h|h|h|h|h <;> subst d <;> simp_all

end TwoPrimary223
