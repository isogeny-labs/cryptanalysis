import Std.Tactic
import Init.Grind.Module.Basic
set_option autoImplicit false
namespace OldPrimeObstruction
open Lean.Grind

/-- A point annihilated by two integers with an explicit Bezout relation is
zero. The target group's finite cardinality and Lagrange bridge are hypotheses
to be supplied separately; no curve or finite-group implementation is encoded. -/
theorem coprime_annihilators {A : Type} [IntModule A]
    (a : A) (p n u v : Int) (relation : u*p+v*n=1)
    (primeAnnihilator : p • a=0) (targetAnnihilator : n • a=0) :
    a=0 := by
  calc
    a = (u*p+v*n) • a := by rw [relation, IntModule.one_zsmul]
    _ = u • (p • a) + v • (n • a) := by
      rw [IntModule.add_zsmul, IntModule.mul_zsmul, IntModule.mul_zsmul]
    _ = 0 := by
      rw [primeAnnihilator, targetAnnihilator,
        IntModule.zsmul_zero, IntModule.zsmul_zero]
      grind

/-- Exact integer arithmetic for the original subgroup order and the newly
certified twisted-source order. This does not assert a Jacobian's cardinality. -/
theorem fixed_orders_coprime : Nat.gcd 2773073 11086844 = 1 := by
  decide

/-- Conditional group obstruction for the actual numeric orders. Interpreting
the target annihilator as the order of either fixed prime-field Jacobian needs
the HLP/Frobenius/isogeny-cardinality and finite-group Lagrange bridges. -/
theorem old_prime_point_zero {A : Type} [IntModule A] (a : A)
    (oldPrime : (2773073 : Int) • a=0)
    (targetOrder : (11086844 : Int) • a=0) : a=0 := by
  have relation : (2163237 : Int)*2773073+(-541075)*11086844=1 := by
    decide
  exact coprime_annihilators a 2773073 11086844 2163237 (-541075)
    relation oldPrime targetOrder

end OldPrimeObstruction
