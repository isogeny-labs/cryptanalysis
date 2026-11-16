import Std.Tactic
import Init.Grind.Module.Basic
set_option autoImplicit false
namespace OriginalFullPrimeRecovery
open Lean.Grind

/-- The prime-source control recovers p from 2p plus an arbitrary four-torsion
term. This is a CRT test oracle, not division by two on the full group. -/
theorem recover_prime_summand {A : Type} [IntModule A]
    (p t : A) (ell r m quotient : Int)
    (prime_ann : ell • p=0) (cofactor_ann : (4 : Int) • t=0)
    (inverse_two : r*2+quotient*ell=1) (multiple_four : r=4*m) :
    r • ((2 : Int) • p+t)=p := by
  have kill : r • t=0 := by
    rw [multiple_four, Int.mul_comm, IntModule.mul_zsmul,
      cofactor_ann, IntModule.zsmul_zero]
  have prime : r • ((2 : Int) • p)=p := by
    calc
      r • ((2 : Int) • p) = (r*2+quotient*ell) • p := by
        rw [IntModule.add_zsmul, IntModule.mul_zsmul, IntModule.mul_zsmul,
          prime_ann, IntModule.zsmul_zero]
        grind
      _ = p := by rw [inverse_two, IntModule.one_zsmul]
  rw [IntModule.zsmul_add, prime, kill]
  grind

/-- Values derived by the test's unchanged extended-Euclid prime helper;
ordinary kernel reduction checks every scalar and CRT condition. -/
theorem actual_original_prime_recovery_witnesses :
    (8*2426439 : Nat)=7*2773073+1 ∧
    (4*2426439 : Nat)=9705756 ∧
    (9705756 : Nat)%4=0 ∧ (2*9705756 : Nat)%2773073=1 ∧
    (9705756*2+(-7)*2773073 : Int)=1 := by
  decide

end OriginalFullPrimeRecovery
